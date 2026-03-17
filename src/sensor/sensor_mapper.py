# src/sensor/sensor_mapper.py

from src.communication.uart_protocol import (
    IDX_BACK_RIGHT_TOP,
    IDX_BACK_RIGHT_UPPER_MID,
    IDX_BACK_RIGHT_LOWER_MID,
    IDX_BACK_RIGHT_BOTTOM,
    IDX_BACK_LEFT_TOP,
    IDX_BACK_LEFT_UPPER_MID,
    IDX_BACK_LEFT_LOWER_MID,
    IDX_BACK_LEFT_BOTTOM,
    IDX_SEAT_REAR_RIGHT,
    IDX_SEAT_FRONT_RIGHT,
    IDX_SEAT_REAR_LEFT,
    IDX_SEAT_FRONT_LEFT,
    IDX_SPINE_UPPER,
    IDX_SPINE_UPPER_MID,
    IDX_SPINE_LOWER_MID,
    IDX_SPINE_LOWER,
    IDX_MPU_RIGHT,
    IDX_MPU_LEFT,
)


def _safe_mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _build_head_summary(tof_3d):
    """
    32개 3D ToF를 단순 summary로 축약.
    지금 단계에서는 16/16으로 좌우 반을 나누는 단순 방식 사용.
    """
    left_half = tof_3d[:16]
    right_half = tof_3d[16:]

    left_mean = _safe_mean(left_half)
    right_mean = _safe_mean(right_half)
    mean_all = _safe_mean(tof_3d)
    min_all = min(tof_3d) if tof_3d else 0.0
    max_all = max(tof_3d) if tof_3d else 0.0

    return {
        "mean": mean_all,
        "min": min_all,
        "max": max_all,
        "left_mean": left_mean,
        "right_mean": right_mean,
        "lr_diff": abs(left_mean - right_mean),
    }


def map_raw_packet(raw_packet):
    """
    raw_packet example:
    {
        "frame_type": "DAT" or "CAL",
        "received_at_ms": 123456789,
        "loadcell": [12 ints],
        "tof_1d": [4 ints],
        "tof_3d": [32 ints],
        "mpu": [2 ints],
    }
    """

    loadcell = raw_packet["loadcell"]
    tof_1d = raw_packet["tof_1d"]
    tof_3d = raw_packet["tof_3d"]
    mpu = raw_packet["mpu"]

    if len(loadcell) != 12:
        raise ValueError(f"Expected 12 loadcell values, got {len(loadcell)}")
    if len(tof_1d) != 4:
        raise ValueError(f"Expected 4 1D ToF values, got {len(tof_1d)}")
    if len(tof_3d) != 32:
        raise ValueError(f"Expected 32 3D ToF values, got {len(tof_3d)}")
    if len(mpu) != 2:
        raise ValueError(f"Expected 2 MPU values, got {len(mpu)}")

    head_summary = _build_head_summary(tof_3d)

    semantic_packet = {
        "frame_type": raw_packet["frame_type"],
        "timestamp_ms": raw_packet["received_at_ms"],

        "loadcell": {
            "back_right": {
                "top": loadcell[IDX_BACK_RIGHT_TOP],
                "upper_mid": loadcell[IDX_BACK_RIGHT_UPPER_MID],
                "lower_mid": loadcell[IDX_BACK_RIGHT_LOWER_MID],
                "bottom": loadcell[IDX_BACK_RIGHT_BOTTOM],
            },
            "back_left": {
                "top": loadcell[IDX_BACK_LEFT_TOP],
                "upper_mid": loadcell[IDX_BACK_LEFT_UPPER_MID],
                "lower_mid": loadcell[IDX_BACK_LEFT_LOWER_MID],
                "bottom": loadcell[IDX_BACK_LEFT_BOTTOM],
            },
            "seat_right": {
                "rear": loadcell[IDX_SEAT_REAR_RIGHT],
                "front": loadcell[IDX_SEAT_FRONT_RIGHT],
            },
            "seat_left": {
                "rear": loadcell[IDX_SEAT_REAR_LEFT],
                "front": loadcell[IDX_SEAT_FRONT_LEFT],
            },
        },

        "tof": {
            "spine": {
                "upper": tof_1d[IDX_SPINE_UPPER],
                "upper_mid": tof_1d[IDX_SPINE_UPPER_MID],
                "lower_mid": tof_1d[IDX_SPINE_LOWER_MID],
                "lower": tof_1d[IDX_SPINE_LOWER],
            },
            "head_raw": tof_3d,
            "head_summary": head_summary,
        },

        "imu": {
            "right_pitch_deg": mpu[IDX_MPU_RIGHT],
            "left_pitch_deg": mpu[IDX_MPU_LEFT],
            "pitch_fused_deg": (mpu[IDX_MPU_RIGHT] + mpu[IDX_MPU_LEFT]) / 2.0,
            "pitch_lr_diff_deg": abs(mpu[IDX_MPU_RIGHT] - mpu[IDX_MPU_LEFT]),
        },
    }

    return semantic_packet