import os
import time

from src.sensor.sensor_receiver import SensorReceiver

from src.app_flow.calibration_flow import run_calibration_flow
from src.app_flow.sit_detector import wait_until_sit_detected
from src.app_flow.app_flow_controller import (
    wait_for_app_profile_command,
    wait_for_calibration_decision,
    wait_for_start_measurement_command,
    wait_for_resume_or_quit_command,
)

from src.core.posture_classifier import PostureClassifier
from src.core.posture_score import PostureScoreEngine

from src.session.profile_manager import ProfileManager
from src.session.calibration import CalibrationManager
from src.session.session_manager import SessionManager

from src.storage.database_manager import DatabaseManager
from src.storage.sample_logger import SampleLogger

from src.feedback.audio_feedback import AudioFeedback

from src.report.report_generator import ReportGenerator
from src.report.report_service import ReportService

from src.communication.command_sender import CommandSender
from src.communication.wifi_server import WiFiServer
from src.communication import session_state as S
from src.communication.uart_protocol import (
    MSG_READY,
    MSG_LINK_OK,
)
from src.communication.app_payload_builder import (
    build_minute_summary_payload,
    build_overall_summary_payload,
)

from src.runtime.measurement_runtime import run_measurement_loop

from src.config.settings import (
    UART_PORT,
    UART_BAUD,
    UART_MOCK_MODE,
    SAMPLE_RATE_HZ,
    ENABLE_SAMPLE_LOGGER,
    HANDSHAKE_AFTER_READY_DELAY_SEC,
    SIT_TO_NEXT_CMD_DELAY_SEC,
)


def finalize_and_save_session(
    runtime_context,
    report_gen,
    db_manager,
    app_server,
    current_profile,
    session_id,
    end_reason="normal_stop",
):
    score_sum = runtime_context.get("score_sum", 0.0)
    score_count = runtime_context.get("score_count", 0)
    posture_count = runtime_context.get("posture_count", {})
    latest_state = runtime_context.get("latest_state", None)

    avg_score = round(score_sum / score_count, 2) if score_count > 0 else 0.0

    dominant_posture = None
    if posture_count:
        dominant_posture = max(posture_count, key=posture_count.get)

    total_sitting_sec = latest_state["total_sitting_sec"] if latest_state else 0
    posture_duration_sec = latest_state["posture_duration_sec"] if latest_state else {}

    print("\n=== Posture Duration Sec ===")
    print(posture_duration_sec)
    print(f"total_sitting_sec={total_sitting_sec}")
    print(f"sum_posture_duration={round(sum(posture_duration_sec.values()), 2) if posture_duration_sec else 0}")

    overall_summary = report_gen.build_overall_summary(
        total_sitting_sec=total_sitting_sec,
        posture_duration_sec=posture_duration_sec,
    )

    minute_summary = report_gen.build_minute_summary()

    report_service = ReportService()
    enhanced_report = report_service.build_enhanced_report(
        overall_summary=overall_summary,
        minute_summary=minute_summary,
    )

    print("\n=== Enhanced Report ===")
    print(enhanced_report)

    print("\n=== Overall Summary ===")
    print(overall_summary)

    print("\n=== Minute Summary ===")
    for item in minute_summary:
        print(item)

    db_manager.end_session(
        session_id=session_id,
        total_sitting_sec=total_sitting_sec,
        avg_score=avg_score,
        dominant_posture=dominant_posture,
        end_reason=end_reason,
    )

    db_manager.save_minute_reports(session_id, minute_summary)
    db_manager.save_daily_report(current_profile["user_id"], overall_summary)
    db_manager.save_enhanced_report(session_id, enhanced_report)

    overall_payload = build_overall_summary_payload(
        user_id=current_profile["user_id"],
        session_id=session_id,
        summary=overall_summary,
    )
    app_server.update_report({
        "type": "enhanced_report",
        "user_id": current_profile["user_id"],
        "session_id": session_id,
        "data": enhanced_report,
    })

    app_server.update_report(overall_payload)

    for item in minute_summary:
        minute_payload = build_minute_summary_payload(
            user_id=current_profile["user_id"],
            session_id=session_id,
            minute_data=item,
        )
        app_server.update_report(minute_payload)

    app_server.update_meta({
        "stage": S.SESSION_SAVED,
        "session_id": session_id,
    })

    print(f"\n세션 저장 완료: session_id={session_id}, end_reason={end_reason}")

def run_uart_handshake(receiver, sender, ready_msg, link_ok_msg):
    print("=== UART Handshake 시작 ===")

    # 1) READY 올 때까지 대기
    receiver.wait_for_message(ready_msg, verbose=True)

    # 2) READY를 본 뒤 ACK 재시도 + LINK_OK 확인
    ack_retry = 0
    max_ack_retry = 20

    while ack_retry < max_ack_retry:
        ack_retry += 1

        if HANDSHAKE_AFTER_READY_DELAY_SEC > 0:
            print(f"[UART] READY 수신 후 {HANDSHAKE_AFTER_READY_DELAY_SEC:.3f}s 대기")
            time.sleep(HANDSHAKE_AFTER_READY_DELAY_SEC)

        # READY 반복 송신으로 RX 버퍼에 남아 있을 수 있는 stale 데이터 정리
        #try:
        #    receiver.ser.reset_input_buffer()
        #    print("[UART] RX buffer flushed before ACK")
        #except Exception as e:
        #    print(f"[UART] RX buffer flush skipped: {e}")

        print(f"[UART] ACK 전송 시도 {ack_retry}/{max_ack_retry}")
        sender.send_ack()

        start_ts = time.time()
        while time.time() - start_ts < 1.0:
            msg = receiver.read_control_message()
            if msg is None:
                continue

            print(f"[UART] RX: {msg}")

            if msg == link_ok_msg:
                print("=== UART 연결 완료 ===")
                return True

            # READY가 또 오면 STM32가 아직 handshake 중인 것으로 보고
            # 다음 루프에서 ACK 재전송
            if msg == ready_msg:
                print("[UART] READY 재수신 -> ACK 재전송 예정")
                break

    raise RuntimeError("UART handshake failed: LINK_OK not received")

def main():
    uart_port = UART_PORT
    uart_mock_mode = UART_MOCK_MODE
    uart_baud = UART_BAUD

    print(f"[UART] using port: {uart_port}")
    print(f"[UART] mock mode: {uart_mock_mode}")
    print(f"[UART] baud: {uart_baud}")

    receiver = SensorReceiver(
        port=uart_port,
        baud_rate=uart_baud,
        mock_line_mode=uart_mock_mode,
    )
    sender = CommandSender(receiver.ser)

    app_server = WiFiServer(host="0.0.0.0", port=8000)
    app_server.start()
    app_server.update_meta({
        "connected": True,
        "stage": "boot_completed",
    })

    profile_manager = ProfileManager()
    session_manager = SessionManager(profile_manager)
    calibration_manager = CalibrationManager(sample_rate_hz=SAMPLE_RATE_HZ)
    db_manager = DatabaseManager()
    sample_logger = SampleLogger(enabled=ENABLE_SAMPLE_LOGGER)

    classifier = PostureClassifier()
    score_engine = PostureScoreEngine(sample_rate_hz=SAMPLE_RATE_HZ)
    audio = AudioFeedback()
    report_gen = ReportGenerator()

    runtime_context = {
        "score_sum": 0.0,
        "score_count": 0,
        "posture_count": {},
        "latest_state": None,
    }

    try:
        run_uart_handshake(
            receiver=receiver,
            sender=sender,
            ready_msg=MSG_READY,
            link_ok_msg=MSG_LINK_OK,
        )

        app_server.update_meta({
            "stage": S.UART_LINK_READY,
        })

        profile_info = wait_for_app_profile_command(
            app_server=app_server,
            session_manager=session_manager,
            db_manager=db_manager,
            sender=sender,
        )

        session_manager.start_session()

        app_server.update_meta({
            "stage": S.PROFILE_LOADED,
            "user_id": profile_info["profile"]["user_id"],
            "user_name": profile_info["profile"]["name"],
        })

        must_calibrate = profile_info["must_calibrate"]
        baseline = session_manager.get_current_baseline()

        if must_calibrate:
            decision = "start_calibration"
        else:
            decision = wait_for_calibration_decision(
                app_server=app_server,
                session_manager=session_manager,
                db_manager=db_manager,
                sender=sender,
            )

        if decision == "start_calibration":
            calibration_reason = app_server.latest_meta_payload.get(
                "calibration_reason",
                "initial",
            )

            baseline = run_calibration_flow(
                receiver=receiver,
                sender=sender,
                calibration_manager=calibration_manager,
                session_manager=session_manager,
                db_manager=db_manager,
                app_server=app_server,
                calibration_reason=calibration_reason,
            )
        else:
            print("앱에서 캘리브레이션 생략 선택")

        decision = wait_for_start_measurement_command(
            app_server=app_server,
            session_manager=session_manager,
            db_manager=db_manager,
            sender=sender,
        )

        if decision == "cancel":
            print("앱에서 측정 시작을 취소함.")
            sender.send_stop()
            session_manager.end_session()
            return

        print("앱에서 측정 시작 요청 확인")
        print("RPi -> STM32 : 착석 확인 요청")

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_MEASURE,
        })

        wait_until_sit_detected(receiver, sender)

        if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
            print(f"[RPi] SIT 확인 후 {SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기")
            time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

        print("측정 시작 명령 전송")
        sender.send_go()
        session_manager.mark_measurement_started()

        app_server.update_meta({
            "stage": S.MEASURING,
        })

        current_profile = session_manager.get_current_profile()
        baseline = session_manager.get_current_baseline()

        print(f"[DB CHECK] creating session for user_id={current_profile['user_id']}")

        session_id = db_manager.create_session(current_profile["user_id"])

        sample_logger.start_session_log(
            user_id=current_profile["user_id"],
            session_id=session_id,
        )

        final_reason = "normal_stop"

        while True:
            result = run_measurement_loop(
                receiver=receiver,
                sender=sender,
                app_server=app_server,
                classifier=classifier,
                score_engine=score_engine,
                session_manager=session_manager,
                db_manager=db_manager,
                report_gen=report_gen,
                audio=audio,
                current_profile=current_profile,
                baseline=baseline,
                session_id=session_id,
                runtime_context=runtime_context,
                calibration_manager=calibration_manager,
                sample_logger=sample_logger,
            )

            if result is None:
                final_reason = "runtime_ended"
                break

            if result["result"] == "paused":
                decision = wait_for_resume_or_quit_command(
                    app_server=app_server,
                    session_manager=session_manager,
                    db_manager=db_manager,
                    sender=sender,
                )

                if decision == "resume":
                    print("일시정지 후 측정 재개 요청 확인")
                    app_server.update_meta({
                        "stage": S.WAIT_SIT_FOR_MEASURE,
                    })
                    wait_until_sit_detected(receiver, sender)

                    if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
                        print(f"[RPi] SIT 확인 후 {SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기")
                        time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

                    sender.send_go()

                    baseline = session_manager.get_current_baseline()

                    app_server.update_meta({
                        "stage": S.MEASURING,
                    })
                    continue

                if decision == "recalibration":
                    print("일시정지 상태에서 재캘리브레이션 요청 확인")

                    baseline = run_calibration_flow(
                        receiver=receiver,
                        sender=sender,
                        calibration_manager=calibration_manager,
                        session_manager=session_manager,
                        db_manager=db_manager,
                        app_server=app_server,
                        calibration_reason="recalibration",
                    )

                    decision = wait_for_start_measurement_command(
                        app_server=app_server,
                        session_manager=session_manager,
                        db_manager=db_manager,
                        sender=sender,
                    )

                    if decision == "cancel":
                        print("재캘리브레이션 후 측정 시작을 취소")
                        sender.send_stop()
                        final_reason = "quit_after_recalibration"
                        break

                    print("재캘리브레이션 후 측정 시작 요청 확인")
                    app_server.update_meta({
                        "stage": S.WAIT_SIT_FOR_MEASURE,
                    })

                    wait_until_sit_detected(receiver, sender)

                    if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
                        print(f"[RPi] SIT 확인 후 {SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기")
                        time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

                    sender.send_go()

                    baseline = session_manager.get_current_baseline()

                    app_server.update_meta({
                        "stage": S.MEASURING,
                    })
                    continue

                if decision == "quit":
                    print("일시정지 상태에서 측정 종료 요청 확인")
                    sender.send_stop()
                    final_reason = "quit_after_pause"
                    break

            if result["result"] == "quit":
                final_reason = "quit"
                break

            if result["result"] == "stand_declined":
                final_reason = "stand_declined"
                break

            final_reason = result["result"]
            break

        finalize_and_save_session(
            runtime_context=runtime_context,
            report_gen=report_gen,
            db_manager=db_manager,
            app_server=app_server,
            current_profile=current_profile,
            session_id=session_id,
            end_reason=final_reason,
        )

        session_manager.end_session()

    finally:
        app_server.stop()
        receiver.close()


if __name__ == "__main__":
    main()