import os


# -----------------------------
# UART / Runtime
# -----------------------------
UART_PORT = os.getenv("POSTURE_UART_PORT", "/dev/ttyAMA3")
UART_BAUD = int(os.getenv("POSTURE_UART_BAUD", "921600"))
UART_MOCK_MODE = os.getenv("POSTURE_UART_MOCK", "0") == "1"

SAMPLE_RATE_HZ = int(os.getenv("POSTURE_SAMPLE_RATE_HZ", "50"))
CALIBRATION_DURATION_SEC = int(os.getenv("POSTURE_CALIBRATION_SEC", "10"))

# READY 수신 후 ACK 보내기 전 대기
HANDSHAKE_AFTER_READY_DELAY_SEC = float(
    os.getenv("POSTURE_HANDSHAKE_AFTER_READY_DELAY_SEC", "0.2")
)

# SIT 확인 후 다음 명령(CAL/GO) 보내기 전 대기
SIT_TO_NEXT_CMD_DELAY_SEC = float(
    os.getenv("POSTURE_SIT_TO_NEXT_CMD_DELAY_SEC", "0.2")
)


# -----------------------------
# Debug / Logging
# -----------------------------
DEBUG_SENSOR_SUMMARY = os.getenv("POSTURE_DEBUG_SENSOR", "0") == "1"
DEBUG_FEATURES = os.getenv("POSTURE_DEBUG_FEATURES", "0") == "1"
DEBUG_FLAGS = os.getenv("POSTURE_DEBUG_FLAGS", "0") == "1"
DEBUG_SENSOR_RAW = os.getenv("POSTURE_DEBUG_SENSOR_RAW", "0") == "1"
DEBUG_SUMMARY_EVERY_N = max(1, int(os.getenv("POSTURE_DEBUG_SUMMARY_EVERY_N", "50")))
ENABLE_SAMPLE_LOGGER = os.getenv("POSTURE_ENABLE_SAMPLE_LOGGER", "1") == "1"


# -----------------------------
# Report / Future extension
# -----------------------------
REPORT_ENGINE = os.getenv("POSTURE_REPORT_ENGINE", "rule")
LLM_REPORT_MODE = os.getenv("POSTURE_LLM_REPORT_MODE", "mock")
LLM_MODEL_BACKEND = os.getenv("POSTURE_LLM_MODEL_BACKEND", "llama_cpp")
LLM_GGUF_MODEL_PATH = os.getenv("POSTURE_LLM_GGUF_MODEL_PATH", "")
LLM_CONTEXT_LEN = int(os.getenv("POSTURE_LLM_CONTEXT_LEN", "2048"))
LLM_MAX_TOKENS = int(os.getenv("POSTURE_LLM_MAX_TOKENS", "256"))
LLM_TEMPERATURE = float(os.getenv("POSTURE_LLM_TEMPERATURE", "0.2"))
# REPORT_ENGINE:
# - "rule": 기존 rule-based 리포트
# - "llm" : LLM-ready 리포트 엔진
#
# LLM_REPORT_MODE:
# - "mock": 실제 LLM 호출 없이 mock LLM 형태로 동작
# 향후 OpenAI / local LLM 연결 시 여기서 모드 확장 가능

# -----------------------------
# Classifier behavior
# -----------------------------
CLASSIFIER_FALLBACK_TO_RULE = True

# -----------------------------
# Buzzer Feedback Settings
# -----------------------------

BUZZER_ENABLE = os.getenv("POSTURE_BUZZER_ENABLE", "0") == "1"

# 최초 감지 후 알람 시작까지 대기 시간 (초)
BUZZER_INITIAL_DELAY_SEC = float(
    os.getenv("POSTURE_BUZZER_INITIAL_DELAY_SEC", "5.0")
)

# stage별 기본 interval (초)
BUZZER_STAGE1_INTERVAL = float(
    os.getenv("POSTURE_BUZZER_STAGE1_INTERVAL", "5.0")
)
BUZZER_STAGE2_INTERVAL = float(
    os.getenv("POSTURE_BUZZER_STAGE2_INTERVAL", "3.0")
)
BUZZER_STAGE3_INTERVAL = float(
    os.getenv("POSTURE_BUZZER_STAGE3_INTERVAL", "1.5")
)

# posture 개수 증가 시 가속 계수
BUZZER_MULTI_POSTURE_FACTOR = float(
    os.getenv("POSTURE_BUZZER_MULTI_POSTURE_FACTOR", "0.3")
)

# posture 위험도 weight
BUZZER_WEIGHT_MAP = {
    "turtle_neck": 1.0,
    "forward_lean": 1.2,
    "side_slouch": 1.1,
    "perching": 1.3,
    "leg_cross_suspect": 1.15,
    "thinking_pose": 1.05,
    "reclined": 1.1,
}