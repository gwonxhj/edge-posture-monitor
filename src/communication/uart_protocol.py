# src/communication/uart_protocol.py

BAUD_RATE = 921600
SERIAL_PORT = "/dev/ttyAMA3"

# -------------------------------------------------------------------
# Binary sensor stream contract
# -------------------------------------------------------------------
# 128 bytes data packet + 1 byte checksum = 129 bytes total frame
#
# Data packet format:
#   <4s 12i 32H 4H 2h
#
# 4s   : header -> b"DAT:" or b"CAL:"
# 12i  : loadcell 12 channels (int32)
# 32H  : 3D ToF 32 channels (uint16)
# 4H   : 1D ToF 4 channels (uint16)
# 2h   : MPU6050 pitch angles 2 channels (int16, degree)
# -------------------------------------------------------------------

SENSOR_PACKET_DATA_SIZE = 128
SENSOR_FRAME_SIZE = 129  # 128 data + 1 checksum
UNPACK_FORMAT = "<4s 12i 32H 4H 2h"

HEADER_DAT = b"DAT:"
HEADER_CAL = b"CAL:"
STREAM_HEADERS = (HEADER_DAT, HEADER_CAL)

LOADCELL_COUNT = 12
TOF_1D_COUNT = 4
TOF_3D_COUNT = 32
MPU_COUNT = 2

# Loadcell index map in 12i
IDX_BACK_RIGHT_TOP = 0
IDX_BACK_RIGHT_UPPER_MID = 1
IDX_BACK_RIGHT_LOWER_MID = 2
IDX_BACK_RIGHT_BOTTOM = 3

IDX_BACK_LEFT_TOP = 4
IDX_BACK_LEFT_UPPER_MID = 5
IDX_BACK_LEFT_LOWER_MID = 6
IDX_BACK_LEFT_BOTTOM = 7

IDX_SEAT_REAR_RIGHT = 8
IDX_SEAT_FRONT_RIGHT = 9
IDX_SEAT_REAR_LEFT = 10
IDX_SEAT_FRONT_LEFT = 11

# 1D ToF index map in 4H
IDX_SPINE_UPPER = 0
IDX_SPINE_UPPER_MID = 1
IDX_SPINE_LOWER_MID = 2
IDX_SPINE_LOWER = 3

# MPU index map in 2h
IDX_MPU_RIGHT = 0
IDX_MPU_LEFT = 1

# ASCII control messages
MSG_READY = "READY"
MSG_ACK = "ACK"
MSG_LINK_OK = "LINK_OK"

MSG_CHK_SIT = "CHK_SIT"
MSG_SIT = "SIT"
MSG_CAL = "CAL"
MSG_CAL_DONE = "CAL_DONE"
MSG_GO = "GO"
MSG_STOP = "STOP"
MSG_QUIT = "QUIT"
MSG_STAND = "STAND"

STAND_TOKEN = b"STAND\n"


def calc_checksum(data_128: bytes) -> int:
    value = 0
    for b in data_128:
        value ^= b
    return value