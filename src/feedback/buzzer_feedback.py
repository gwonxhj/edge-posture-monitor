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

CHIP_PATH = "/dev/gpiochip0"
LINE_OFFSET = 18


class BuzzerFeedback:
    def __init__(self):
        self.current_postures = set()
        self.first_detect_time = None
        self.last_beep_time = 0.0
        self.stage = 0

        self.chip = gpiod.Chip(CHIP_PATH)

        line_settings = gpiod.LineSettings()
        line_settings.direction = gpiod.line.Direction.OUTPUT

        self.request = self.chip.request_lines(
            consumer="posture-buzzer",
            config={LINE_OFFSET: line_settings},
        )

        self._off()

    def reset(self):
        self.current_postures = set()
        self.first_detect_time = None
        self.last_beep_time = 0.0
        self.stage = 0
        self._off()

    def close(self):
        try:
            self._off()
        except Exception:
            pass

        try:
            self.request.release()
        except Exception:
            pass

        try:
            self.chip.close()
        except Exception:
            pass

    def _on(self):
        self.request.set_value(LINE_OFFSET, gpiod.line.Value.ACTIVE)

    def _off(self):
        self.request.set_value(LINE_OFFSET, gpiod.line.Value.INACTIVE)

    def _calc_interval(self, postures: set[str]):
        if not postures:
            return None

        weight = max(BUZZER_WEIGHT_MAP.get(p, 1.0) for p in postures)

        if self.stage == 1:
            base = BUZZER_STAGE1_INTERVAL
        elif self.stage == 2:
            base = BUZZER_STAGE2_INTERVAL
        else:
            base = BUZZER_STAGE3_INTERVAL

        count_factor = 1 + (len(postures) - 1) * BUZZER_MULTI_POSTURE_FACTOR
        return base / (weight * count_factor)

    def _update_stage(self, elapsed_sec: float):
        if elapsed_sec >= 15:
            self.stage = 3
        elif elapsed_sec >= 10:
            self.stage = 2
        elif elapsed_sec >= BUZZER_INITIAL_DELAY_SEC:
            self.stage = 1
        else:
            self.stage = 0

    def update(self, active_postures: set[str]):
        if not BUZZER_ENABLE:
            return

        now = time.time()

        # 정상 자세면 즉시 리셋
        if not active_postures:
            self.reset()
            return

        # 이상 자세 종류가 바뀌면 카운터 리셋
        if active_postures != self.current_postures:
            print(f"[BUZZER] posture changed -> reset | {sorted(active_postures)}")
            self.current_postures = set(active_postures)
            self.first_detect_time = now
            self.last_beep_time = 0.0
            self.stage = 0
            self._off()
            return

        if self.first_detect_time is None:
            self.first_detect_time = now
            return

        elapsed_sec = now - self.first_detect_time
        self._update_stage(elapsed_sec)

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