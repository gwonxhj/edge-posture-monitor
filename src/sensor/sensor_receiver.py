"""
UART sensor stream receiver.
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
        """
        try:
            line = self.ser.readline()
            if not line:
                return None

            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                return None

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
                print(f"[UART RX] {msg}")

            if msg == expected_msg:
                return True

    def _read_mock_line_packet(self):
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
                if len(self._buffer) > SENSOR_FRAME_SIZE * 2:
                    del self._buffer[:-6]
                return None

            start_idx = min(candidates)

            if start_idx > 0:
                del self._buffer[:start_idx]

            if stand_idx == start_idx:
                if len(self._buffer) < len(STAND_TOKEN):
                    return None

                token = bytes(self._buffer[:len(STAND_TOKEN)])
                if token == STAND_TOKEN:
                    del self._buffer[:len(STAND_TOKEN)]
                    print("[UART RX EVENT] STAND")
                    return {
                        "frame_type": "EVENT",
                        "event": "STAND",
                    }
                else:
                    del self._buffer[0]
                    continue

            if len(self._buffer) < SENSOR_FRAME_SIZE:
                return None

            frame = bytes(self._buffer[:SENSOR_FRAME_SIZE])
            data_packet = frame[:SENSOR_PACKET_DATA_SIZE]
            received_checksum = frame[-1]

            expected_checksum = calc_checksum(data_packet)
            if received_checksum != expected_checksum:
                self.checksum_fail_count += 1
                print(
                    "[UART RX ERROR] checksum mismatch | "
                    f"recv={received_checksum} expected={expected_checksum} "
                    f"fail_count={self.checksum_fail_count}"
                )
                del self._buffer[0]
                continue

            try:
                parsed = parse_sensor_packet(data_packet)
            except Exception as e:
                self.parse_fail_count += 1
                print(
                    "[UART RX ERROR] packet parse failed | "
                    f"error={e} fail_count={self.parse_fail_count}"
                )
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

    def read_real_sensor(self):
        return self.read_sensor_packet()

    def _find_stand_index(self):
        return self._buffer.find(STAND_TOKEN)