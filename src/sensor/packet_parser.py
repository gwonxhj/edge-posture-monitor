import struct

from src.communication.uart_protocol import SENSOR_VALUE_COUNT


def parse_sensor_payload(payload: bytes):
    """
    payload format:
    seq            : uint16
    timestamp_ms   : uint32
    values[22]     : 22 x int16

    total = 2 + 4 + 44 = 50 bytes
    """
    fmt = "<HI" + ("h" * SENSOR_VALUE_COUNT)
    expected_size = struct.calcsize(fmt)

    if len(payload) != expected_size:
        raise ValueError(f"Invalid payload size: expected {expected_size}, got {len(payload)}")

    unpacked = struct.unpack(fmt, payload)

    seq = unpacked[0]
    timestamp_ms = unpacked[1]
    values = list(unpacked[2:])

    return {
        "seq": seq,
        "timestamp_ms": timestamp_ms,
        "values": values,
    }