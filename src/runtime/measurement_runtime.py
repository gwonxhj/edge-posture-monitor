from src.communication import session_state as S
from src.communication.uart_protocol import MSG_STAND
from src.communication.app_payload_builder import (
    build_realtime_payload,
    build_stand_event_payload,
)
from src.core.feature_extractor import extract_features
from src.core.monitoring_metrics import build_monitoring_metrics
from src.core.posture_flags import detect_posture_flags
from src.core.posture_mapper import to_display_label
from src.sensor.sensor_mapper import map_raw_packet
from src.app_flow.app_flow_controller import wait_for_restart_decision
from src.app_flow.sit_detector import wait_until_sit_detected


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
):
    print("\n=== 실시간 측정 시작 ===")

    score_sum = runtime_context.get("score_sum", 0.0)
    score_count = runtime_context.get("score_count", 0)
    posture_count = runtime_context.get("posture_count", {})
    latest_state = runtime_context.get("latest_state", None)

    while True:
        control_msg = receiver.read_control_message()
        if control_msg == MSG_STAND:
            print("[UART] STAND 감지")

            stand_payload = build_stand_event_payload(
                user_id=current_profile["user_id"]
            )
            app_server.update_status(stand_payload)

            decision = wait_for_restart_decision(
                app_server=app_server,
                session_manager=session_manager,
                db_manager=db_manager,
            )

            if decision == "decline_resume_after_stand":
                print("사용자가 재시작을 거부하여 측정을 종료함. (STM32 추가 명령 없음)")
                return {
                    "result": "stand_declined",
                    "score_sum": score_sum,
                    "score_count": score_count,
                    "posture_count": posture_count,
                    "latest_state": latest_state,
                }

            if decision == "quit_measurement":
                print("STAND 이후 사용자가 측정 종료를 요청함. (STM32 추가 명령 없음)")
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

        cmd = app_server.get_next_command()
        if cmd is not None:
            from src.communication.app_command_handler import handle_app_command

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

        raw_packet = receiver.read_real_sensor()
        if raw_packet is None:
            continue

        semantic_packet = map_raw_packet(raw_packet)

        extracted = extract_features(semantic_packet, baseline=baseline)
        features = extracted["features"]
        feature_map = extracted["feature_map"]
        delta_map = extracted["delta_map"]

        predicted = classifier.predict(features)
        flags = detect_posture_flags(feature_map, delta_map)

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