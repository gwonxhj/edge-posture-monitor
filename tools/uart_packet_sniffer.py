import serial
import struct
import time

SERIAL_PORT = '/dev/serial0'
BAUD_RATE = 921600
PACKET_SIZE = 129
UNPACK_FORMAT = '<4s 12i 32H 4H 2h B'

HEADERS = (b'DAT:', b'CAL:')


def xor_checksum(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def find_next_header(buffer: bytearray) -> int:
    indices = [buffer.find(h) for h in HEADERS]
    indices = [i for i in indices if i != -1]
    return min(indices) if indices else -1


def receive_pure_data():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    buffer = bytearray()
    packet_count = 0
    checksum_fail_count = 0
    last_print_time = time.time()

    print("📡 UART packet sniffing start...")

    try:
        while True:
            buffer += ser.read(ser.in_waiting or 1)

            while len(buffer) >= PACKET_SIZE:
                start_idx = find_next_header(buffer)

                if start_idx == -1:
                    if len(buffer) > PACKET_SIZE * 2:
                        buffer.clear()
                    break

                if len(buffer) < start_idx + PACKET_SIZE:
                    break

                packet = bytes(buffer[start_idx:start_idx + PACKET_SIZE])
                del buffer[:start_idx + PACKET_SIZE]

                received_checksum = packet[-1]
                calc = xor_checksum(packet[:-1])

                if received_checksum != calc:
                    checksum_fail_count += 1
                    print(
                        f"❌ checksum mismatch | recv={received_checksum} calc={calc} "
                        f"| fail_count={checksum_fail_count}"
                    )
                    continue

                unpacked = struct.unpack(UNPACK_FORMAT, packet)

                header = unpacked[0].decode('utf-8')
                hx711 = unpacked[1:13]

                tof3d = unpacked[13:45]   # 32개
                tof1d = unpacked[45:49]   # 4개

                mpu = unpacked[49:51]

                packet_count += 1

                now = time.time()
                if now - last_print_time >= 0.5:
                    print(f"[{header}] packet_count={packet_count}")
                    print(f"  loadcell12 = {hx711}")
                    print(f"  tof1d      = {tof1d}")
                    print(f"  mpu        = {mpu}")
                    print(f"  tof3d[0:8] = {tof3d[:8]}")
                    print("-" * 60)
                    last_print_time = now

    except KeyboardInterrupt:
        print("\n🛑 수신 종료")
        print(f"total packets: {packet_count}")
        print(f"checksum fails: {checksum_fail_count}")
    finally:
        ser.close()


if __name__ == '__main__':
    receive_pure_data()