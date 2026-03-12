import time
from src.communication.uart_protocol import MSG_SIT


def wait_until_sit_detected(receiver, sender, interval_sec=1.0):
    """
    STM32에 CHK_SIT을 주기적으로 보내면서 SIT 응답을 기다림
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