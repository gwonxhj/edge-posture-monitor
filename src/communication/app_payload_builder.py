# src/communication/app_payload_builder.py

import time


def _clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, value))


def _level_from_percent(percent: int) -> str:
    """
    앱 색상 표시용 상태값
    - good    : 양호
    - caution : 주의
    - danger  : 위험
    """
    if percent >= 80:
        return "good"
    if percent >= 40:
        return "caution"
    return "danger"


def _safe_round(value, digits=3):
    try:
        return round(float(value), digits)
    except Exception:
        return 0.0


def _normalize_group_to_percent(values):
    """
    그룹 내부 상대값 기준 0~100 퍼센트로 정규화.
    현재는 UI 표시용 임시 정규화 방식.
    실측/보정 완료 후 절대 기준으로 교체 가능.
    """
    if not values:
        return []

    abs_values = [abs(v) for v in values]
    max_value = max(abs_values) if abs_values else 0

    if max_value <= 0:
        return [0 for _ in values]

    return [_clamp(int(round((abs(v) / max_value) * 100))) for v in values]


def _build_cell_dict(percent: int, raw_value, raw_key="raw"):
    return {
        "percent": int(_clamp(percent)),
        "level": _level_from_percent(int(_clamp(percent))),
        raw_key: raw_value,
    }


def build_realtime_payload(
    user_id,
    posture,
    flags,
    state,
    monitoring_metrics,
):
    return {
        "type": "realtime_status",
        "user_id": user_id,
        "timestamp": int(time.time()),
        "posture": {
            "dominant": posture,
            "flags": flags,
        },
        "score": {
            "current": state["score"],
            "alert": state["alert"],
            "alert_stage": state["alert_stage"],
        },
        "monitoring": monitoring_metrics,
    }


def build_minute_summary_payload(user_id, session_id, minute_data):
    return {
        "type": "minute_summary",
        "user_id": user_id,
        "session_id": session_id,
        "minute_index": minute_data["minute_index"],
        "avg_score": minute_data["avg_score"],
        "dominant_posture": minute_data["dominant_posture"],
        "dominant_posture_ratio": minute_data["dominant_posture_ratio"],
    }


def build_overall_summary_payload(user_id, session_id, summary):
    return {
        "type": "overall_summary",
        "user_id": user_id,
        "session_id": session_id,
        "avg_score": summary["avg_score"],
        "total_sitting_sec": summary["total_sitting_sec"],
        "dominant_posture": summary["dominant_posture"],
        "dominant_posture_ratio": summary["dominant_posture_ratio"],
        "posture_duration_sec": summary["posture_duration_sec"],
    }


def build_stand_event_payload(user_id):
    return {
        "type": "stand_event",
        "user_id": user_id,
        "timestamp": int(time.time()),
        "message": "사용자가 자리에서 일어났습니다. 측정을 재시작 하시겠습니까?",
        "actions": {
            "resume": "resume_after_stand",
            "stop": "decline_resume_after_stand",
        },
    }


def build_meta_payload(stage, extra=None):
    payload = {
        "type": "meta",
        "stage": stage,
        "timestamp": int(time.time()),
    }
    if extra:
        payload.update(extra)
    return payload


def build_sensor_distribution_payload(
    user_id,
    session_id,
    sample_index,
    raw_packet,
    feature_map,
    semantic_packet=None,
):
    """
    앱 대시보드용 상세 센서 분포 payload
    - spine ToF는 semantic_packet의 정제/안정화 값 우선 사용
    - head ToF는 비정상 범위값을 제외하고 요약
    """
    semantic_packet = semantic_packet or {}

    loadcell = raw_packet.get("loadcell", [])
    tof_1d = raw_packet.get("tof_1d", [])
    tof_3d = raw_packet.get("tof_3d", [])
    mpu = raw_packet.get("mpu", [])

    # -------------------------------------------------
    # Loadcell raw unpack
    # -------------------------------------------------
    back_right = loadcell[0:4] if len(loadcell) >= 4 else [0, 0, 0, 0]
    back_left = loadcell[4:8] if len(loadcell) >= 8 else [0, 0, 0, 0]
    seat_raw = loadcell[8:12] if len(loadcell) >= 12 else [0, 0, 0, 0]

    back_ui_values = [
        back_left[0],
        back_left[1],
        back_left[2],
        back_left[3],
        back_right[0],
        back_right[1],
        back_right[2],
        back_right[3],
    ]
    back_ui_percents = _normalize_group_to_percent(back_ui_values)

    seat_rear_right = seat_raw[0] if len(seat_raw) > 0 else 0
    seat_front_right = seat_raw[1] if len(seat_raw) > 1 else 0
    seat_rear_left = seat_raw[2] if len(seat_raw) > 2 else 0
    seat_front_left = seat_raw[3] if len(seat_raw) > 3 else 0

    seat_ui_values = [
        seat_rear_left,
        seat_rear_right,
        seat_front_left,
        seat_front_right,
    ]
    seat_ui_percents = _normalize_group_to_percent(seat_ui_values)

    # -------------------------------------------------
    # ToF
    # -------------------------------------------------
    def tof_mm_to_percent(mm_value):
        try:
            mm = float(mm_value)
        except Exception:
            return 0

        percent = int(round((1000.0 - max(0.0, min(mm, 1000.0))) / 10.0))
        return _clamp(percent)

    # spine는 semantic_packet의 안정화 값 우선 사용
    spine_sem = semantic_packet.get("tof", {}).get("spine", {})

    spine_upper = spine_sem.get(
        "upper",
        tof_1d[0] if len(tof_1d) > 0 else 0,
    )
    spine_upper_mid = spine_sem.get(
        "upper_mid",
        tof_1d[1] if len(tof_1d) > 1 else 0,
    )
    spine_lower_mid = spine_sem.get(
        "lower_mid",
        tof_1d[2] if len(tof_1d) > 2 else 0,
    )
    spine_lower = spine_sem.get(
        "lower",
        tof_1d[3] if len(tof_1d) > 3 else 0,
    )

    spine_percents = [
        tof_mm_to_percent(spine_upper),
        tof_mm_to_percent(spine_upper_mid),
        tof_mm_to_percent(spine_lower_mid),
        tof_mm_to_percent(spine_lower),
    ]

    # head 3D ToF는 비정상값 제거
    def _valid_head_values(arr):
        out = []
        for v in arr:
            try:
                fv = float(v)
            except Exception:
                continue
            if 80 <= fv <= 1200:
                out.append(fv)
        return out

    left_tof3d_raw = tof_3d[:16] if len(tof_3d) >= 16 else tof_3d[:]
    right_tof3d_raw = tof_3d[16:32] if len(tof_3d) >= 32 else []

    left_tof3d = _valid_head_values(left_tof3d_raw)
    right_tof3d = _valid_head_values(right_tof3d_raw)
    all_tof3d = left_tof3d + right_tof3d

    def safe_min(arr):
        return min(arr) if arr else 0

    def safe_max(arr):
        return max(arr) if arr else 0

    def safe_mean(arr):
        return round(sum(arr) / len(arr), 3) if arr else 0.0

    head_overall_percent = tof_mm_to_percent(safe_min(all_tof3d))

    # -------------------------------------------------
    # IMU
    # -------------------------------------------------
    pitch_right = float(mpu[0]) if len(mpu) > 0 else 0.0
    pitch_left = float(mpu[1]) if len(mpu) > 1 else 0.0
    pitch_fused_deg = semantic_packet.get(
        "imu", {}
    ).get("pitch_fused_deg", feature_map.get("pitch_fused_deg", 0.0))

    # -------------------------------------------------
    # Summary
    # -------------------------------------------------
    back_left_total_percent = int(round(sum(back_ui_percents[:4]) / 4)) if back_ui_percents else 0
    back_right_total_percent = int(round(sum(back_ui_percents[4:]) / 4)) if back_ui_percents else 0

    seat_rear_total_percent = int(round(sum(seat_ui_percents[:2]) / 2)) if seat_ui_percents else 0
    seat_front_total_percent = int(round(sum(seat_ui_percents[2:]) / 2)) if seat_ui_percents else 0
    seat_left_total_percent = int(round((seat_ui_percents[0] + seat_ui_percents[2]) / 2)) if len(seat_ui_percents) == 4 else 0
    seat_right_total_percent = int(round((seat_ui_percents[1] + seat_ui_percents[3]) / 2)) if len(seat_ui_percents) == 4 else 0

    back_balance_percent = _clamp(
        100 - int(round(abs(back_left_total_percent - back_right_total_percent)))
    )
    seat_balance_percent = _clamp(
        100 - int(round(abs(seat_left_total_percent - seat_right_total_percent)))
    )

    return {
        "type": "sensor_distribution",
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": int(time.time()),
        "frame_index": sample_index,

        "back_pressure": {
            "left_top": _build_cell_dict(back_ui_percents[0], back_ui_values[0]),
            "left_upper_mid": _build_cell_dict(back_ui_percents[1], back_ui_values[1]),
            "left_lower_mid": _build_cell_dict(back_ui_percents[2], back_ui_values[2]),
            "left_bottom": _build_cell_dict(back_ui_percents[3], back_ui_values[3]),
            "right_top": _build_cell_dict(back_ui_percents[4], back_ui_values[4]),
            "right_upper_mid": _build_cell_dict(back_ui_percents[5], back_ui_values[5]),
            "right_lower_mid": _build_cell_dict(back_ui_percents[6], back_ui_values[6]),
            "right_bottom": _build_cell_dict(back_ui_percents[7], back_ui_values[7]),
            "summary": {
                "left_total_percent": back_left_total_percent,
                "right_total_percent": back_right_total_percent,
                "balance_percent": back_balance_percent,
            },
        },

        "seat_pressure": {
            "rear_left": _build_cell_dict(seat_ui_percents[0], seat_ui_values[0]),
            "rear_right": _build_cell_dict(seat_ui_percents[1], seat_ui_values[1]),
            "front_left": _build_cell_dict(seat_ui_percents[2], seat_ui_values[2]),
            "front_right": _build_cell_dict(seat_ui_percents[3], seat_ui_values[3]),
            "summary": {
                "rear_total_percent": seat_rear_total_percent,
                "front_total_percent": seat_front_total_percent,
                "left_total_percent": seat_left_total_percent,
                "right_total_percent": seat_right_total_percent,
                "balance_percent": seat_balance_percent,
                "center_shift": {
                    "fb": _safe_round(feature_map.get("seat_fb_shift", 0.0), 3),
                    "lr": _safe_round(feature_map.get("seat_lr_diff", 0.0), 3),
                },
            },
        },

        "spine_tof": {
            "upper": _build_cell_dict(spine_percents[0], spine_upper, raw_key="raw_mm"),
            "upper_mid": _build_cell_dict(spine_percents[1], spine_upper_mid, raw_key="raw_mm"),
            "lower_mid": _build_cell_dict(spine_percents[2], spine_lower_mid, raw_key="raw_mm"),
            "lower": _build_cell_dict(spine_percents[3], spine_lower, raw_key="raw_mm"),
            "summary": {
                "overall_percent": int(round(sum(spine_percents) / 4)) if spine_percents else 0,
                "curve_score": _safe_round(feature_map.get("spine_curve", 0.0), 3),
            },
        },

        "head_tof": {
            "overall": {
                "percent": int(head_overall_percent),
                "level": _level_from_percent(int(head_overall_percent)),
            },
            "left_sensor": {
                "min_mm": safe_min(left_tof3d),
                "max_mm": safe_max(left_tof3d),
                "mean_mm": safe_mean(left_tof3d),
            },
            "right_sensor": {
                "min_mm": safe_min(right_tof3d),
                "max_mm": safe_max(right_tof3d),
                "mean_mm": safe_mean(right_tof3d),
            },
        },

        "imu": {
            "pitch_left_deg": _safe_round(pitch_left, 3),
            "pitch_right_deg": _safe_round(pitch_right, 3),
            "pitch_fused_deg": _safe_round(pitch_fused_deg, 3),
            "pitch_lr_diff_deg": _safe_round(abs(pitch_left - pitch_right), 3),
        },
    }