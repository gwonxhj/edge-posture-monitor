from src.communication import session_state as S
from src.communication.app_payload_builder import (
    build_realtime_payload,
    build_stand_event_payload,
)
from src.communication.app_command_handler import handle_app_command
from src.communication.uart_protocol import MSG_CAL_DONE

from src.core.feature_extractor import extract_features
from src.core.monitoring_metrics import build_monitoring_metrics
from src.core.posture_flags import detect_posture_flags
from src.core.posture_mapper import to_display_label

from src.sensor.sensor_mapper import map_raw_packet

from src.app_flow.sit_detector import wait_until_sit_detected
from src.app_flow.app_flow_controller import wait_for_restart_decision


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

    score_sum = runtime_context.get("score_sum", 0.0)
    score_count = runtime_context.get("score_count", 0)
    posture_count = runtime_context.get("posture_count", {})
    latest_state = runtime_context.get("latest_state", None)

    while True:
        cmd = app_server.get_next_command()
        if cmd is not None:
            result = handle_app_command(
                cmd=cmd,
                session_manager=session_manager,
                db_manager=db_manager,
                app_server=app_server,
            )
            print("[APP CMD RESULT]", result)

            if result["action"] == "pause_measurement":
                print("앱에서 측정 일시정지 요청이 들어와서 STM32로 STOP 전송")
                sender.send_stop()
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
                return {
                    "result": "quit",
                    "score_sum": score_sum,
                    "score_count": score_count,
                    "posture_count": posture_count,
                    "latest_state": latest_state,
                }
            
            if result["action"] == "start_calibration":
                # 1. 측정 일시 정지
                sender.send_stop()

                # 2. 착석 확인
                wait_until_sit_detected(receiver, sender)

                # 3. CAL 요청
                sender.send_cal()

                # 4. stage 갱신
                app_server.update_meta({
                    "stage": S.CALIBRATING,
                    "calibration_reason": app_server.latest_meta_payload.get(
                        "calibration_reason", 
                        "recalibration",
                    ),
                })

                # 5. calibration 수행
                new_baseline = calibration_manager.run_calibration_loop(
                    receiver=receiver,
                    mapper_func=map_raw_packet,
                    feature_extractor_func=extract_features,
                    duration_sec=10,
                    verbose=True,
                )

                # 6. STM32의 CAL_DONE 확인
                print("[Measurement] CAL_DONE 대기 중...")
                receiver.wait_for_message(MSG_CAL_DONE, verbose=True)

                # 7. baseline 저장
                session_manager.save_baseline_for_current_user(new_baseline)

                # 필요 시 DB 저장 로직 있으면 추가
                # db_manager.save_baseline(...)

                # 8. 현재 baseline 교체
                baseline = new_baseline

                # 9. 앱 meta 갱신
                app_server.update_meta({
                    "stage": S.MEASURING,
                    "calibration_reason": None,
                })

                # 10. 측정 재개
                sender.send_go()

                print("[Measurement] recalibration completed, measurement resumed")
                continue

        raw_packet = receiver.read_sensor_packet()
        if raw_packet is None:
            continue

        if raw_packet.get("frame_type") == "EVENT":
            if raw_packet.get("event") == "STAND":
                print("[UART] STAND 이벤트 감지")

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
                )

                if decision == "decline_resume_after_stand":
                    print("사용자가 재시작을 거부하여 측정을 종료함.")
                    return {
                        "result": "stand_declined",
                        "score_sum": score_sum,
                        "score_count": score_count,
                        "posture_count": posture_count,
                        "latest_state": latest_state,
                    }

                if decision == "quit_measurement":
                    print("STAND 이후 사용자가 측정 종료를 요청함.")
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
                    sender.send_go()

                    app_server.update_meta({
                        "stage": S.MEASURING,
                    })
                    print("측정 재개")
                    continue

            continue

        if raw_packet.get("frame_type") != "DAT":
            continue

        semantic_packet = map_raw_packet(raw_packet)

        extracted = extract_features(semantic_packet, baseline=baseline)
        features = extracted["features"]
        feature_map = extracted["feature_map"]
        delta_map = extracted["delta_map"]

        predicted = classifier.predict(features)
        flags = detect_posture_flags(feature_map, delta_map)

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
            posture=predicted,
            flags=flags,
            step_samples=1,
        )
        latest_state = state

        if state["alert"]:
            audio.play_posture_alert(predicted)

        metrics = build_monitoring_metrics(feature_map, baseline)

        score_sum += state["score"]
        score_count += 1
        posture_count[predicted] = posture_count.get(predicted, 0) + 1

        runtime_context["score_sum"] = score_sum
        runtime_context["score_count"] = score_count
        runtime_context["posture_count"] = posture_count
        runtime_context["latest_state"] = latest_state

        report_gen.add_sample(
            timestamp_sec=state["total_sitting_sec"],
            score=state["score"],
            posture=predicted,
        )

        realtime_payload = build_realtime_payload(
            user_id=current_profile["user_id"],
            posture=predicted,
            flags=flags,
            state=state,
            monitoring_metrics=metrics,
        )
        app_server.update_status(realtime_payload)

        active_flags = [k for k, v in flags.items() if v]

        print(
            f"[REAL] posture={predicted} ({to_display_label(predicted)}) | "
            f"flags={active_flags} | "
            f"score={state['score']} | "
            f"duration={state['current_duration_sec']}s | "
            f"alert={state['alert']} | "
            f"alert_stage={state['alert_stage']} | "
            f"penalty={state['penalty_applied']} | "
            f"loadcell={metrics['loadcell']['balance_score']}({metrics['loadcell']['balance_level']}) | "
            f"spine_tof={metrics['spine_tof']['score']}({metrics['spine_tof']['level']}) | "
            f"neck_tof={metrics['neck_tof']['score']}({metrics['neck_tof']['level']})"
        )