import time
from src.communication.uart_protocol import MSG_SIT


def wait_until_sit_detected(receiver, sender, interval_sec=1.0):
    """
    STM32에 CHK_SIT을 주기적으로 보내면서 SIT 응답을 기다림.

    중요:
    - 이 함수는 ASCII control-only 구간에서만 사용해야 함.
    - 즉, 이 구간에서는 STM32가 DAT:/CAL: binary stream을 보내지 않아야 안전함.
    - binary stream과 readline() 기반 ASCII 읽기를 동시에 섞으면 UART sync가 깨질 수 있음.
    """
    print("[RPi] 착석 확인 polling 시작")

    while True:
        sender.send_check_sit()

        start = time.time()

        while time.time() - start < interval_sec:
            msg = receiver.read_control_message()

            if msg == MSG_SIT:
                print("[UART] RX: SIT")
                return True

            time.sleep(0.05)