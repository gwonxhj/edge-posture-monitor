import argparse
import struct
import threading
import time

import serial

from src.communication.uart_protocol import (
    BAUD_RATE,
    UNPACK_FORMAT,
    HEADER_DAT,
    HEADER_CAL,
    MSG_READY,
    MSG_LINK_OK,
    MSG_SIT,
    MSG_CAL_DONE,
    MSG_STAND,
    calc_checksum,
)
from src.sensor.sensor_simulator import read_mock_sensor


class FakeSTM32:
    def __init__(self, port: str, baud: int = BAUD_RATE, scenario: str = "mixed"):
        self.ser = serial.Serial(port, baud, timeout=0.1)

        self.scenario_name = scenario

        self.calibration_sample_count = 0
        self.calibration_max_samples = 500

        self.measure_sample_count = 0
        self.stand_trigger_sample = 300  # 약 6초 후 (50Hz 기준)
        self.sent_stand_once = False

        self.mode = "idle"   # idle / calibration / measure
        self.running = True

        # handshake 안정화용
        self.handshake_ack_received = False
        self.ready_interval_sec = 0.5
        self.last_ready_sent_at = 0.0
        self.initial_boot_delay_sec = 2.0

        self.measure_scenario = self._build_measure_scenario(scenario)
        self.scenario_idx = 0
        self.scenario_count = 0

        print(f"[FAKE STM32] scenario: {self.scenario_name}")

    def send_line(self, text: str):
        self.ser.write((text + "\n").encode("utf-8"))
        self.ser.flush()

    def _build_binary_frame(self, header: bytes, packet: dict) -> bytes:
        loadcell = packet["loadcell"]
        tof_1d = packet["tof_1d"]
        tof_3d = packet["tof_3d"]
        mpu = packet["mpu"]

        data_128 = struct.pack(
            UNPACK_FORMAT,
            header,
            *loadcell,
            *tof_1d,
            *tof_3d,
            *mpu,
        )
        checksum = calc_checksum(data_128)
        return data_128 + bytes([checksum])

    def send_binary_packet(self, header: bytes, packet: dict):
        frame = self._build_binary_frame(header, packet)
        self.ser.write(frame)
        self.ser.flush()

    def build_measure_packet(self):
        posture, max_count = self.measure_scenario[self.scenario_idx]
        packet = read_mock_sensor(posture=posture)

        self.scenario_count += 1
        if self.scenario_count >= max_count:
            self.scenario_count = 0
            self.scenario_idx = (self.scenario_idx + 1) % len(self.measure_scenario)

        return packet
    
    def _build_measure_scenario(self, scenario_name: str):
        if scenario_name == "normal_only":
            return [("normal", 999999)]

        if scenario_name == "turtle_neck_only":
            return [("turtle_neck", 999999)]

        if scenario_name == "forward_lean_only":
            return [("forward_lean", 999999)]

        if scenario_name == "side_slouch_only":
            return [("side_slouch", 999999)]
        
        if scenario_name == "leg_cross_only":
            return [("leg_cross_suspect", 999999)]
        
        if scenario_name == "thinking_pose_only":
            return [("thinking_pose", 999999)]

        if scenario_name == "perching_only":
            return [("perching", 999999)]
        
        if scenario_name == "reclined_only":
            return [("reclined", 999999)]

        # default: mixed
        return [
            ("normal", 100),
            ("turtle_neck", 150),
            ("forward_lean", 150),
            ("side_slouch", 120),
            ("leg_cross_suspect", 120),
            ("thinking_pose", 120),
            ("perching", 120),
            ("reclined", 80),
        ]

    def build_calibration_packet(self):
        return read_mock_sensor(posture="normal")

    def sender_loop(self):
        """
        mode에 따라 50Hz로 센서 패킷 송신
        + ACK 받기 전까지 READY 재전송
        """
        boot_time = time.time()

        while self.running:
            now = time.time()

            # handshake가 끝나지 않았다면 READY를 주기적으로 반복 송신
            if not self.handshake_ack_received:
                if now - boot_time >= self.initial_boot_delay_sec:
                    if now - self.last_ready_sent_at >= self.ready_interval_sec:
                        self.send_line(MSG_READY)
                        self.last_ready_sent_at = now
                        print("[FAKE STM32] sent READY")

            if self.mode == "calibration":
                packet = self.build_calibration_packet()
                self.send_binary_packet(HEADER_CAL, packet)
                self.calibration_sample_count += 1
                time.sleep(0.02)

                if self.calibration_sample_count >= self.calibration_max_samples:
                    self.mode = "idle"
                    self.calibration_sample_count = 0
                    self.send_line(MSG_CAL_DONE)
                    print("[FAKE STM32] sent CAL_DONE -> mode idle")

            elif self.mode == "measure":
                if not self.sent_stand_once and self.measure_sample_count >= self.stand_trigger_sample:
                    self.send_line(MSG_STAND)
                    self.sent_stand_once = True
                    self.mode = "idle"
                    print("[FAKE STM32] sent STAND -> mode idle")
                    continue

                packet = self.build_measure_packet()
                self.send_binary_packet(HEADER_DAT, packet)
                self.measure_sample_count += 1
                time.sleep(0.02)

            else:
                time.sleep(0.01)

    def command_loop(self):
        """
        RPi -> STM32 ASCII 명령 처리
        """
        print("[FAKE STM32] boot...")

        while self.running:
            try:
                line = self.ser.readline()
            except serial.SerialException as e:
                print(f"[FAKE STM32] serial exception: {e}")
                break

            if not line:
                continue

            cmd = line.decode("utf-8", errors="ignore").strip()
            if not cmd:
                continue

            print(f"[FAKE STM32] RX: {cmd}")

            if cmd == "ACK":
                if not self.handshake_ack_received:
                    self.handshake_ack_received = True
                    self.send_line(MSG_LINK_OK)
                    print("[FAKE STM32] sent LINK_OK")

            elif cmd == "CHK_SIT":
                time.sleep(1.0)
                self.send_line(MSG_SIT)
                print("[FAKE STM32] sent SIT")

            elif cmd == "CAL":
                self.mode = "calibration"
                self.calibration_sample_count = 0
                print("[FAKE STM32] mode -> calibration")

            elif cmd == "GO":
                self.mode = "measure"
                self.measure_sample_count = 0
                self.sent_stand_once = False
                print("[FAKE STM32] mode -> measure")

            elif cmd == "STOP":
                self.mode = "idle"
                print("[FAKE STM32] mode -> idle")

            elif cmd == "QUIT":
                self.mode = "idle"
                print("[FAKE STM32] mode -> idle (QUIT)")

    def run(self):
        sender_thread = threading.Thread(target=self.sender_loop, daemon=True)
        sender_thread.start()

        try:
            self.command_loop()
        except KeyboardInterrupt:
            print("\n[FAKE STM32] stopping...")
        finally:
            self.running = False
            self.ser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="serial port for fake stm32")
    parser.add_argument("--baud", type=int, default=BAUD_RATE)
    parser.add_argument(
        "--scenario",
        default="mixed",
        choices=[
            "mixed",
            "normal_only",
            "turtle_neck_only",
            "forward_lean_only",
            "side_slouch_only",
            "leg_cross_only",
            "thinking_pose_only",
            "perching_only",
            "reclined_only",
        ],
        help="fake posture scenario",
    )
    args = parser.parse_args()

    fake = FakeSTM32(
        port=args.port, 
        baud=args.baud,
        scenario=args.scenario,
    )
    fake.run()


if __name__ == "__main__":
    main()