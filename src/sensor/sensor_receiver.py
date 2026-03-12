import json
import serial

from src.communication.uart_protocol import (
    BAUD_RATE,
    STX1,
    STX2,
    ETX,
    PACKET_TYPE_SENSOR,
)
from src.sensor.packet_parser import parse_sensor_payload


class SensorReceiver:
    def __init__(
        self,
        port: str,
        baud_rate: int = BAUD_RATE,
        timeout: float = 0.1,
        mock_line_mode: bool = False,
    ):
        self.ser = serial.Serial(port, baud_rate, timeout=timeout)
        self.mock_line_mode = mock_line_mode
        self._pending_mock_packet = None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read_control_message(self):
        """
        Control message reader.
        mock_line_mode에서는 sensor JSON line이 들어오면 버퍼에 저장하고,
        control message가 아니므로 None 반환.
        """
        try:
            line = self.ser.readline()
            if not line:
                return None

            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                return None

            # mock sensor json이면 버퍼에 넣고 control message로는 처리 안 함
            if self.mock_line_mode and text.startswith("{") and '"values"' in text:
                self._pending_mock_packet = text
                return None

            return text
        except Exception:
            return None

    def wait_for_message(self, expected_msg: str, verbose: bool = True):
        while True:
            msg = self.read_control_message()
            if msg is None:
                continue

            if verbose:
                print(f"[UART] RX: {msg}")

            if msg == expected_msg:
                return True

    def _read_exact(self, size: int):
        data = self.ser.read(size)
        if len(data) != size:
            return None
        return data

    def _read_mock_line_packet(self):
        """
        mock mode:
        fake_stm32.py가 JSON line으로 보내는 raw_packet을 읽는다.
        예:
        {"seq":1,"timestamp_ms":123456,"values":[...]}
        """
        try:
            if self._pending_mock_packet is not None:
                text = self._pending_mock_packet
                self._pending_mock_packet = None
            else:
                line = self.ser.readline()
                if not line:
                    return None
                text = line.decode("utf-8", errors="ignore").strip()

            if not text:
                return None

            # control message면 sensor packet이 아니므로 무시
            CONTROL_MESSAGE = {
                "READY",
                "LINK_OK",
                "SIT",
                "STAND",
                "CAL_DONE",
            }
            
            if text in CONTROL_MESSAGE:
                return None

            packet = json.loads(text)

            if not isinstance(packet, dict):
                return None

            if "seq" not in packet or "timestamp_ms" not in packet or "values" not in packet:
                return None

            if not isinstance(packet["values"], list):
                return None

            return packet
        except Exception:
            return None

    def read_real_sensor(self):
        if self.mock_line_mode:
            return self._read_mock_line_packet()

        """
        real mode:
        Binary sensor packet reader.
        Packet format:
        [STX1][STX2][TYPE][LEN_L][LEN_H][PAYLOAD][CHECKSUM][ETX]
        checksum = sum(payload) & 0xFF
        """
        while True:
            first = self.ser.read(1)
            if not first:
                return None

            if first[0] != STX1:
                continue

            second = self.ser.read(1)
            if not second or second[0] != STX2:
                continue

            packet_type = self._read_exact(1)
            if packet_type is None:
                return None

            if packet_type[0] != PACKET_TYPE_SENSOR:
                continue

            length_bytes = self._read_exact(2)
            if length_bytes is None:
                return None

            payload_len = int.from_bytes(length_bytes, byteorder="little")

            payload = self._read_exact(payload_len)
            if payload is None:
                return None

            checksum = self._read_exact(1)
            if checksum is None:
                return None

            etx = self._read_exact(1)
            if etx is None or etx[0] != ETX:
                return None

            calc_checksum = sum(payload) & 0xFF
            if checksum[0] != calc_checksum:
                return None

            try:
                packet = parse_sensor_payload(payload)
                return packet
            except Exception:
                return None