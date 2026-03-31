from copy import deepcopy

from src.config.settings import FACTOR_ENABLE, LOADCELL_CALIBRATION


LOADCELL_ORDER = [
    "back_right_top",
    "back_right_upper_mid",
    "back_right_lower_mid",
    "back_right_bottom",
    "back_left_top",
    "back_left_upper_mid",
    "back_left_lower_mid",
    "back_left_bottom",
    "seat_rear_right",
    "seat_front_right",
    "seat_rear_left",
    "seat_front_left",
]


def convert_loadcell_to_kg(raw_value, count_per_kg, noise_floor_kg=0.05):
    """
    STM32에서 이미 tare(offset 차감)된 HX711 값을 kg 단위로 변환한다.

    STM32가 부팅 시 HX711_Init()에서 무하중 offset을 측정하고,
    매 샘플마다 (raw - hx711_offset) 값을 전송하므로,
    RPi에서는 추가 offset 차감 없이 count_per_kg로 나누기만 하면 된다.

    스트레인 게이지 장착 방향에 따라 하중 시 음수 delta가 나올 수 있으므로
    abs()로 크기만 사용한다. (offset 제거 후이므로 안전)

    - raw_value: STM32에서 수신한 값 (이미 tare 완료)
    - count_per_kg: ADC count / kg 비율
    - noise_floor_kg: 이 값 미만은 노이즈로 간주하여 0 처리
    """
    if not count_per_kg:
        return 0.0

    weight_kg = abs(raw_value) / count_per_kg

    if weight_kg < noise_floor_kg:
        return 0.0

    return round(weight_kg, 4)


def apply_sensor_factors(raw_packet: dict, debug=False) -> dict:
    """
    raw_packet에 센서 보정을 적용한 새 dict를 반환한다.

    현재는 loadcell만 실제 calibration(offset/count_per_kg) 기반으로 변환하고,
    ToF / MPU는 기존 값을 그대로 유지한다.
    """
    if not FACTOR_ENABLE:
        return raw_packet

    corrected = deepcopy(raw_packet)

    loadcell = corrected.get("loadcell", [])
    if isinstance(loadcell, list) and loadcell:
        new_loadcell = []
        for idx, value in enumerate(loadcell):
            if idx < len(LOADCELL_ORDER):
                key = LOADCELL_ORDER[idx]
                calib = LOADCELL_CALIBRATION.get(key, {})
                count_per_kg = calib.get("count_per_kg", 1.0)
                converted = convert_loadcell_to_kg(
                    raw_value=value,
                    count_per_kg=count_per_kg,
                )

                if debug:
                    print(
                        f"  [{idx}] {key}: "
                        f"stm32_raw={value}  "
                        f"abs={abs(value)}  "
                        f"count_per_kg={count_per_kg}  "
                        f"kg={converted}"
                    )
            else:
                converted = value

            new_loadcell.append(converted)

        corrected["loadcell"] = new_loadcell

    return corrected