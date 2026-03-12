import os
import time


class AudioFeedback:
    def __init__(self):
        self.last_posture_alert_time = 0
        self.last_rest_alert_time = 0

    def _beep(self):
        os.system("printf '\a'")

    def _say(self, text: str):
        # macOS 기본 음성 명령
        os.system(f'say "{text}"')

    def play_posture_alert(self, posture: str):
        now = time.time()

        # posture alert 연속 중복 방지
        if now - self.last_posture_alert_time < 5:
            return

        self.last_posture_alert_time = now

        print(f"[AUDIO] 자세 경고음 출력: {posture}")
        self._beep()

        message_map = {
            "turtle_neck": "거북목 자세를 교정해주세요.",
            "forward_lean": "상체를 곧게 펴주세요.",
            "reclined": "의자에 바르게 앉아주세요.",
            "side_slouch": "비뚤어진 자세를 교정해주세요.",
            "leg_cross_suspect": "다리를 바르게 두어주세요.",
            "thinking_pose": "몸을 펴고 바르게 앉아주세요.",
            "perching": "걸터앉은 자세를 교정해주세요.",
        }

        msg = message_map.get(posture, "자세를 교정해주세요.")
        self._say(msg)

    def play_rest_alert(self):
        now = time.time()

        if now - self.last_rest_alert_time < 30:
            return

        self.last_rest_alert_time = now

        print("[AUDIO] 휴식 알림음 출력")
        self._beep()
        self._say("휴식 시간이 되었습니다. 잠시 일어나 스트레칭 해주세요.")