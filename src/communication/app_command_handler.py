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
    "debug_send_chk_sit": [
        S.UART_LINK_READY,
        S.PROFILE_LOADED,
        S.WAIT_START_DECISION,
        S.MEASURING,
        S.PAUSED,
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
        S.PAUSED,
        S.WAIT_START_DECISION,
        S.CALIBRATION_COMPLETED,
        S.WAIT_RESTART_DECISION,
    ],
    "request_recalibration": [
        S.PROFILE_LOADED,
        S.WAIT_CALIBRATION_DECISION,
        S.CALIBRATION_COMPLETED,
        S.WAIT_START_DECISION,
        S.SESSION_SAVED,
        S.MEASURING,
        S.PAUSED,
    ],
    "resume_measurement": [
        S.PAUSED,
    ],
}


def handle_app_command(cmd: dict, session_manager, db_manager, app_server, sender):
    """
    앱에서 온 command 처리
    """
    print("[CMD HANDLER] incoming cmd:", cmd)

    if not cmd or "cmd" not in cmd:
        print("[CMD HANDLER] invalid command payload")
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

    print(
        "[CMD HANDLER] stage check | "
        f"command={command} | current_stage={current_stage} | allowed={allowed_stages}"
    )

    if allowed_stages is not None and current_stage not in allowed_stages:
        print(
            "[CMD HANDLER] rejected | "
            f"command={command} | reason=invalid_stage | current_stage={current_stage}"
        )
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
                print(f"[CMD HANDLER] submit_profile missing field: {key}")
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

        print(
            "[CMD HANDLER] profile loaded | "
            f"user_id={profile_info['profile']['user_id']} | mode=new"
        )

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
            print("[CMD HANDLER] select_profile missing user_id")
            return {
                "action": "error",
                "message": "missing_field:user_id",
            }

        user_id = cmd["user_id"]

        if not session_manager.profile_manager.user_exists(user_id):
            print(f"[CMD HANDLER] select_profile failed | profile_not_found | user_id={user_id}")
            return {
                "action": "error",
                "message": "profile_not_found",
            }

        profile_info = session_manager.select_or_create_user(user_id=user_id)
        profile = profile_info["profile"]

        db_manager.upsert_user(
            user_id=profile["user_id"],
            name=profile["name"],
            height_cm=profile["height_cm"],
            weight_kg=profile["weight_kg"],
            rest_work_min=profile["rest_work_min"],
            rest_break_min=profile["rest_break_min"],
            sensitivity=profile.get("sensitivity", "normal"),
        )

        app_server.update_meta({
            "stage": S.PROFILE_LOADED,
            "user_id": profile["user_id"],
            "user_name": profile["name"],
        })

        print(
            "[CMD HANDLER] profile loaded | "
            f"user_id={profile['user_id']} | mode=existing"
        )

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
            print("[CMD HANDLER] start_calibration failed | no_profile_selected")
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_CALIBRATION,
            "calibration_reason": "initial",
        })

        print("[CMD HANDLER] action=start_calibration")
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
            print("[CMD HANDLER] skip_calibration failed | no_profile_selected")
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        baseline = session_manager.get_current_baseline()
        if baseline is None:
            print("[CMD HANDLER] skip_calibration failed | baseline_required")
            return {
                "action": "error",
                "message": "baseline_required",
            }

        app_server.update_meta({
            "stage": S.WAIT_START_DECISION,
        })

        print("[CMD HANDLER] action=skip_calibration")
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
            print("[CMD HANDLER] start_measurement failed | no_profile_selected")
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        baseline = session_manager.get_current_baseline()
        if baseline is None:
            print("[CMD HANDLER] start_measurement failed | baseline_required")
            return {
                "action": "error",
                "message": "baseline_required",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_MEASURE,
        })

        print("[CMD HANDLER] action=start_measurement")
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

        print("[CMD HANDLER] action=pause_measurement")
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

        print("[CMD HANDLER] action=quit_measurement")
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

        print("[CMD HANDLER] action=resume_measurement")
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
            print("[CMD HANDLER] request_recalibration failed | no_profile_selected")
            return {
                "action": "error",
                "message": "no_profile_selected",
            }

        app_server.update_meta({
            "stage": S.WAIT_SIT_FOR_CALIBRATION,
            "calibration_reason": "recalibration",
        })

        print("[CMD HANDLER] action=request_recalibration")
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

        print("[CMD HANDLER] action=resume_after_stand")
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

        print("[CMD HANDLER] action=decline_resume_after_stand")
        return {
            "action": "decline_resume_after_stand",
            "message": "resume_declined",
        }

    # -------------------------------------------------
    # DEBUG: CHK_SIT 직접 전송
    # -------------------------------------------------
    elif command == "debug_send_chk_sit":
        print("[CMD HANDLER] action=debug_send_chk_sit -> UART TX 예정")
        sender.send_check_sit()
        return {
            "action": "debug_send_chk_sit",
            "message": "CHK_SIT sent",
        }

    print(f"[CMD HANDLER] unknown_command={command}")
    return {
        "action": "noop",
        "message": f"unknown_command:{command}",
    }