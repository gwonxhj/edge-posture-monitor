"""
Realtime measurement runtime loop.

실시간 DAT packet 처리, STAND 이벤트 처리,
앱 command 처리, 자세 분석 및 리포트 누적을 담당한다.
"""
import time
import json

from src.communication import session_state as S
from src.communication.app_payload_builder import (
    build_realtime_payload,
    build_stand_event_payload,
    build_debug_sensor_payload,
    build_sensor_distribution_payload,
)
from src.communication.app_command_handler import handle_app_command
from src.communication.uart_protocol import MSG_CAL_DONE

from src.core.feature_extractor import extract_features
from src.core.monitoring_metrics import build_monitoring_metrics
from src.core.posture_flags import detect_posture_flags
from src.core.posture_mapper import to_display_label

from src.sensor.sensor_mapper import map_raw_packet
from src.core.sensor_factor import apply_sensor_factors

from src.app_flow.sit_detector import wait_until_sit_detected
from src.app_flow.app_flow_controller import wait_for_restart_decision

from src.config.settings import (
    DEBUG_FEATURES,
    DEBUG_FLAGS,
    DEBUG_SENSOR_RAW,
    DEBUG_SUMMARY_EVERY_N,
    SIT_TO_NEXT_CMD_DELAY_SEC,
    BUZZER_ENABLE,
    DEBUG_SENSOR_DISTRIBUTION,
)


def select_report_posture(predicted, flags, feature_map=None):
    """
    리포트/집계용 posture 선택 규칙

    우선순위:
    1. normal flag가 켜져 있으면 무조건 normal
    2. 강한 rule posture는 classifier보다 우선
    3. rule 기반 자세가 없으면 classifier 결과 사용
    """
    feature_map = feature_map or {}

    seat_fb_shift = feature_map.get("seat_fb_shift", 0.0)
    pitch = feature_map.get("pitch_fused_deg", 0.0)
    neck_forward = feature_map.get("neck_forward_delta", 0.0)

    # 1) normal 우선
    if flags.get("normal", False):
        return "normal"

    # 2) 강한 override
    if flags.get("forward_lean") and (seat_fb_shift > 0.35 or pitch > 8.0):
        return "forward_lean"

    if flags.get("turtle_neck") and neck_forward > 55:
        return "turtle_neck"

    if flags.get("reclined"):
        return "reclined"

    if flags.get("side_slouch"):
        return "side_slouch"

    if flags.get("perching"):
        return "perching"

    if flags.get("thinking_pose"):
        return "thinking_pose"

    if flags.get("leg_cross_suspect"):
        return "leg_cross_suspect"

    # 3) fallback
    return predicted


def run_measurement_loop(
    receiver,
    sender,
    app_server,
    classifier,
    score_engine,
    session_manager,
    db_manager,
    report_gen,
    audio,
    current_profile,
    baseline,
    session_id,
    runtime_context,
    calibration_manager,
    sample_logger,
):
    print("\n=== 실시간 측정 시작 ===")

    buzzer = None
    if BUZZER_ENABLE:
        from src.feedback.buzzer_feedback import BuzzerFeedback
        buzzer = BuzzerFeedback()

    try:
        score_sum = runtime_context.get("score_sum", 0.0)
        score_count = runtime_context.get("score_count", 0)
        posture_count = runtime_context.get("posture_count", {})
        latest_state = runtime_context.get("latest_state", None)
        sample_index = runtime_context.get("sample_index", 0)
        last_checksum_warn = runtime_context.get("last_checksum_warn", 0)
        last_parse_warn = runtime_context.get("last_parse_warn", 0)
        prev_report_posture = runtime_context.get("prev_report_posture")

        while True:
            cmd = app_server.get_next_command()
            if cmd is not None:
                result = handle_app_command(
                    cmd=cmd,
                    session_manager=session_manager,
                    db_manager=db_manager,
                    app_server=app_server,
                    sender=sender,
                )
                print("[APP CMD RESULT]", result)

                if result["action"] == "pause_measurement":
                    print("앱에서 측정 일시정지 요청이 들어와서 STM32로 STOP 전송")
                    sender.send_stop()
                    if buzzer:
                        buzzer.reset()
                    app_server.update_meta({
                        "stage": S.PAUSED,
                    })
                    return {
                        "result": "paused",
                        "score_sum": score_sum,
                        "score_count": score_count,
                        "posture_count": posture_count,
                        "latest_state": latest_state,
                    }

                if result["action"] == "quit_measurement":
                    print("앱에서 측정 종료 요청이 들어와서 STM32로 STOP 전송")
                    sender.send_stop()
                    if buzzer:
                        buzzer.reset()
                    return {
                        "result": "quit",
                        "score_sum": score_sum,
                        "score_count": score_count,
                        "posture_count": posture_count,
                        "latest_state": latest_state,
                    }

                if result["action"] == "start_calibration":
                    sender.send_stop()
                    if buzzer:
                        buzzer.reset()

                    wait_until_sit_detected(receiver, sender)

                    if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
                        print(
                            f"[Measurement] SIT 확인 후 CAL 전 "
                            f"{SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기"
                        )
                        time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

                    sender.send_cal()

                    app_server.update_meta({
                        "stage": S.CALIBRATING,
                        "calibration_reason": app_server.latest_meta_payload.get(
                            "calibration_reason",
                            "recalibration",
                        ),
                    })

                    new_baseline = calibration_manager.run_calibration_loop(
                        receiver=receiver,
                        mapper_func=map_raw_packet,
                        feature_extractor_func=extract_features,
                        duration_sec=10,
                        verbose=True,
                    )

                    print("[Measurement] CAL_DONE 대기 중...")
                    receiver.wait_for_message(MSG_CAL_DONE, verbose=True)

                    session_manager.save_baseline_for_current_user(new_baseline)
                    baseline = new_baseline

                    # 🔥 baseline sanity check
                    if baseline.get("neck_mean", 0) < 100:
                        print("[WARN] baseline neck_mean too low → fallback correction")
                        baseline["neck_mean"] = 200.0

                    if abs(baseline.get("spine_curve", 0)) > 100:
                        print("[WARN] baseline spine_curve abnormal → reset")
                        baseline["spine_curve"] = 0.0

                    app_server.update_meta({
                        "stage": S.MEASURING,
                        "calibration_reason": None,
                    })

                    if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
                        print(
                            f"[Measurement] baseline 교체 후 GO 전 "
                            f"{SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기"
                        )
                        time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

                    sender.send_go()
                    print("[Measurement] recalibration completed, measurement resumed")
                    continue

            raw_packet = receiver.read_sensor_packet()
            if raw_packet is None:
                continue

            raw_packet = apply_sensor_factors(raw_packet)

            if (
                receiver.checksum_fail_count > 0
                and receiver.checksum_fail_count % 50 == 0
                and receiver.checksum_fail_count != last_checksum_warn
            ):
                print(f"[WARN] checksum_fail_count={receiver.checksum_fail_count}")
                last_checksum_warn = receiver.checksum_fail_count
                runtime_context["last_checksum_warn"] = last_checksum_warn

            if (
                receiver.parse_fail_count > 0
                and receiver.parse_fail_count % 20 == 0
                and receiver.parse_fail_count != last_parse_warn
            ):
                print(f"[WARN] parse_fail_count={receiver.parse_fail_count}")
                last_parse_warn = receiver.parse_fail_count
                runtime_context["last_parse_warn"] = last_parse_warn

            if raw_packet.get("frame_type") == "EVENT":
                if raw_packet.get("event") == "STAND":
                    print("[UART] STAND 이벤트 감지")
                    if buzzer:
                        buzzer.reset()

                    stand_payload = build_stand_event_payload(
                        user_id=current_profile["user_id"]
                    )
                    app_server.update_status(stand_payload)

                    app_server.update_meta({
                        "stage": S.WAIT_RESTART_DECISION,
                    })

                    decision = wait_for_restart_decision(
                        app_server=app_server,
                        session_manager=session_manager,
                        db_manager=db_manager,
                        sender=sender,
                    )

                    if decision == "decline_resume_after_stand":
                        print("사용자가 재시작을 거부하여 측정을 종료함.")
                        if buzzer:
                            buzzer.reset()
                        return {
                            "result": "stand_declined",
                            "score_sum": score_sum,
                            "score_count": score_count,
                            "posture_count": posture_count,
                            "latest_state": latest_state,
                        }

                    if decision == "quit_measurement":
                        print("STAND 이후 사용자가 측정 종료를 요청함.")
                        if buzzer:
                            buzzer.reset()
                        return {
                            "result": "quit",
                            "score_sum": score_sum,
                            "score_count": score_count,
                            "posture_count": posture_count,
                            "latest_state": latest_state,
                        }

                    if decision == "resume_after_stand":
                        print("재시작 요청 -> CHK_SIT 전송")
                        wait_until_sit_detected(receiver, sender)

                        if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
                            print(
                                f"[Measurement] SIT 확인 후 GO 전 "
                                f"{SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기"
                            )
                            time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

                        sender.send_go()

                        app_server.update_meta({
                            "stage": S.MEASURING,
                        })
                        print("측정 재개")
                        continue
                continue

            if raw_packet.get("frame_type") != "DAT":
                continue

            sample_index += 1
            runtime_context["sample_index"] = sample_index

            if sample_index % 100 == 0:
                print(f"[HEARTBEAT] DAT stream alive | sample={sample_index}")

            if DEBUG_SENSOR_RAW and sample_index % DEBUG_SUMMARY_EVERY_N == 0:
                loadcell = raw_packet.get("loadcell", [])

                loadcell_named = {
                    "back_right_top": loadcell[0] if len(loadcell) > 0 else None,
                    "back_right_upper_mid": loadcell[1] if len(loadcell) > 1 else None,
                    "back_right_lower_mid": loadcell[2] if len(loadcell) > 2 else None,
                    "back_right_bottom": loadcell[3] if len(loadcell) > 3 else None,
                    "back_left_top": loadcell[4] if len(loadcell) > 4 else None,
                    "back_left_upper_mid": loadcell[5] if len(loadcell) > 5 else None,
                    "back_left_lower_mid": loadcell[6] if len(loadcell) > 6 else None,
                    "back_left_bottom": loadcell[7] if len(loadcell) > 7 else None,
                    "seat_rear_right": loadcell[8] if len(loadcell) > 8 else None,
                    "seat_front_right": loadcell[9] if len(loadcell) > 9 else None,
                    "seat_rear_left": loadcell[10] if len(loadcell) > 10 else None,
                    "seat_front_left": loadcell[11] if len(loadcell) > 11 else None,
                }

                print(
                    "[RAW SUMMARY]",
                    {
                        "sample_index": sample_index,
                        "frame_type": raw_packet.get("frame_type"),
                        "loadcell_named": loadcell_named,
                        "loadcell_sum": sum(loadcell),
                        "tof_1d": raw_packet.get("tof_1d", []),
                        "tof_3d_len": len(raw_packet.get("tof_3d", [])),
                        "mpu": raw_packet.get("mpu", []),
                    }
                )

            semantic_packet = map_raw_packet(raw_packet)

            extracted = extract_features(semantic_packet, baseline=baseline)
            features = extracted["features"]
            feature_map = extracted["feature_map"]
            delta_map = extracted["delta_map"]

            if DEBUG_SENSOR_RAW and sample_index % DEBUG_SUMMARY_EVERY_N == 0:
                debug_payload = build_debug_sensor_payload(
                    user_id=current_profile["user_id"],
                    raw_packet=raw_packet,
                    semantic_packet=semantic_packet,
                    feature_map=feature_map,
                    delta_map=delta_map,
                )
                print("[DEBUG SENSOR PAYLOAD]")
                print(debug_payload)

            if DEBUG_FEATURES and sample_index % DEBUG_SUMMARY_EVERY_N == 0:
                print(
                    "[DEBUG FEATURE]",
                    {
                        "sample_index": sample_index,
                        "seat_fb_shift": round(feature_map["seat_fb_shift"], 3),
                        "neck_mean": round(feature_map["neck_mean"], 3),
                        "neck_forward_delta": round(feature_map["neck_forward_delta"], 3),
                        "spine_curve": round(feature_map["spine_curve"], 3),
                        "pitch_fused_deg": round(feature_map["pitch_fused_deg"], 3),
                        "back_total": round(feature_map["back_total"], 3),
                        "neck_mean_delta": round(delta_map.get("neck_mean_delta", 0.0), 3),
                        "neck_forward_delta_delta": round(
                            delta_map.get("neck_forward_delta_delta", 0.0), 3
                        ),
                    }
                )

            predicted = classifier.predict(features)
            flags = detect_posture_flags(feature_map, delta_map)
            report_posture = select_report_posture(
                predicted=predicted,
                flags=flags,
                feature_map=feature_map,
            )

            old_report_posture = prev_report_posture
            posture_changed = (
                old_report_posture is not None
                and old_report_posture != report_posture
            )
            runtime_context["prev_report_posture"] = report_posture
            prev_report_posture = report_posture

            sample_logger.log_sample(
                user_id=current_profile["user_id"],
                session_id=session_id,
                raw_packet=raw_packet,
                semantic_packet=semantic_packet,
                feature_map=feature_map,
                delta_map=delta_map,
                predicted=predicted,
                flags=flags,
                label=None,
                source="runtime",
            )

            state = score_engine.update(
                posture=report_posture,
                flags=flags,
                step_samples=1,
            )
            latest_state = state

            if state["alert"]:
                audio.play_posture_alert(predicted)

            metrics = build_monitoring_metrics(feature_map, baseline)

            score_sum += state["score"]
            score_count += 1
            posture_count[report_posture] = posture_count.get(report_posture, 0) + 1

            runtime_context["score_sum"] = score_sum
            runtime_context["score_count"] = score_count
            runtime_context["posture_count"] = posture_count
            runtime_context["latest_state"] = latest_state

            report_gen.add_sample(
                timestamp_sec=state["total_sitting_sec"],
                score=state["score"],
                posture=report_posture,
            )

            realtime_payload = build_realtime_payload(
                user_id=current_profile["user_id"],
                posture=report_posture,
                flags=flags,
                state=state,
                monitoring_metrics=metrics,
            )
            app_server.update_status(realtime_payload)

            # 🔥 압력 분포 항상 전송 (디버깅 안정화 단계)
            distribution_payload = build_sensor_distribution_payload(
                user_id=current_profile["user_id"],
                session_id=session_id,
                sample_index=sample_index,
                raw_packet=raw_packet,
                feature_map=feature_map,
                semantic_packet=semantic_packet,
            )

            app_server.update_status(distribution_payload)

            # 선택 로그
            if DEBUG_SENSOR_DISTRIBUTION and sample_index % DEBUG_SUMMARY_EVERY_N == 0:
                print("[SENSOR DISTRIBUTION]")
                print(json.dumps(distribution_payload, indent=2, ensure_ascii=False))

            active_flags = [k for k, v in flags.items() if v]

            # normal 은 부저 활성 자세 목록에서 제외
            active_bad_postures = {k for k, v in flags.items() if v and k != "normal"}
            if buzzer:
                buzzer.update(active_bad_postures)

            if DEBUG_FLAGS and sample_index % DEBUG_SUMMARY_EVERY_N == 0:
                print(
                    "[DEBUG FLAGS]",
                    {
                        "sample_index": sample_index,
                        "predicted": predicted,
                        "report_posture": report_posture,
                        "active_flags": active_flags,
                    }
                )

            if posture_changed:
                print(
                    "[SNAPSHOT][POSTURE_CHANGED]",
                    {
                        "sample_index": sample_index,
                        "prev_report_posture": old_report_posture,
                        "report_posture": report_posture,
                        "active_flags": active_flags,
                        "seat_fb_shift": round(feature_map["seat_fb_shift"], 3),
                        "neck_mean": round(feature_map["neck_mean"], 3),
                        "neck_forward_delta": round(feature_map["neck_forward_delta"], 3),
                        "spine_curve": round(feature_map["spine_curve"], 3),
                        "pitch_fused_deg": round(feature_map["pitch_fused_deg"], 3),
                        "back_total": round(feature_map["back_total"], 3),
                    }
                )

            print(
                f"[REAL] sample={sample_index} | "
                f"predicted={predicted} ({to_display_label(predicted)}) | "
                f"report_posture={report_posture} | "
                f"flags={active_flags} | "
                f"score={state['score']} | "
                f"duration={state['current_duration_sec']}s | "
                f"alert={state['alert']} | "
                f"alert_stage={state['alert_stage']} | "
                f"penalty={state['penalty_applied']} | "
                f"pitch={round(feature_map['pitch_fused_deg'], 2)} | "
                f"seat_fb={round(feature_map['seat_fb_shift'], 3)} | "
                f"back_total={round(feature_map['back_total'], 2)} | "
                f"neck_mean={round(feature_map['neck_mean'], 2)} | "
                f"loadcell={metrics['loadcell']['balance_score']}({metrics['loadcell']['balance_level']}) | "
                f"spine_tof={metrics['spine_tof']['score']}({metrics['spine_tof']['level']}) | "
                f"neck_tof={metrics['neck_tof']['score']}({metrics['neck_tof']['level']}) | "
                f"chk_fail={receiver.checksum_fail_count} | "
                f"parse_fail={receiver.parse_fail_count}"
            )

    finally:
        if buzzer:
            buzzer.close()