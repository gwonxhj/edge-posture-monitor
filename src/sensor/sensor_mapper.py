def map_raw_packet(raw_packet):
    """
    raw_packet format example:
    {
        "seq": 1,
        "timestamp_ms": 12345,
        "values": [
            v0, v1, ..., v21
        ]
    }

    index meaning:
    0~11 : loadcell
    12~13: VL53L8CX (neck)
    14~17: VL53L0X (spine)
    18~20: MPU6050 gyro filtered x/y/z
    21   : MPU6050 tilt estimate
    """

    values = raw_packet["values"]

    if len(values) < 22:
        raise ValueError(f"Expected at least 22 sensor values, got {len(values)}")

    semantic_packet = {
        "seq": raw_packet["seq"],
        "timestamp_ms": raw_packet["timestamp_ms"],

        "loadcell": {
            "back_right": {
                "top": values[0],
                "upper_mid": values[1],
                "lower_mid": values[2],
                "bottom": values[3],
            },
            "back_left": {
                "top": values[4],
                "upper_mid": values[5],
                "lower_mid": values[6],
                "bottom": values[7],
            },
            "seat_right": {
                "rear": values[8],
                "front": values[9],
            },
            "seat_left": {
                "rear": values[10],
                "front": values[11],
            },
        },

        "tof": {
            "neck": {
                "right": values[12],
                "left": values[13],
            },
            "spine": {
                "upper": values[14],
                "upper_mid": values[15],
                "lower_mid": values[16],
                "lower": values[17],
            },
        },

        "imu": {
            "gyro_x_filt": values[18],
            "gyro_y_filt": values[19],
            "gyro_z_filt": values[20],
            "tilt_est": values[21],
        }
    }

    return semantic_packet