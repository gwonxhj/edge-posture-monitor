import time
from src.core.posture_types import POSTURE_WEIGHT


class AlertManager:

    def __init__(self):

        self.current_posture = None
        self.start_time = None

        self.alert_stage = 0
        self.last_alert_time = None

        self.score = 100

    def update(self, posture):

        now = time.time()

        if posture != self.current_posture:

            self.current_posture = posture
            self.start_time = now
            self.alert_stage = 0

            return False

        duration = now - self.start_time

        threshold = self.get_threshold(posture)

        if duration > threshold:

            if self.alert_stage == 0:

                self.alert_stage = 1
                self.last_alert_time = now
                return True

            elif now - self.last_alert_time > 10:

                self.alert_stage += 1
                self.last_alert_time = now

                penalty = POSTURE_WEIGHT.get(posture, 0) + 0.1

                self.score -= penalty

                return True

        return False

    def get_threshold(self, posture):

        table = {
            "turtle_neck": 20,
            "forward_lean": 20,
            "side_slouch": 15,
            "leg_cross_suspect": 30,
            "reclined": 30,
            "thinking_pose": 15
        }

        return table.get(posture, 20)