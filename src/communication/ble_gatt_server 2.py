import time
import json
import threading
from queue import Queue, Empty
from typing import Any

from src.communication.ble_constants import (
    DEVICE_NAME,
    POSTURE_SERVICE_UUID,
    CONTROL_RX_CHAR_UUID,
    STATUS_TX_CHAR_UUID,
    REPORT_TX_CHAR_UUID,
    META_CHAR_UUID,
)

# -----------------------------
# Optional Linux/RPi BLE backend
# - macOS / 개발 PC에서는 mock mode
# - Raspberry Pi(Linux) + bluezero 설치 환경에서만 real BLE mode
# -----------------------------
adapter: Any = None
peripheral: Any = None
BLUEZERO_AVAILABLE = False

try:
    from bluezero import adapter as _adapter
    from bluezero import peripheral as _peripheral

    adapter = _adapter
    peripheral = _peripheral
    BLUEZERO_AVAILABLE = True
except Exception:
    adapter = None
    peripheral = None
    BLUEZERO_AVAILABLE = False


class BleCommandQueue:
    def __init__(self):
        self._queue = Queue()

    def put(self, cmd: dict):
        self._queue.put(cmd)

    def get_nowait(self):
        try:
            return self._queue.get_nowait()
        except Empty:
            return None


class BleGattServer:
    """
    개발용:
    - macOS / bluezero 미설치 환경에서는 mock 모드
    실사용:
    - Raspberry Pi + bluezero 환경에서는 real BLE mode
    """

    def __init__(self, adapter_address=None):
        self.device_name = DEVICE_NAME
        self.service_uuid = POSTURE_SERVICE_UUID

        self.control_rx_uuid = CONTROL_RX_CHAR_UUID
        self.status_tx_uuid = STATUS_TX_CHAR_UUID
        self.report_tx_uuid = REPORT_TX_CHAR_UUID
        self.meta_uuid = META_CHAR_UUID

        self.command_queue = BleCommandQueue()

        self.latest_status_payload = {}
        self.latest_report_payload = {}
        self.latest_meta_payload = {
            "device_name": self.device_name,
            "service_uuid": self.service_uuid,
            "connected": False,
            "backend": "bluezero" if BLUEZERO_AVAILABLE else "mock",
        }

        self._running = False
        self._server_thread = None
        self._peripheral = None
        self.adapter_address = adapter_address

    # -------------------------------------------------
    # public API
    # -------------------------------------------------
    def start(self):
        if self._running:
            return

        self._running = True

        if BLUEZERO_AVAILABLE:
            self._server_thread = threading.Thread(target=self._run_real, daemon=True)
            self._server_thread.start()
            print("[BLE] GATT server starting in real mode (bluezero)")
        else:
            self._server_thread = threading.Thread(target=self._run_mock, daemon=True)
            self._server_thread.start()
            print("[BLE] GATT server starting in mock mode")

    def stop(self):
        self._running = False

        if BLUEZERO_AVAILABLE:
            try:
                if self._peripheral is not None:
                    self._peripheral.stop()
            except Exception as e:
                print(f"[BLE] stop error: {e}")

        print("[BLE] GATT server stopped")

    def get_next_command(self):
        return self.command_queue.get_nowait()

    def update_status(self, payload: dict):
        self.latest_status_payload = payload
        print("[BLE][STATUS NOTIFY]")
        print(json.dumps(payload, ensure_ascii=False))

    def update_report(self, payload: dict):
        self.latest_report_payload = payload
        print("[BLE][REPORT NOTIFY]")
        print(json.dumps(payload, ensure_ascii=False))

    def update_meta(self, payload: dict):
        self.latest_meta_payload.update(payload)
        print("[BLE][META]")
        print(json.dumps(self.latest_meta_payload, ensure_ascii=False))

    # -------------------------------------------------
    # mock helpers
    # -------------------------------------------------
    def inject_mock_command(self, cmd: dict):
        """
        개발 중 앱 명령을 흉내낼 때 수동으로 넣을 수 있는 함수
        """
        self.command_queue.put(cmd)

    def on_control_write(self, raw_text: str):
        """
        앱이 control_rx characteristic에 썼다고 가정하는 mock/공통 handler
        """
        try:
            payload = json.loads(raw_text)
            self.command_queue.put(payload)
            print(f"[BLE] RX control: {payload}")
        except Exception as e:
            print(f"[BLE] Invalid control payload: {e} | raw={raw_text}")

    def get_status_json(self) -> str:
        return json.dumps(self.latest_status_payload, ensure_ascii=False)

    def get_report_json(self) -> str:
        return json.dumps(self.latest_report_payload, ensure_ascii=False)

    def get_meta_json(self) -> str:
        return json.dumps(self.latest_meta_payload, ensure_ascii=False)

    # -------------------------------------------------
    # mock mode
    # -------------------------------------------------
    def _run_mock(self):
        while self._running:
            time.sleep(0.05)

    # -------------------------------------------------
    # real bluezero mode
    # -------------------------------------------------
    def _control_write_callback(self, value, options):
        try:
            if isinstance(value, bytes):
                raw = value.decode("utf-8")
            else:
                raw = bytes(value).decode("utf-8")

            payload = json.loads(raw)
            self.command_queue.put(payload)
            print("[BLE] RX control:", payload)
        except Exception as e:
            print(f"[BLE] control write parse error: {e}")

    def _status_read(self):
        return bytearray(
            json.dumps(self.latest_status_payload, ensure_ascii=False).encode("utf-8")
        )

    def _report_read(self):
        return bytearray(
            json.dumps(self.latest_report_payload, ensure_ascii=False).encode("utf-8")
        )

    def _meta_read(self):
        return bytearray(
            json.dumps(self.latest_meta_payload, ensure_ascii=False).encode("utf-8")
        )

    def _run_real(self):
        try:
            if self.adapter_address is None:
                dongles = adapter.Adapter.available()
                if not dongles:
                    raise RuntimeError("No BLE adapter found")
                self.adapter_address = dongles[0].address

            print(f"[BLE] using adapter: {self.adapter_address}")

            self._peripheral = peripheral.Peripheral(
                adapter_addr=self.adapter_address,
                local_name=self.device_name,
                appearance=0,
            )

            self._peripheral.add_service(
                srv_id=1,
                uuid=self.service_uuid,
                primary=True,
            )

            # App -> RPi
            self._peripheral.add_characteristic(
                srv_id=1,
                chr_id=1,
                uuid=self.control_rx_uuid,
                value=[],
                notifying=False,
                flags=["write", "write-without-response"],
                write_callback=self._control_write_callback,
            )

            # RPi -> App
            self._peripheral.add_characteristic(
                srv_id=1,
                chr_id=2,
                uuid=self.status_tx_uuid,
                value=[],
                notifying=False,
                flags=["read", "notify"],
                read_callback=self._status_read,
            )

            self._peripheral.add_characteristic(
                srv_id=1,
                chr_id=3,
                uuid=self.report_tx_uuid,
                value=[],
                notifying=False,
                flags=["read", "notify"],
                read_callback=self._report_read,
            )

            self._peripheral.add_characteristic(
                srv_id=1,
                chr_id=4,
                uuid=self.meta_uuid,
                value=[],
                notifying=False,
                flags=["read"],
                read_callback=self._meta_read,
            )

            self._peripheral.publish()
            self.latest_meta_payload["connected"] = True
            print("[BLE] Peripheral published")

            while self._running:
                time.sleep(0.05)

        except Exception as e:
            print(f"[BLE] server error: {e}")
            self._running = False