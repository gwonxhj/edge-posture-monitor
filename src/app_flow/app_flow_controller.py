from src.communication import session_state as S
from src.communication.app_command_handler import handle_app_command


def wait_for_app_profile_command(app_server, session_manager, db_manager, sender):
    print("[APP] profile command 대기 중...")

    while True:
        cmd = app_server.get_next_command()
        if cmd is None:
            continue

        result = handle_app_command(
            cmd=cmd,
            session_manager=session_manager,
            db_manager=db_manager,
            app_server=app_server,
            sender=sender,
        )

        if result["action"] == "profile_loaded":
            return result["profile_info"]

        print("[APP CMD RESULT]", result)


def wait_for_calibration_decision(app_server, session_manager, db_manager, sender):
    app_server.update_meta({
        "stage": S.WAIT_CALIBRATION_DECISION,
    })
    print("[APP] 캘리브레이션 결정 command 대기 중...")

    while True:
        cmd = app_server.get_next_command()
        if cmd is None:
            continue

        result = handle_app_command(
            cmd=cmd,
            session_manager=session_manager,
            db_manager=db_manager,
            app_server=app_server,
            sender=sender,
        )
        print("[APP CMD RESULT]", result)

        if result["action"] == "start_calibration":
            return "start_calibration"

        if result["action"] == "skip_calibration":
            return "skip_calibration"


def wait_for_start_measurement_command(app_server, session_manager, db_manager, sender):
    app_server.update_meta({
        "stage": S.WAIT_START_DECISION,
    })
    print("[APP] 측정 시작 command 대기 중...")

    while True:
        cmd = app_server.get_next_command()
        if cmd is None:
            continue

        result = handle_app_command(
            cmd=cmd,
            session_manager=session_manager,
            db_manager=db_manager,
            app_server=app_server,
            sender=sender,
        )
        print("[APP CMD RESULT]", result)

        if result["action"] == "start_measurement":
            return "start"

        if result["action"] == "quit_measurement":
            return "cancel"


def wait_for_restart_decision(app_server, session_manager, db_manager, sender):
    app_server.update_meta({
        "stage": S.WAIT_RESTART_DECISION,
    })
    print("[APP] STAND 이후 재시작 결정 command 대기 중...")

    while True:
        cmd = app_server.get_next_command()
        if cmd is None:
            continue

        result = handle_app_command(
            cmd=cmd,
            session_manager=session_manager,
            db_manager=db_manager,
            app_server=app_server,
            sender=sender,
        )
        print("[APP CMD RESULT]", result)

        if result["action"] == "resume_after_stand":
            return "resume_after_stand"

        if result["action"] == "decline_resume_after_stand":
            return "decline_resume_after_stand"

        if result["action"] == "quit_measurement":
            return "quit_measurement"
        
def wait_for_resume_or_quit_command(app_server, session_manager, db_manager, sender):
    app_server.update_meta({
        "stage": S.PAUSED,
    })
    print("[APP] 일시정지 상태, 재개/종료/재캘리브레이션 command 대기 중...")

    while True:
        cmd = app_server.get_next_command()
        if cmd is None:
            continue

        result = handle_app_command(
            cmd=cmd,
            session_manager=session_manager,
            db_manager=db_manager,
            app_server=app_server,
            sender=sender,
        )
        print("[APP CMD RESULT]", result)

        if result["action"] == "resume_measurement":
            return "resume"

        if result["action"] == "quit_measurement":
            return "quit"
        
        if result["action"] == "start_calibration":
            return "recalibration"