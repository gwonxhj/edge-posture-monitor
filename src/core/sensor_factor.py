from copy import deepcopy
from typing import Any

from src.config.settings import (
    FACTOR_ENABLE,
    LOADCELL_FACTORS,
    TOF_1D_FACTORS,
    TOF_3D_FACTORS,
)


LOADCELL_ORDER = [
    "back_right_top",
    "back_right_upper_mid",
    "back_right_lower_mid",
    "back_right_bottom",
    "back_left_top",
    "back_left_upper_mid",
    "back_left_lower_mid",
    "back_left_bottom",
    "seat_rear_right",
    "seat_front_right",
    "seat_rear_left",
    "seat_front_left",
]

TOF_1D_ORDER = [
    "spine_upper",
    "spine_upper_mid",
    "spine_lower_mid",
    "spine_lower",
]


def _safe_apply_factor(value: Any, factor: float):
    try:
        return type(value)(round(float(value) * float(factor)))
    except Exception:
        return value


def apply_sensor_factors(raw_packet: dict) -> dict:
    """
    raw_packet에 센서별 factor를 적용한 새 dict를 반환한다.

    현재는 factor 구조만 먼저 반영하는 단계이므로,
    settings.py 기본값을 모두 1.0으로 두면 기존 동작과 동일하다.
    """
    if not FACTOR_ENABLE:
        return raw_packet

    corrected = deepcopy(raw_packet)

    # -------------------------------------------------
    # Loadcell factor 적용
    # -------------------------------------------------
    loadcell = corrected.get("loadcell", [])
    if isinstance(loadcell, list) and loadcell:
        new_loadcell = []
        for idx, value in enumerate(loadcell):
            if idx < len(LOADCELL_ORDER):
                key = LOADCELL_ORDER[idx]
                factor = LOADCELL_FACTORS.get(key, 1.0)
            else:
                factor = 1.0
            new_loadcell.append(_safe_apply_factor(value, factor))
        corrected["loadcell"] = new_loadcell

    # -------------------------------------------------
    # 1D ToF factor 적용
    # -------------------------------------------------
    tof_1d = corrected.get("tof_1d", [])
    if isinstance(tof_1d, list) and tof_1d:
        new_tof_1d = []
        for idx, value in enumerate(tof_1d):
            if idx < len(TOF_1D_ORDER):
                key = TOF_1D_ORDER[idx]
                factor = TOF_1D_FACTORS.get(key, 1.0)
            else:
                factor = 1.0
            new_tof_1d.append(_safe_apply_factor(value, factor))
        corrected["tof_1d"] = new_tof_1d

    # -------------------------------------------------
    # 3D ToF factor 적용
    # 앞 16개 = left_sensor, 뒤 16개 = right_sensor 로 가정
    # -------------------------------------------------
    tof_3d = corrected.get("tof_3d", [])
    if isinstance(tof_3d, list) and tof_3d:
        left_factor = TOF_3D_FACTORS.get("left_sensor", 1.0)
        right_factor = TOF_3D_FACTORS.get("right_sensor", 1.0)

        new_tof_3d = []
        for idx, value in enumerate(tof_3d):
            factor = left_factor if idx < 16 else right_factor
            new_tof_3d.append(_safe_apply_factor(value, factor))
        corrected["tof_3d"] = new_tof_3d

    return corrected