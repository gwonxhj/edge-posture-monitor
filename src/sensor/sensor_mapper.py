"""
Raw sensor packet to semantic packet mapper.

raw 배열 기반 센서 데이터를
loadcell / spine ToF / head ToF / MPU 의미 구조로 변환한다.
"""

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

HEAD_VALID_MIN_MM = 80
HEAD_VALID_MAX_MM = 1200

SPINE_VALID_MIN_MM = 30
SPINE_VALID_MAX_MM = 1200

EMA_ALPHA_SPINE = 0.25
EMA_ALPHA_HEAD = 0.20

_PREV_SPINE = {
    "upper": None,
    "upper_mid": None,
    "lower_mid": None,
    "lower": None,
}

_PREV_HEAD = {
    "left_mean": None,
    "right_mean": None,
    "mean": None,
}


def _safe_mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _ema(prev_value, new_value, alpha):
    if prev_value is None:
        return float(new_value)
    return (alpha * float(new_value)) + ((1.0 - alpha) * float(prev_value))


def _is_valid_mm(value, low, high):
    try:
        v = float(value)
    except Exception:
        return False
    return low <= v <= high


def _sanitize_spine_value(key, value):
    prev = _PREV_SPINE.get(key)

    if _is_valid_mm(value, SPINE_VALID_MIN_MM, SPINE_VALID_MAX_MM):
        smoothed = _ema(prev, float(value), EMA_ALPHA_SPINE)
    else:
        smoothed = prev if prev is not None else 0.0

    _PREV_SPINE[key] = smoothed
    return round(smoothed, 3)


def _build_head_summary(tof_3d):
    """
    32개 3D ToF를 summary로 축약.

    패킷 순서 계약:
    - tof_3d[0:16]   : 착석 기준 우측 목 센서 4x4
    - tof_3d[16:32]  : 착석 기준 좌측 목 센서 4x4
    """
    right_half_raw = tof_3d[:16]
    left_half_raw = tof_3d[16:]

    right_half = [
        float(v) for v in right_half_raw
        if _is_valid_mm(v, HEAD_VALID_MIN_MM, HEAD_VALID_MAX_MM)
    ]
    left_half = [
        float(v) for v in left_half_raw
        if _is_valid_mm(v, HEAD_VALID_MIN_MM, HEAD_VALID_MAX_MM)
    ]
    valid_all = right_half + left_half

    raw_right_mean = _safe_mean(right_half)
    raw_left_mean = _safe_mean(left_half)

    if raw_right_mean > 0:
        right_mean = _ema(_PREV_HEAD["right_mean"], raw_right_mean, EMA_ALPHA_HEAD)
    else:
        right_mean = _PREV_HEAD["right_mean"] if _PREV_HEAD["right_mean"] is not None else 0.0

    if raw_left_mean > 0:
        left_mean = _ema(_PREV_HEAD["left_mean"], raw_left_mean, EMA_ALPHA_HEAD)
    else:
        left_mean = _PREV_HEAD["left_mean"] if _PREV_HEAD["left_mean"] is not None else 0.0

    nonzero_means = [v for v in [left_mean, right_mean] if v > 0]
    mean_all_raw = _safe_mean(nonzero_means) if nonzero_means else 0.0

    if mean_all_raw > 0:
        mean_all = _ema(_PREV_HEAD["mean"], mean_all_raw, EMA_ALPHA_HEAD)
    else:
        mean_all = _PREV_HEAD["mean"] if _PREV_HEAD["mean"] is not None else 0.0

    _PREV_HEAD["left_mean"] = left_mean
    _PREV_HEAD["right_mean"] = right_mean
    _PREV_HEAD["mean"] = mean_all

    min_all = min(valid_all) if valid_all else 0.0
    max_all = max(valid_all) if valid_all else 0.0

    return {
        "mean": round(mean_all, 3),
        "min": round(min_all, 3),
        "max": round(max_all, 3),
        "left_mean": round(left_mean, 3),
        "right_mean": round(right_mean, 3),
        "lr_diff": round(abs(left_mean - right_mean), 3),
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

    spine_upper = _sanitize_spine_value("upper", tof_1d[IDX_SPINE_UPPER])
    spine_upper_mid = _sanitize_spine_value("upper_mid", tof_1d[IDX_SPINE_UPPER_MID])
    spine_lower_mid = _sanitize_spine_value("lower_mid", tof_1d[IDX_SPINE_LOWER_MID])
    spine_lower = _sanitize_spine_value("lower", tof_1d[IDX_SPINE_LOWER])

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
                "upper": spine_upper,
                "upper_mid": spine_upper_mid,
                "lower_mid": spine_lower_mid,
                "lower": spine_lower,
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