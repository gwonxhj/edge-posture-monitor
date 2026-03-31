import time

from src.communication import session_state as S
from src.communication.uart_protocol import MSG_CAL_DONE
from src.sensor.sensor_mapper import map_raw_packet
from src.core.feature_extractor import extract_features
from src.core.sensor_factor import apply_sensor_factors
from src.app_flow.sit_detector import wait_until_sit_detected
from src.config.settings import SIT_TO_NEXT_CMD_DELAY_SEC


def run_calibration_flow(
    receiver,
    sender,
    calibration_manager,
    session_manager,
    db_manager,
    app_server,
    calibration_reason="initial",
):
    app_server.update_meta({
        "stage": S.WAIT_SIT_FOR_CALIBRATION,
        "calibration_reason": calibration_reason,
    })

    print("\n자세 측정 전, 정자세 데이터 학습을 위해 의자에 앉아주세요.")
    print("RPi -> STM32 : 착석 확인 요청")

    wait_until_sit_detected(receiver, sender)

    if SIT_TO_NEXT_CMD_DELAY_SEC > 0:
        print(f"[RPi] SIT 확인 후 {SIT_TO_NEXT_CMD_DELAY_SEC:.3f}s 대기")
        time.sleep(SIT_TO_NEXT_CMD_DELAY_SEC)

    print("착석 확인 완료. 캘리브레이션 시작")
    app_server.update_meta({
        "stage": S.CALIBRATING,
        "calibration_reason": calibration_reason,
    })

    sender.send_cal()

    baseline = calibration_manager.run_calibration_loop(
        receiver=receiver,
        mapper_func=map_raw_packet,
        feature_extractor_func=extract_features,
        duration_sec=10,
        verbose=True,
    )

    print("[RPi] CAL_DONE 대기 중...")
    receiver.wait_for_message(MSG_CAL_DONE, verbose=True)

    session_manager.save_baseline_for_current_user(baseline)
    current_profile = session_manager.get_current_profile()
    db_manager.save_baseline(current_profile["user_id"], baseline)

    app_server.update_meta({
        "stage": S.CALIBRATION_COMPLETED,
        "calibration_reason": None,
    })

    print("캘리브레이션 저장 완료")
    return baseline