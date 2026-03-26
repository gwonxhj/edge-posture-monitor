import time
import gpiod

from src.config.settings import (
    BUZZER_ENABLE,
    BUZZER_INITIAL_DELAY_SEC,
    BUZZER_STAGE1_INTERVAL,
    BUZZER_STAGE2_INTERVAL,
    BUZZER_STAGE3_INTERVAL,
    BUZZER_MULTI_POSTURE_FACTOR,
    BUZZER_WEIGHT_MAP,
)

BUZZER_CHIP = "/dev/gpiochip0"
BUZZER_LINE_OFFSET = 18


class BuzzerFeedback:
    def __init__(self):
        self.current_postures = set()
        self.first_detect_time = None
        self.last_beep_time = 0
        self.stage = 0

        self.chip = gpiod.Chip(BUZZER_CHIP)
        self.line = self.chip.get_line(BUZZER_LINE_OFFSET)
        self.line.request(
            consumer="posture-buzzer",
            type=gpiod.LINE_REQ_DIR_OUT,
            default_vals=[0],
        )

    def reset(self):
        self.current_postures = set()
        self.first_detect_time = None
        self.last_beep_time = 0
        self.stage = 0
        self._off()

    def close(self):
        try:
            self._off()
            self.line.release()
        except Exception:
            pass
        try:
            self.chip.close()
        except Exception:
            pass

    def _on(self):
        self.line.set_value(1)

    def _off(self):
        self.line.set_value(0)

    def _calc_interval(self, postures):
        if not postures:
            return None

        weight = max([BUZZER_WEIGHT_MAP.get(p, 1.0) for p in postures])

        if self.stage == 1:
            base = BUZZER_STAGE1_INTERVAL
        elif self.stage == 2:
            base = BUZZER_STAGE2_INTERVAL
        else:
            base = BUZZER_STAGE3_INTERVAL

        count_factor = 1 + (len(postures) - 1) * BUZZER_MULTI_POSTURE_FACTOR
        return base / (weight * count_factor)

    def _update_stage(self, elapsed):
        if elapsed >= 15:
            self.stage = 3
        elif elapsed >= 10:
            self.stage = 2
        elif elapsed >= BUZZER_INITIAL_DELAY_SEC:
            self.stage = 1
        else:
            self.stage = 0

    def update(self, active_postures: set):
        if not BUZZER_ENABLE:
            return

        now = time.time()

        if not active_postures:
            self.reset()
            return

        if active_postures != self.current_postures:
            print(f"[BUZZER] posture changed -> reset | {active_postures}")
            self.current_postures = active_postures.copy()
            self.first_detect_time = now
            self.stage = 0
            self.last_beep_time = 0
            self._off()
            return

        if self.first_detect_time is None:
            self.first_detect_time = now
            return

        elapsed = now - self.first_detect_time
        self._update_stage(elapsed)

        if self.stage == 0:
            self._off()
            return

        interval = self._calc_interval(active_postures)
        if interval is None:
            return

        if now - self.last_beep_time >= interval:
            self.last_beep_time = now
            self._beep()

    def _beep(self):
        print(f"[BUZZER] stage={self.stage}")

        if self.stage == 1:
            self._on()
            time.sleep(0.08)
            self._off()

        elif self.stage == 2:
            self._on()
            time.sleep(0.06)
            self._off()
            time.sleep(0.04)
            self._on()
            time.sleep(0.06)
            self._off()

        else:
            self._on()
            time.sleep(0.4)
            self._off()