import argparse
import json
import threading
import time

import serial

from src.sensor.sensor_simulator import read_mock_sensor


class FakeSTM32:
    def __init__(self, port: str, baud: int = 921600):
        self.ser = serial.Serial(port, baud, timeout=0.1)

        self.calibration_sample_count = 0
        self.calibration_max_samples = 500

        self.measure_sample_count = 0
        self.stand_trigger_sample = 300  # 약 6초 후 (50Hz 기준)
        self.sent_stand_once = False
        self.waiting_resume = False

        self.mode = "idle"   # idle / calibration / measure
        self.running = True
        self.seq = 0

        # handshake 안정화용
        self.handshake_ack_received = False
        self.ready_interval_sec = 0.5
        self.last_ready_sent_at = 0.0
        self.initial_boot_delay_sec = 2.0

        self.measure_scenario = [
            ("normal", 100),
            ("turtle_neck", 150),
            ("forward_lean", 150),
            ("side_slouch", 120),
            ("leg_cross_suspect", 120),
            ("thinking_pose", 120),
            ("perching", 120),
            ("reclined", 80),
        ]
        self.scenario_idx = 0
        self.scenario_count = 0

    def send_line(self, text: str):
        self.ser.write((text + "\n").encode("utf-8"))
        self.ser.flush()

    def send_json_packet(self, packet: dict):
        self.ser.write((json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8"))
        self.ser.flush()

    def build_measure_packet(self):
        posture, max_count = self.measure_scenario[self.scenario_idx]
        packet = read_mock_sensor(posture=posture)
        packet["seq"] = self.seq
        self.seq += 1

        self.scenario_count += 1
        if self.scenario_count >= max_count:
            self.scenario_count = 0
            self.scenario_idx = (self.scenario_idx + 1) % len(self.measure_scenario)

        return packet

    def build_calibration_packet(self):
        packet = read_mock_sensor(posture="normal")
        packet["seq"] = self.seq
        self.seq += 1
        return packet

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
                        self.send_line("READY")
                        self.last_ready_sent_at = now
                        print("[FAKE STM32] sent READY")

            if self.mode == "calibration":
                packet = self.build_calibration_packet()
                self.send_json_packet(packet)
                self.calibration_sample_count += 1
                time.sleep(0.02)

                if self.calibration_sample_count >= self.calibration_max_samples:
                    self.mode = "idle"
                    self.calibration_sample_count = 0
                    print("[FAKE STM32] calibration completed -> idle")

            elif self.mode == "measure":
                if not self.sent_stand_once and self.measure_sample_count >= self.stand_trigger_sample:
                    self.send_line("STAND")
                    self.sent_stand_once = True
                    self.waiting_resume = True
                    self.mode = "idle"
                    print("[FAKE STM32] sent STAND -> mode idle (waiting resume)")
                    continue

                packet = self.build_measure_packet()
                self.send_json_packet(packet)
                self.measure_sample_count += 1
                time.sleep(0.02)

            else:
                time.sleep(0.01)

    def command_loop(self):
        """
        RPi -> STM32 명령 처리
        """
        print("[FAKE STM32] boot...")

        while self.running:
            line = self.ser.readline()
            if not line:
                continue

            cmd = line.decode("utf-8", errors="ignore").strip()
            if not cmd:
                continue

            print(f"[FAKE STM32] RX: {cmd}")

            if cmd.endswith("ACK"):
                if not self.handshake_ack_received:
                    self.handshake_ack_received = True
                    self.send_line("LINK_OK")
                    print("[FAKE STM32] sent LINK_OK")

            elif cmd.endswith("CHK_SIT"):
                time.sleep(1.0)
                self.send_line("SIT")
                print("[FAKE STM32] sent SIT")

            elif cmd.endswith("CAL"):
                self.mode = "calibration"
                self.calibration_sample_count = 0
                print("[FAKE STM32] mode -> calibration")

            elif cmd.endswith("GO"):
                self.mode = "measure"
                self.waiting_resume = False

                # 재개 후 다시 STAND 테스트가 가능하도록 리셋
                self.measure_sample_count = 0
                self.sent_stand_once = False

                print("[FAKE STM32] mode -> measure")

            elif cmd.endswith("STOP"):
                self.mode = "idle"
                print("[FAKE STM32] mode -> idle")

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
    parser.add_argument("--baud", type=int, default=921600)
    args = parser.parse_args()

    fake = FakeSTM32(port=args.port, baud=args.baud)
    fake.run()


if __name__ == "__main__":
    main()