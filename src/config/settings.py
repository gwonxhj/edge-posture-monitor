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
DEBUG_SENSOR_DISTRIBUTION = os.getenv("POSTURE_DEBUG_SENSOR_DIST", "0") == "1"

# -----------------------------
# Report / Future extension
# -----------------------------
REPORT_ENGINE = os.getenv("POSTURE_REPORT_ENGINE", "rule")
LLM_REPORT_MODE = os.getenv("POSTURE_LLM_REPORT_MODE", "mock")
LLM_MODEL_BACKEND = os.getenv("POSTURE_LLM_MODEL_BACKEND", "llama_cpp")
LLM_GGUF_MODEL_PATH = os.getenv("POSTURE_LLM_GGUF_MODEL_PATH", "models/llm/qwen2.5-0.5b-instruct-q4_k_m.gguf")
LLM_CONTEXT_LEN = int(os.getenv("POSTURE_LLM_CONTEXT_LEN", "2048"))
LLM_MAX_TOKENS = int(os.getenv("POSTURE_LLM_MAX_TOKENS", "512"))
LLM_TEMPERATURE = float(os.getenv("POSTURE_LLM_TEMPERATURE", "0.2"))
# REPORT_ENGINE:
# - "rule": 기존 rule-based 리포트
# - "llm" : LLM 리포트 엔진 (llama-cpp-python)
#
# LLM_REPORT_MODE:
# - "mock": 실제 LLM 호출 없이 rule-based fallback
# - "live": llama-cpp-python으로 실제 GGUF 모델 추론

# -----------------------------
# Classifier behavior
# -----------------------------
CLASSIFIER_FALLBACK_TO_RULE = True

# -----------------------------
# Sensor Factor Settings
# -----------------------------
# 추후 필요 시 *_OFFSETS 구조도 추가 가능

FACTOR_ENABLE = os.getenv("POSTURE_FACTOR_ENABLE", "1") == "1"

TOF_1D_FACTORS = {
    "spine_upper": 1.0,
    "spine_upper_mid": 1.0,
    "spine_lower_mid": 1.0,
    "spine_lower": 1.0,
}

TOF_3D_FACTORS = {
    "left_sensor": 1.0,
    "right_sensor": 1.0,
}

# -----------------------------
# Loadcell Calibration Settings
# -----------------------------
LOADCELL_CALIBRATION = {
    "back_right_top": {
        "offset": -37382,
        "count_per_kg": 26494.80,
    },
    "back_right_upper_mid": {
        "offset": 382921,
        "count_per_kg": 17730.19,
    },
    "back_right_lower_mid": {
        "offset": -49580,
        "count_per_kg": 28652.59,
    },
    "back_right_bottom": {
        "offset": -381543,
        "count_per_kg": 37188.80,
    },
    "back_left_top": {
        "offset": 579756,
        "count_per_kg": 19373.19,
    },
    "back_left_upper_mid": {
        "offset": 212781,
        "count_per_kg": 25634.00,
    },
    "back_left_lower_mid": {
        "offset": -437696,
        "count_per_kg": 21877.00,
    },
    "back_left_bottom": {
        "offset": 14766,
        "count_per_kg": 16290.20,
    },
    "seat_rear_right": {
        "offset": 145829,
        "count_per_kg": 45788.60,
    },
    "seat_front_right": {
        "offset": 1207776,
        "count_per_kg": 45302.19,
    },
    "seat_rear_left": {
        "offset": 470425,
        "count_per_kg": 46565.19,
    },
    "seat_front_left": {
        "offset": 145837,
        "count_per_kg": 47868.19,
    },
}