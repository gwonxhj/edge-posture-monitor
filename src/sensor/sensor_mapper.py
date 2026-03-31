"""
Raw sensor packet to semantic packet mapper.
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

# -----------------------------
# VALID RANGE
# -----------------------------
HEAD_VALID_MIN_MM = 30
HEAD_VALID_MAX_MM = 1200

SPINE_VALID_MIN_MM = 30
SPINE_VALID_MAX_MM = 1200

# -----------------------------
# STABILIZATION PARAM
# -----------------------------
EMA_ALPHA_SPINE = 0.25
EMA_ALPHA_HEAD = 0.20

HEAD_MIN_VALID_POINTS = 6
HEAD_MAX_JUMP_MM = 120
SPINE_MAX_JUMP_MM = 150

# -----------------------------
# STATE
# -----------------------------
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

_SPINE_INVALID_STREAK = {
    "upper": 0,
    "upper_mid": 0,
    "lower_mid": 0,
    "lower": 0,
}

_HEAD_INVALID_STREAK = {
    "left": 0,
    "right": 0,
    "all": 0,
}

MAX_INVALID_HOLD_FRAMES = 25


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


# -----------------------------
# SPINE
# -----------------------------
def _sanitize_spine_value(key, value):
    prev = _PREV_SPINE.get(key)

    if _is_valid_mm(value, SPINE_VALID_MIN_MM, SPINE_VALID_MAX_MM):
        value = float(value)

        if prev is not None and abs(value - prev) > SPINE_MAX_JUMP_MM:
            value = prev

        smoothed = _ema(prev, value, EMA_ALPHA_SPINE)
        _SPINE_INVALID_STREAK[key] = 0
    else:
        _SPINE_INVALID_STREAK[key] += 1

        if prev is not None and _SPINE_INVALID_STREAK[key] <= MAX_INVALID_HOLD_FRAMES:
            smoothed = prev
        else:
            # 데드존 진입 시 0.0 대신 최소 유효값으로 고정 (점수 급락 방지)
            smoothed = float(SPINE_VALID_MIN_MM)

    _PREV_SPINE[key] = smoothed
    return round(smoothed, 3)


# -----------------------------
# HEAD (🔥 핵심 수정된 부분)
# -----------------------------
def _build_head_summary(tof_3d):
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

    raw_right_mean = (
        _safe_mean(right_half)
        if len(right_half) >= HEAD_MIN_VALID_POINTS
        else None
    )
    raw_left_mean = (
        _safe_mean(left_half)
        if len(left_half) >= HEAD_MIN_VALID_POINTS
        else None
    )

    # 데드존 진입 시 0.0 대신 최소 유효값으로 고정 (점수 급락 방지)
    _head_floor = float(HEAD_VALID_MIN_MM)

    # RIGHT
    prev_r = _PREV_HEAD["right_mean"]
    if raw_right_mean is not None:
        if prev_r is not None and abs(raw_right_mean - prev_r) > HEAD_MAX_JUMP_MM:
            raw_right_mean = prev_r
        right_mean = _ema(prev_r, raw_right_mean, EMA_ALPHA_HEAD)
        _HEAD_INVALID_STREAK["right"] = 0
    else:
        _HEAD_INVALID_STREAK["right"] += 1
        if prev_r is not None and _HEAD_INVALID_STREAK["right"] <= MAX_INVALID_HOLD_FRAMES:
            right_mean = prev_r
        else:
            right_mean = _head_floor

    # LEFT
    prev_l = _PREV_HEAD["left_mean"]
    if raw_left_mean is not None:
        if prev_l is not None and abs(raw_left_mean - prev_l) > HEAD_MAX_JUMP_MM:
            raw_left_mean = prev_l
        left_mean = _ema(prev_l, raw_left_mean, EMA_ALPHA_HEAD)
        _HEAD_INVALID_STREAK["left"] = 0
    else:
        _HEAD_INVALID_STREAK["left"] += 1
        if prev_l is not None and _HEAD_INVALID_STREAK["left"] <= MAX_INVALID_HOLD_FRAMES:
            left_mean = prev_l
        else:
            left_mean = _head_floor

    # TOTAL
    valid_means = [v for v in [left_mean, right_mean] if v > 0]
    mean_raw = _safe_mean(valid_means) if valid_means else None

    prev_m = _PREV_HEAD["mean"]
    if mean_raw is not None:
        if prev_m is not None and abs(mean_raw - prev_m) > HEAD_MAX_JUMP_MM:
            mean_raw = prev_m
        mean_all = _ema(prev_m, mean_raw, EMA_ALPHA_HEAD)
        _HEAD_INVALID_STREAK["all"] = 0
    else:
        _HEAD_INVALID_STREAK["all"] += 1
        if prev_m is not None and _HEAD_INVALID_STREAK["all"] <= MAX_INVALID_HOLD_FRAMES:
            mean_all = prev_m
        else:
            mean_all = _head_floor

    _PREV_HEAD["left_mean"] = left_mean
    _PREV_HEAD["right_mean"] = right_mean
    _PREV_HEAD["mean"] = mean_all

    valid_all = right_half + left_half

    if valid_all:
        min_all = min(valid_all)
        max_all = max(valid_all)
    else:
        min_all = prev_m if prev_m is not None else 0.0
        max_all = prev_m if prev_m is not None else 0.0

    return {
        "mean": round(mean_all, 3),
        "min": round(min_all, 3),
        "max": round(max_all, 3),
        "left_mean": round(left_mean, 3),
        "right_mean": round(right_mean, 3),
        "lr_diff": round(abs(left_mean - right_mean), 3),
    }


# -----------------------------
# MAIN
# -----------------------------
def map_raw_packet(raw_packet):
    loadcell = raw_packet["loadcell"]
    tof_1d = raw_packet["tof_1d"]
    tof_3d = raw_packet["tof_3d"]
    mpu = raw_packet["mpu"]

    spine_upper = _sanitize_spine_value("upper", tof_1d[IDX_SPINE_UPPER])
    spine_upper_mid = _sanitize_spine_value("upper_mid", tof_1d[IDX_SPINE_UPPER_MID])
    spine_lower_mid = _sanitize_spine_value("lower_mid", tof_1d[IDX_SPINE_LOWER_MID])
    spine_lower = _sanitize_spine_value("lower", tof_1d[IDX_SPINE_LOWER])

    head_summary = _build_head_summary(tof_3d)

    return {
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