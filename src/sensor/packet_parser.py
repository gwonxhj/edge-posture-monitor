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
    format: <4s 12i 4H 32H 2h
    """
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
    tof_1d = list(unpacked[13:17])
    tof_3d = list(unpacked[17:49])
    mpu = list(unpacked[49:51])

    return {
        "frame_type": frame_type,               # "DAT" or "CAL"
        "received_at_ms": int(time.time() * 1000),
        "loadcell": loadcell,                   # len 12
        "tof_1d": tof_1d,                       # len 4
        "tof_3d": tof_3d,                       # len 32
        "mpu": mpu,                             # len 2
    }