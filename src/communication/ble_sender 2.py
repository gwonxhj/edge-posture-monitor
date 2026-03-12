import json


class BLESender:

    def __init__(self):
        # 실제 BLE 연결은 나중 단계에서 붙인다
        self.connected = False

    def send(self, payload: dict):
        """
        BLE 전송 (현재는 콘솔 출력)
        """

        message = json.dumps(payload, ensure_ascii=False)

        # BLE 연결 전 테스트용
        print("\n[BLE SEND]")
        print(message)