# src/core/feature_extractor.py

# 비율 계산 시 최소 하중 임계값 (kg)
# total이 이 값 미만이면 노이즈로 간주하여 비율을 0으로 처리한다.
# 이렇게 하면 하중이 없는 센서 그룹에서 노이즈에 의한 on/off 떨림이
# back_lr_diff를 0~1로 랜덤 점프시키는 문제를 방지한다.
BACK_MIN_TOTAL_KG = 0.5
SEAT_MIN_TOTAL_KG = 0.5


def extract_features(packet, baseline=None):
    loadcell = packet["loadcell"]
    tof = packet["tof"]
    imu = packet["imu"]

    # -----------------------------
    # Loadcell: back
    # -----------------------------
    br_top = loadcell["back_right"]["top"]
    br_um = loadcell["back_right"]["upper_mid"]
    br_lm = loadcell["back_right"]["lower_mid"]
    br_bottom = loadcell["back_right"]["bottom"]

    bl_top = loadcell["back_left"]["top"]
    bl_um = loadcell["back_left"]["upper_mid"]
    bl_lm = loadcell["back_left"]["lower_mid"]
    bl_bottom = loadcell["back_left"]["bottom"]

    back_right_total = br_top + br_um + br_lm + br_bottom
    back_left_total = bl_top + bl_um + bl_lm + bl_bottom
    back_total_raw = back_right_total + back_left_total
    back_total = back_total_raw + 1e-6

    # total이 최소 임계값 미만이면 비율 = 0 (노이즈 영역)
    if back_total_raw < BACK_MIN_TOTAL_KG:
        back_lr_diff = 0.0
    else:
        back_lr_diff = abs(back_right_total - back_left_total) / back_total

    back_upper = br_top + br_um + bl_top + bl_um
    back_lower = br_lm + br_bottom + bl_lm + bl_bottom
    back_upper_lower_ratio = back_upper / (back_lower + 1e-6)

    # -----------------------------
    # Loadcell: seat
    # -----------------------------
    sr_rear = loadcell["seat_right"]["rear"]
    sr_front = loadcell["seat_right"]["front"]
    sl_rear = loadcell["seat_left"]["rear"]
    sl_front = loadcell["seat_left"]["front"]

    seat_right_total = sr_rear + sr_front
    seat_left_total = sl_rear + sl_front
    seat_total_raw = seat_right_total + seat_left_total
    seat_total = seat_total_raw + 1e-6

    seat_front_total = sr_front + sl_front
    seat_rear_total = sr_rear + sl_rear

    # total이 최소 임계값 미만이면 비율 = 0 (노이즈 영역)
    if seat_total_raw < SEAT_MIN_TOTAL_KG:
        seat_lr_diff = 0.0
        seat_fb_shift = 0.0
    else:
        seat_lr_diff = abs(seat_right_total - seat_left_total) / seat_total
        seat_fb_shift = (seat_front_total - seat_rear_total) / seat_total

    # -----------------------------
    # ToF: head summary (기존 neck 역할 대체)
    # -----------------------------
    head_summary = tof["head_summary"]
    neck_mean = head_summary["mean"]
    neck_lr_diff = head_summary["lr_diff"]

    # -----------------------------
    # ToF: spine
    # -----------------------------
    spine_upper = tof["spine"]["upper"]
    spine_upper_mid = tof["spine"]["upper_mid"]
    spine_lower_mid = tof["spine"]["lower_mid"]
    spine_lower = tof["spine"]["lower"]

    spine_mid_avg = (spine_upper_mid + spine_lower_mid) / 2.0
    spine_curve = spine_upper - spine_lower

    spine_variation = (
        abs(spine_upper - spine_upper_mid) +
        abs(spine_upper_mid - spine_lower_mid) +
        abs(spine_lower_mid - spine_lower)
    ) / 3.0

    neck_forward_delta = neck_mean - spine_mid_avg

    # -----------------------------
    # IMU: pitch only
    # -----------------------------
    right_pitch_deg = imu["right_pitch_deg"]
    left_pitch_deg = imu["left_pitch_deg"]
    pitch_fused_deg = imu["pitch_fused_deg"]
    pitch_lr_diff_deg = imu["pitch_lr_diff_deg"]

    imu_motion_proxy = (abs(right_pitch_deg) + abs(left_pitch_deg)) / 2.0

    # -----------------------------
    # classifier 입력용 feature 순서 유지(18개 유지)
    # 기존 gyro_y_filt / tilt_est / motion_level 자리를
    # pitch_fused_deg / pitch_lr_diff_deg / imu_motion_proxy로 대체
    # -----------------------------
    features = [
        back_lr_diff,             # 0
        back_upper_lower_ratio,   # 1
        seat_lr_diff,             # 2
        seat_fb_shift,            # 3
        neck_mean,                # 4
        neck_lr_diff,             # 5
        spine_curve,              # 6
        spine_variation,          # 7
        neck_forward_delta,       # 8
        pitch_fused_deg,          # 9
        pitch_lr_diff_deg,        # 10
        imu_motion_proxy,         # 11
        back_right_total,         # 12
        back_left_total,          # 13
        seat_right_total,         # 14
        seat_left_total,          # 15
        seat_front_total,         # 16
        seat_rear_total,          # 17
    ]

    feature_map = {
        "back_lr_diff": back_lr_diff,
        "back_upper_lower_ratio": back_upper_lower_ratio,
        "seat_lr_diff": seat_lr_diff,
        "seat_fb_shift": seat_fb_shift,
        "neck_mean": neck_mean,
        "neck_lr_diff": neck_lr_diff,
        "spine_curve": spine_curve,
        "spine_variation": spine_variation,
        "neck_forward_delta": neck_forward_delta,
        "pitch_fused_deg": pitch_fused_deg,
        "pitch_lr_diff_deg": pitch_lr_diff_deg,
        "imu_motion_proxy": imu_motion_proxy,
        "back_right_total": back_right_total,
        "back_left_total": back_left_total,
        "seat_right_total": seat_right_total,
        "seat_left_total": seat_left_total,
        "seat_front_total": seat_front_total,
        "seat_rear_total": seat_rear_total,
        "back_total": back_right_total + back_left_total,
        "seat_total": seat_right_total + seat_left_total,
        # 개별 로드셀 kg (baseline 저장 → sensor_distribution percent 계산용)
        "back_left_top_kg": bl_top,
        "back_left_upper_mid_kg": bl_um,
        "back_left_lower_mid_kg": bl_lm,
        "back_left_bottom_kg": bl_bottom,
        "back_right_top_kg": br_top,
        "back_right_upper_mid_kg": br_um,
        "back_right_lower_mid_kg": br_lm,
        "back_right_bottom_kg": br_bottom,
        "seat_rear_left_kg": sl_rear,
        "seat_rear_right_kg": sr_rear,
        "seat_front_left_kg": sl_front,
        "seat_front_right_kg": sr_front,
    }

    delta_map = {}

    if baseline is not None:
        for key, value in feature_map.items():
            if key in baseline and isinstance(baseline[key], (int, float)):
                delta_map[f"{key}_delta"] = value - baseline[key]

    return {
        "features": features,
        "feature_map": feature_map,
        "delta_map": delta_map,
    }