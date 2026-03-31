"""
Binary sensor packet parser.

128-byte UART payload를 unpack하여
loadcell / ToF / MPU 구조의 dict로 변환한다.
"""

import struct
import time

from src.communication.uart_protocol import (
    SENSOR_PACKET_DATA_SIZE,
    UNPACK_FORMAT,
    HEADER_DAT,
    HEADER_CAL,
)


def parse_sensor_packet(data_packet: bytes):
    """
    data_packet must be exactly 128 bytes
    format: <4s 12i 32H 4H 2h
    """
    expected_size = struct.calcsize(UNPACK_FORMAT)
    if expected_size != SENSOR_PACKET_DATA_SIZE:
        raise ValueError(
            f"UNPACK_FORMAT size mismatch: calcsize={expected_size}, "
            f"expected={SENSOR_PACKET_DATA_SIZE}"
        )

    if len(data_packet) != SENSOR_PACKET_DATA_SIZE:
        raise ValueError(
            f"Invalid data packet size: expected {SENSOR_PACKET_DATA_SIZE}, got {len(data_packet)}"
        )

    unpacked = struct.unpack(UNPACK_FORMAT, data_packet)

    header = unpacked[0]
    if header not in (HEADER_DAT, HEADER_CAL):
        raise ValueError(f"Invalid packet header: {header!r}")

    frame_type = header.decode("ascii").rstrip(":")

    loadcell = list(unpacked[1:13])
    tof_3d = list(unpacked[13:45])
    tof_1d = list(unpacked[45:49])
    mpu = list(unpacked[49:51])

    return {
        "frame_type": frame_type,
        "received_at_ms": int(time.time() * 1000),
        "loadcell": loadcell,
        "tof_1d": tof_1d,
        "tof_3d": tof_3d,
        "mpu": mpu,
    }