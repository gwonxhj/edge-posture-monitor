# src/communication/app_command_handler.py

from src.communication import session_state as S

# -------------------------------------------------
# command 허용 stage 정의
# -------------------------------------------------
ALLOWED_STAGE_BY_COMMAND = {
    "submit_profile": [
        S.UART_LINK_READY,
        S.PROFILE_LOADED,
    ],
    "select_profile": [
        S.UART_LINK_READY,
        S.PROFILE_LOADED,
    ],
    "start_calibration": [
        S.PROFILE_LOADED,
        S.WAIT_CALIBRATION_DECISION,
        S.CALIBRATION_COMPLETED,
    ],
    "skip_calibration": [
        S.PROFILE_LOADED,
        S.WAIT_CALIBRATION_DECISION,
    ],
    "start_measurement": [
        S.CALIBRATION_COMPLETED,
        S.WAIT_START_DECISION,
    ],
    "resume_after_stand": [
        S.WAIT_RESTART_DECISION,
    ],
    "decline_resume_after_stand": [
        S.WAIT_RESTART_DECISION,
    ],
    "pause_measurement": [
        S.MEASURING,
    ],
    "quit_measurement": [
        S.MEASURING,
        S.WAIT_START_DECISION,
        S.CALIBRATION_COMPLETED,
        S.WAIT_RESTART_DECISION,
    ],
    "request_recalibration": [
        S.PROFILE_LOADED,
        S.WAIT_CALIBRATION_DECISION,
        S.CALIBRATION_COMPLETED,
        S.SESSION_SAVED,
    ],
    "resume_measurement": [
        S.PAUSED,
    ],
}


def handle_app_command(cmd: dict, session_manager, db_manager, app_server):
    """
    앱에서 온 command 처리

    반환 예시:
    {
        "action": "profile_loaded",
        "message": "existing_profile_loaded",
        "profile_info": {...}
    }
    """

    if not cmd or "cmd" not in cmd:
        return {
            "action": "noop",
            "message": "invalid_command",
        }

    command = cmd["cmd"]

    # -------------------------------------------------
    # stage validation
    # -------------------------------------------------
    current_stage = app_server.latest_meta_payload.get("stage")

    allowed_stages = ALLOWED_STAGE_BY_COMMAND.get(command)

    if allowed_stages is not None and current_stage not in allowed_stages:
        return {
            "action": "error",
            "message": "invalid_stage",
            "cmd": command,
            "stage": current_stage,
            "allowed_stages": allowed_stages,
        }

    # -------------------------------------------------
    # 신규 프로필 등록
    # -------------------------------------------------
    if command == "submit_profile":
        required_keys = [
            "user_id",
            "name",
            "height_cm",
            "weight_kg",
            "rest_work_min",
            "rest_break_min",
        ]

        for key in required_keys:
            if key not in cmd:
                return {
                    "action": "error",
                    "message": f"missing_field:{key}",
                }

        user_id = cmd["user_id"]
        name = cmd["name"]
        height_cm = cmd["height_cm"]
        weight_kg = cmd["weight_kg"]
        rest_work_min = cmd["rest_work_min"]
        rest_break_min = cmd["rest_break_min"]

        db_manager.upsert_user(
            user_id=user_id,
            name=name,
            height_cm=height_cm,
            weight_kg=weight_kg,
            rest_work_min=rest_work_min,
            rest_break_min=rest_break_min,
            sensitivity="normal",
        )

        profile_info = session_manager.select_or_create_user(
            user_id=user_id,
            name=name,
            height_cm=height_cm,
            weight_kg=weight_kg,
            rest_work_min=rest_work_min,
            rest_break_min=rest_break_min,
            sensitivity="normal",
        )

        app_server.update_meta({
            "stage": S.PROFILE_LOADED,
            "user_id": profile_info["profile"]["user_id"],
            "user_name": profile_info["profile"]["name"],
        })

        return {
            "action": "profile_loaded",
            "message": "new_profile_registered",
            "profile_info": profile_info,
        }

    # -------------------------------------------------
    # 기존 프로필 선택
    # -------------------------------------------------
    elif command == "select_profile":
        if "user_id" not in cmd:
            return {
                "action": "error",
                "message": "missing_field:user_id",
            }

        user_id = cmd["user_id"]

        if not session_manager.profile_manager.user_exists(user_id):
            return {
                "action": "error",
                "message": "profile_not_found",
            }

        profile_info = session_manager.select_or_create_user(user_id=user_id)

        app_server.update_meta({
            "stage": S.PROFILE_LOADED,
            "user_id": profile_info["profile"]["user_id"],
            "user_name": profile_info["profile"]["name"],
        })

        return {
            "action": "profile_loaded",
            "message": "existing_profile_loaded",
            "profile_info": profile_info,
        }

    # -------------------------------------------------
    # 캘리브레이션 시작 요청
    # -------------------------------------------------
    elif command == "start_calibration":
        current_profile = session_manager.get_current_profile()
        if current_profile is None:
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_CALIBRATION,
        })

        return {
            "action": "start_calibration",
            "message": "calibration_requested",
        }

    # -------------------------------------------------
    # 캘리브레이션 생략
    # -------------------------------------------------
    elif command == "skip_calibration":
        current_profile = session_manager.get_current_profile()
        if current_profile is None:
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        baseline = session_manager.get_current_baseline()
        if baseline is None:
            return {
                "action": "error",
                "message": "baseline_required",
            }

        app_server.update_meta({
            "stage": S.WAIT_START_DECISION,
        })

        return {
            "action": "skip_calibration",
            "message": "calibration_skipped",
        }

    # -------------------------------------------------
    # 측정 시작 요청
    # -------------------------------------------------
    elif command == "start_measurement":
        current_profile = session_manager.get_current_profile()
        if current_profile is None:
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        baseline = session_manager.get_current_baseline()
        if baseline is None:
            return {
                "action": "error",
                "message": "baseline_required",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_MEASURE,
        })

        return {
            "action": "start_measurement",
            "message": "measurement_requested",
        }

    # -------------------------------------------------
    # 측정 일시정지 요청
    # -------------------------------------------------
    elif command == "pause_measurement":
        app_server.update_meta({
            "stage": S.MEASUREMENT_STOP_REQUESTED,
        })

        return {
            "action": "pause_measurement",
            "message": "measurement_pause_requested",
        }

    # -------------------------------------------------
    # 측정 완전 종료 요청
    # -------------------------------------------------
    elif command == "quit_measurement":
        app_server.update_meta({
            "stage": S.MEASUREMENT_STOP_REQUESTED,
        })

        return {
            "action": "quit_measurement",
            "message": "measurement_quit_requested",
        }
    
    # -------------------------------------------------
    # 측정 재개 요청
    # -------------------------------------------------
    elif command == "resume_measurement":
        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_MEASURE,
        })

        return {
            "action": "resume_measurement",
            "message": "measurement_resume_requested",
        }

    # -------------------------------------------------
    # 재캘리브레이션 요청
    # -------------------------------------------------
    elif command == "request_recalibration":
        current_profile = session_manager.get_current_profile()
        if current_profile is None:
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_CALIBRATION,
        })

        return {
            "action": "start_calibration",
            "message": "recalibration_requested",
        }

    # -------------------------------------------------
    # STAND 이후 재시작 yes
    # -------------------------------------------------
    elif command == "resume_after_stand":
        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_MEASURE,
        })

        return {
            "action": "resume_after_stand",
            "message": "resume_requested",
        }

    # -------------------------------------------------
    # STAND 이후 재시작 no
    # -------------------------------------------------
    elif command == "decline_resume_after_stand":
        app_server.update_meta({
            "stage": S.MEASUREMENT_STOP_REQUESTED,
        })

        return {
            "action": "decline_resume_after_stand",
            "message": "resume_declined",
        }

    return {
        "action": "noop",
        "message": f"unknown_command:{command}",
    }