"""
UART sensor stream receiver.

STM32에서 전송하는 DAT / CAL binary frame과
STAND ASCII event를 복원하여 상위 runtime으로 전달한다.
"""

import json
import serial

from src.communication.uart_protocol import (
    BAUD_RATE,
    SENSOR_PACKET_DATA_SIZE,
    SENSOR_FRAME_SIZE,
    HEADER_DAT,
    HEADER_CAL,
    STAND_TOKEN,
    calc_checksum,
)
from src.sensor.packet_parser import parse_sensor_packet


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
        self._buffer = bytearray()

        # debug counters
        self.checksum_fail_count = 0
        self.parse_fail_count = 0

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def read_control_message(self):
        """
        ASCII control message reader.
        주의:
        - 이 함수는 READY/ACK/LINK_OK/CHK_SIT/SIT 같은 idle 단계에서만 쓰는 것을 권장.
        - 실시간 binary sensor stream 중에는 사용하지 않는 것이 안전함.
        """
        try:
            line = self.ser.readline()
            if not line:
                return None

            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                return None

            # mock sensor json이면 버퍼에 넣고 control message로는 처리 안 함
            if self.mock_line_mode and text.startswith("{"):
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

    def _read_mock_line_packet(self):
        """
        mock mode:
        JSON line packet reader.
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

            return packet
        except Exception:
            return None

    def _find_next_header_index(self):
        candidates = []
        for header in (HEADER_DAT, HEADER_CAL):
            idx = self._buffer.find(header)
            if idx != -1:
                candidates.append(idx)

        if not candidates:
            return -1
        return min(candidates)

    def _extract_one_sensor_packet(self):
        while True:
            header_idx = self._find_next_header_index()
            stand_idx = self._find_stand_index()

            candidates = [idx for idx in (header_idx, stand_idx) if idx != -1]
            if not candidates:
                # 헤더/이벤트가 전혀 없으면 버퍼가 너무 커지지 않게 정리
                if len(self._buffer) > SENSOR_FRAME_SIZE * 2:
                    # DAT:/CAL: 또는 STAND\n 가 다음 chunk와 이어질 수 있으니
                    # 마지막 몇 바이트만 남김
                    del self._buffer[:-6]
                return None

            start_idx = min(candidates)

            if start_idx > 0:
                del self._buffer[:start_idx]

            # STAND 이벤트가 더 앞에 있는 경우 우선 처리
            if stand_idx == start_idx:
                if len(self._buffer) < len(STAND_TOKEN):
                    return None

                token = bytes(self._buffer[:len(STAND_TOKEN)])
                if token == STAND_TOKEN:
                    del self._buffer[:len(STAND_TOKEN)]
                    return {
                        "frame_type": "EVENT",
                        "event": "STAND",
                    }
                else:
                    del self._buffer[0]
                    continue

            # 여기부터는 binary DAT/CAL packet 처리
            if len(self._buffer) < SENSOR_FRAME_SIZE:
                return None

            frame = bytes(self._buffer[:SENSOR_FRAME_SIZE])
            data_packet = frame[:SENSOR_PACKET_DATA_SIZE]
            received_checksum = frame[-1]

            expected_checksum = calc_checksum(data_packet)
            if received_checksum != expected_checksum:
                self.checksum_fail_count += 1
                del self._buffer[0]
                continue

            try:
                parsed = parse_sensor_packet(data_packet)
            except Exception:
                self.parse_fail_count += 1
                del self._buffer[0]
                continue

            del self._buffer[:SENSOR_FRAME_SIZE]
            return parsed

    def read_sensor_packet(self):
        if self.mock_line_mode:
            return self._read_mock_line_packet()

        while True:
            try:
                chunk = self.ser.read(self.ser.in_waiting or 1)
            except serial.SerialException as e:
                print(f"[UART] Serial read exception: {e}")
                return None

            if not chunk:
                return None

            self._buffer.extend(chunk)

            packet = self._extract_one_sensor_packet()
            if packet is not None:
                return packet

    # 하위 호환용 alias
    def read_real_sensor(self):
        return self.read_sensor_packet()
    
    def _find_stand_index(self):
        return self._buffer.find(STAND_TOKEN)