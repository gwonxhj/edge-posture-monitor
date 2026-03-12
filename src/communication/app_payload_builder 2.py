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