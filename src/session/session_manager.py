class SessionManager:
    def __init__(self, profile_manager):
        self.profile_manager = profile_manager
        self.current_profile = None
        self.session_active = False
        self.measurement_started = False

    def select_or_create_user(
        self,
        user_id: str,
        name: str = None,
        height_cm: float = None,
        weight_kg: float = None,
        rest_work_min: int = 60,
        rest_break_min: int = 10,
        mode: str = "pc",
        sensitivity: str = "normal",
    ):
        if self.profile_manager.user_exists(user_id):
            self.current_profile = self.profile_manager.load_profile(user_id)
            is_new_user = False
        else:
            if name is None or height_cm is None or weight_kg is None:
                raise ValueError("New user requires name, height_cm, and weight_kg")

            self.current_profile = self.profile_manager.create_profile(
                user_id=user_id,
                name=name,
                height_cm=height_cm,
                weight_kg=weight_kg,
                rest_work_min=rest_work_min,
                rest_break_min=rest_break_min,
                mode=mode,
                sensitivity=sensitivity,
            )
            is_new_user = True

        has_baseline = self.current_profile.get("baseline") is not None

        return {
            "is_new_user": is_new_user,
            "has_baseline": has_baseline,
            "must_calibrate": is_new_user or (not has_baseline),
            "profile": self.current_profile,
        }

    def save_baseline_for_current_user(self, baseline: dict):
        if self.current_profile is None:
            raise ValueError("No user selected")

        user_id = self.current_profile["user_id"]
        self.current_profile = self.profile_manager.update_baseline(user_id, baseline)
        return self.current_profile

    def get_current_profile(self):
        return self.current_profile

    def get_current_baseline(self):
        if self.current_profile is None:
            return None
        return self.current_profile.get("baseline")

    def get_rest_config(self):
        if self.current_profile is None:
            return {
                "rest_work_min": 60,
                "rest_break_min": 10,
            }

        return {
            "rest_work_min": self.current_profile.get("rest_work_min", 60),
            "rest_break_min": self.current_profile.get("rest_break_min", 10),
        }

    def start_session(self):
        if self.current_profile is None:
            raise ValueError("No user selected")
        self.session_active = True
        self.measurement_started = False

    def mark_measurement_started(self):
        self.measurement_started = True

    def end_session(self):
        self.session_active = False
        self.measurement_started = False

    def is_session_active(self):
        return self.session_active

    def is_measurement_started(self):
        return self.measurement_started