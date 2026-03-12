from src.communication import session_state as S
#from src.communication.uart_protocol import MSG_SIT
from src.sensor.sensor_mapper import map_raw_packet
from src.core.feature_extractor import extract_features
from src.app_flow.sit_detector import wait_until_sit_detected


def run_calibration_flow(
    receiver,
    sender,
    calibration_manager,
    session_manager,
    db_manager,
    app_server,
):
    app_server.update_meta({
        "stage": S.WAIT_SIT_FOR_CALIBRATION,
    })

    print("\n자세 측정 전, 정자세 데이터 학습을 위해 의자에 앉아주세요.")
    print("RPi -> STM32 : 착석 확인 요청")

    wait_until_sit_detected(receiver, sender)

    print("착석 확인 완료. 캘리브레이션 시작")
    app_server.update_meta({
        "stage": S.CALIBRATING,
    })
    sender.send_cal()

    baseline = calibration_manager.run_calibration_loop(
        receiver=receiver,
        mapper_func=map_raw_packet,
        feature_extractor_func=extract_features,
        duration_sec=10,
        verbose=True,
    )

    session_manager.save_baseline_for_current_user(baseline)
    current_profile = session_manager.get_current_profile()
    db_manager.save_baseline(current_profile["user_id"], baseline)

    app_server.update_meta({
        "stage": S.CALIBRATION_COMPLETED,
    })

    print("캘리브레이션 저장 완료")
    return baseline