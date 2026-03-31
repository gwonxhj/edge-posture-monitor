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
    "turtle_neck": 10,
    "forward_lean": 10,
    "reclined": 15,
    "side_slouch": 8,
    "leg_cross_suspect": 15,
    "thinking_pose": 10,
    "perching": 8,
}

# 이상 자세가 유지될 때 초당 기본 차감량
POSTURE_DECAY_PER_SEC = {
    "normal": 0.0,
    "turtle_neck": 0.25,
    "forward_lean": 0.30,
    "reclined": 0.12,
    "side_slouch": 0.30,
    "leg_cross_suspect": 0.10,
    "thinking_pose": 0.15,
    "perching": 0.35,
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
            return 0.15
        if self.alert_stage == 3:
            return 0.20
        return 0.25

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

        # 0) 정자세 유지 시 점수 회복 (초당 +0.05, 최대 100)
        if posture == "normal" and self.score < 100.0:
            recovery = 0.05 * (step_samples / self.sample_rate_hz)
            self.score = min(100.0, self.score + recovery)

        # 1) 이상 자세일 때는 매 샘플마다 소량 감점
        if posture != "normal":
            per_sec = POSTURE_DECAY_PER_SEC.get(posture, 0.0)
            continuous_penalty = per_sec * (step_samples / self.sample_rate_hz)
            penalty_applied += continuous_penalty
            self.score -= continuous_penalty

            threshold_samples = int(
                POSTURE_ALERT_THRESHOLD_SEC.get(posture, 20) * self.sample_rate_hz
            )
            recheck_samples = int(10 * self.sample_rate_hz)

            # 2) 최초 임계 지속 시간 도달 시 1차 알림 + 기본 패널티
            if self.current_posture_samples >= threshold_samples and self.alert_stage == 0:
                self.alert_stage = 1
                self.last_alert_sample = self.current_posture_samples
                first_penalty = POSTURE_BASE_WEIGHT.get(posture, 0.0)
                penalty_applied += first_penalty
                self.score -= first_penalty
                alert = True

            # 3) 이후 10초마다 재알림 + 추가 패널티
            elif self.alert_stage >= 1 and (
                self.current_posture_samples - self.last_alert_sample
            ) >= recheck_samples:
                self.alert_stage += 1
                self.last_alert_sample = self.current_posture_samples
                extra = self._next_extra_penalty()
                penalty_applied += extra
                self.score -= extra
                alert = True

        if self.score < 0:
            self.score = 0.0

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
            "penalty_applied": round(penalty_applied, 3),
            "posture_duration_sec": posture_duration_sec,
            "flags": flags or {},
        }