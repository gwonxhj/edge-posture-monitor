import json
import os
from datetime import datetime


class ProfileManager:
    def __init__(self, profile_dir="profiles"):
        self.profile_dir = profile_dir
        os.makedirs(self.profile_dir, exist_ok=True)

    def _profile_path(self, user_id: str):
        return os.path.join(self.profile_dir, f"{user_id}.json")

    def user_exists(self, user_id: str) -> bool:
        return os.path.exists(self._profile_path(user_id))

    def create_profile(
        self,
        user_id: str,
        name: str,
        height_cm: float,
        weight_kg: float,
        rest_work_min: int = 60,
        rest_break_min: int = 10,
        mode: str = "pc",
        sensitivity: str = "normal",
    ):
        profile = {
            "user_id": user_id,
            "name": name,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "rest_work_min": rest_work_min,
            "rest_break_min": rest_break_min,
            "mode": mode,
            "sensitivity": sensitivity,
            "baseline": None,
            "last_calibrated_at": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self.save_profile(profile)
        return profile

    def load_profile(self, user_id: str):
        path = self._profile_path(user_id)
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        return profile

    def save_profile(self, profile: dict):
        profile["updated_at"] = datetime.now().isoformat()
        path = self._profile_path(profile["user_id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def update_baseline(self, user_id: str, baseline: dict):
        profile = self.load_profile(user_id)
        if profile is None:
            raise ValueError(f"Profile not found: {user_id}")

        profile["baseline"] = baseline
        profile["last_calibrated_at"] = datetime.now().isoformat()
        self.save_profile(profile)
        return profile

    def update_settings(
        self,
        user_id: str,
        height_cm=None,
        weight_kg=None,
        rest_work_min=None,
        rest_break_min=None,
        mode=None,
        sensitivity=None,
    ):
        profile = self.load_profile(user_id)
        if profile is None:
            raise ValueError(f"Profile not found: {user_id}")

        if height_cm is not None:
            profile["height_cm"] = height_cm
        if weight_kg is not None:
            profile["weight_kg"] = weight_kg
        if rest_work_min is not None:
            profile["rest_work_min"] = rest_work_min
        if rest_break_min is not None:
            profile["rest_break_min"] = rest_break_min
        if mode is not None:
            profile["mode"] = mode
        if sensitivity is not None:
            profile["sensitivity"] = sensitivity

        self.save_profile(profile)
        return profile

    def has_baseline(self, user_id: str) -> bool:
        profile = self.load_profile(user_id)
        if profile is None:
            return False
        return profile.get("baseline") is not None

    def list_profiles(self):
        profiles = []
        for filename in os.listdir(self.profile_dir):
            if filename.endswith(".json"):
                user_id = filename[:-5]
                profile = self.load_profile(user_id)
                if profile is not None:
                    profiles.append(profile)
        return profiles