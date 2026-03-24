import os


# -----------------------------
# UART / Runtime
# -----------------------------
UART_PORT = os.getenv("POSTURE_UART_PORT", "/dev/ttyAMA0")
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