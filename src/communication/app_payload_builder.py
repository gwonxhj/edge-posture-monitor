# src/communication/app_payload_builder.py

import time


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

def build_debug_sensor_payload(user_id, raw_packet, semantic_packet, feature_map, delta_map=None):
    tof_3d = raw_packet.get("tof_3d", [])
    loadcell = raw_packet.get("loadcell", [])
    mpu = raw_packet.get("mpu", [])
    delta_map = delta_map or {}

    return {
        "type": "debug_sensor",
        "user_id": user_id,
        "timestamp": int(time.time()),
        "raw": {
            "loadcell_sum": sum(loadcell),
            "tof_1d": raw_packet.get("tof_1d", []),
            "tof_3d_min": min(tof_3d) if tof_3d else 0,
            "tof_3d_max": max(tof_3d) if tof_3d else 0,
            "tof_3d_mean": round(sum(tof_3d) / len(tof_3d), 3) if tof_3d else 0.0,
            "mpu": mpu,
        },
        "semantic": {
            "pitch_fused_deg": round(semantic_packet["imu"]["pitch_fused_deg"], 3),
            "back_total": round(feature_map["back_total"], 3),
            "seat_fb_shift": round(feature_map["seat_fb_shift"], 3),
            "back_lr_diff": round(feature_map["back_lr_diff"], 3),
            "seat_lr_diff": round(feature_map["seat_lr_diff"], 3),
            "neck_mean": round(feature_map["neck_mean"], 3),
            "neck_forward_delta": round(feature_map["neck_forward_delta"], 3),
            "spine_curve": round(feature_map["spine_curve"], 3),
        },
        "delta": {
            "seat_fb_shift_delta": round(delta_map.get("seat_fb_shift_delta", 0.0), 3),
            "neck_mean_delta": round(delta_map.get("neck_mean_delta", 0.0), 3),
            "neck_forward_delta_delta": round(delta_map.get("neck_forward_delta_delta", 0.0), 3),
            "spine_curve_delta": round(delta_map.get("spine_curve_delta", 0.0), 3),
            "pitch_fused_deg_delta": round(delta_map.get("pitch_fused_deg_delta", 0.0), 3),
        },
    }