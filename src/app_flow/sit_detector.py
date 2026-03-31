import time

from src.communication.uart_protocol import MSG_SIT


def wait_until_sit_detected(
    receiver,
    sender,
    interval_sec=1.0,
    stable_wait_sec=2.0,
):
    """
    STM32에 CHK_SIT을 주기적으로 보내면서 SIT 응답을 기다림.

    - 최초 SIT를 받아도 바로 통과하지 않고
      stable_wait_sec 동안 연속적으로 SIT가 확인되어야 착석 확정.
    - 살짝 닿자마자 캘리브레이션이 바로 시작되는 문제를 줄이기 위한 안정화 대기.
    """
    print("[RPi] 착석 확인 polling 시작")

    sit_started_at = None

    while True:
        sender.send_check_sit()

        start = time.time()
        got_sit_in_this_round = False

        while time.time() - start < interval_sec:
            msg = receiver.read_control_message()

            if msg == MSG_SIT:
                got_sit_in_this_round = True

            time.sleep(0.05)

        if got_sit_in_this_round:
            if sit_started_at is None:
                sit_started_at = time.time()
                print(
                    f"[UART] RX: SIT | 착석 안정화 대기 시작 "
                    f"({stable_wait_sec:.1f}s)"
                )
            else:
                elapsed = time.time() - sit_started_at
                if elapsed >= stable_wait_sec:
                    print("[UART] RX: SIT stable confirmed")
                    return True
        else:
            sit_started_at = None