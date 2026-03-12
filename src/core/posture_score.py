POSTURE_BASE_WEIGHT = {
    "normal": 0.0,
    "turtle_neck": 0.2,
    "forward_lean": 0.2,
    "reclined": 0.1,
    "side_slouch": 0.3,
    "leg_cross_suspect": 0.1,
    "thinking_pose": 0.2,
    "perching": 0.3,
}

POSTURE_ALERT_THRESHOLD_SEC = {
    "turtle_neck": 20,
    "forward_lean": 20,
    "reclined": 30,
    "side_slouch": 15,
    "leg_cross_suspect": 30,
    "thinking_pose": 15,
    "perching": 12,
}


class PostureScoreEngine:
    def __init__(self, sample_rate_hz=50):
        self.sample_rate_hz = sample_rate_hz

        self.score = 100.0

        self.current_posture = None
        self.current_posture_samples = 0

        self.total_sitting_samples = 0

        self.posture_duration_samples = {
            "normal": 0,
            "turtle_neck": 0,
            "forward_lean": 0,
            "reclined": 0,
            "side_slouch": 0,
            "leg_cross_suspect": 0,
            "thinking_pose": 0,
            "perching": 0,
        }

        self.alert_stage = 0
        self.last_alert_sample = 0

    def _samples_to_sec(self, samples):
        return samples / self.sample_rate_hz

    def _next_extra_penalty(self):
        if self.alert_stage <= 1:
            return 0.0
        if self.alert_stage == 2:
            return 0.1
        if self.alert_stage == 3:
            return 0.1
        return 0.2

    def update(self, posture, flags=None, step_samples=1):
        self.total_sitting_samples += step_samples

        if posture not in self.posture_duration_samples:
            self.posture_duration_samples[posture] = 0

        self.posture_duration_samples[posture] += step_samples

        if posture == self.current_posture:
            self.current_posture_samples += step_samples
        else:
            self.current_posture = posture
            self.current_posture_samples = step_samples
            self.alert_stage = 0
            self.last_alert_sample = 0

        alert = False
        penalty_applied = 0.0

        if posture != "normal":
            threshold_samples = int(
                POSTURE_ALERT_THRESHOLD_SEC.get(posture, 20) * self.sample_rate_hz
            )

            recheck_samples = int(10 * self.sample_rate_hz)

            if self.current_posture_samples >= threshold_samples and self.alert_stage == 0:
                # 1차 알림
                self.alert_stage = 1
                self.last_alert_sample = self.current_posture_samples
                alert = True

            elif self.alert_stage >= 1 and \
                 (self.current_posture_samples - self.last_alert_sample) >= recheck_samples:
                # 미개선 재알림 + penalty 증가
                self.alert_stage += 1
                self.last_alert_sample = self.current_posture_samples
                extra = self._next_extra_penalty()
                penalty_applied = POSTURE_BASE_WEIGHT.get(posture, 0.0) + extra
                self.score -= penalty_applied
                if self.score < 0:
                    self.score = 0.0
                alert = True

        posture_duration_sec = {
            k: self._samples_to_sec(v)
            for k, v in self.posture_duration_samples.items()
        }

        return {
            "score": round(self.score, 2),
            "current_posture": self.current_posture,
            "current_duration_sec": round(self._samples_to_sec(self.current_posture_samples), 2),
            "total_sitting_sec": round(self._samples_to_sec(self.total_sitting_samples), 2),
            "alert": alert,
            "alert_stage": self.alert_stage,
            "penalty_applied": round(penalty_applied, 2),
            "posture_duration_sec": posture_duration_sec,
            "flags": flags or {},
        }