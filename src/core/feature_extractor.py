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
    back_total = back_right_total + back_left_total + 1e-6

    back_lr_diff = abs(back_right_total - back_left_total) / back_total

    back_upper = br_top + br_um + bl_top + bl_um
    back_lower = br_lm + br_bottom + bl_lm + bl_bottom
    back_upper_lower_ratio = back_upper / (back_lower + 1e-6)

    # -----------------------------
    # Loadcell: seat
    # rear = 8/10, front = 9/11
    # -----------------------------
    sr_rear = loadcell["seat_right"]["rear"]
    sr_front = loadcell["seat_right"]["front"]
    sl_rear = loadcell["seat_left"]["rear"]
    sl_front = loadcell["seat_left"]["front"]

    seat_right_total = sr_rear + sr_front
    seat_left_total = sl_rear + sl_front
    seat_total = seat_right_total + seat_left_total + 1e-6

    seat_lr_diff = abs(seat_right_total - seat_left_total) / seat_total

    seat_front_total = sr_front + sl_front
    seat_rear_total = sr_rear + sl_rear

    # front-heavy면 positive
    seat_fb_shift = (seat_front_total - seat_rear_total) / seat_total

    # -----------------------------
    # ToF: neck
    # -----------------------------
    neck_right = tof["neck"]["right"]
    neck_left = tof["neck"]["left"]

    neck_mean = (neck_right + neck_left) / 2.0
    neck_lr_diff = abs(neck_right - neck_left)

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
    # IMU
    # -----------------------------
    gyro_x_filt = imu["gyro_x_filt"]
    gyro_y_filt = imu["gyro_y_filt"]
    gyro_z_filt = imu["gyro_z_filt"]
    tilt_est = imu["tilt_est"]

    motion_level = (
        abs(gyro_x_filt) + abs(gyro_y_filt) + abs(gyro_z_filt)
    ) / 3.0

    # -----------------------------
    # classifier 입력용 feature 순서 유지
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
        gyro_y_filt,              # 9
        tilt_est,                 # 10
        motion_level,             # 11
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
        "gyro_y_filt": gyro_y_filt,
        "tilt_est": tilt_est,
        "motion_level": motion_level,
        "back_right_total": back_right_total,
        "back_left_total": back_left_total,
        "seat_right_total": seat_right_total,
        "seat_left_total": seat_left_total,
        "seat_front_total": seat_front_total,
        "seat_rear_total": seat_rear_total,
        "back_total": back_right_total + back_left_total,
        "seat_total": seat_right_total + seat_left_total,
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