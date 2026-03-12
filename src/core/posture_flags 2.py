def detect_posture_flags(feature_map, delta_map=None):
    if delta_map is None:
        delta_map = {}

    back_lr_diff = feature_map["back_lr_diff"]
    seat_lr_diff = feature_map["seat_lr_diff"]
    seat_fb_shift = feature_map["seat_fb_shift"]
    neck_mean = feature_map["neck_mean"]
    neck_forward_delta = feature_map["neck_forward_delta"]
    spine_curve = feature_map["spine_curve"]
    tilt_est = feature_map["tilt_est"]
    back_total = feature_map["back_total"]

    # baseline delta
    seat_fb_shift_delta = delta_map.get("seat_fb_shift_delta", seat_fb_shift)
    neck_mean_delta = delta_map.get("neck_mean_delta", 0.0)
    neck_forward_delta_delta = delta_map.get("neck_forward_delta_delta", neck_forward_delta)
    spine_curve_delta = delta_map.get("spine_curve_delta", spine_curve)
    tilt_est_delta = delta_map.get("tilt_est_delta", tilt_est)
    back_lr_diff_delta = delta_map.get("back_lr_diff_delta", back_lr_diff)
    seat_lr_diff_delta = delta_map.get("seat_lr_diff_delta", seat_lr_diff)
    back_total_delta = delta_map.get("back_total_delta", 0.0)

    flags = {
        "turtle_neck": False,
        "forward_lean": False,
        "reclined": False,
        "side_slouch": False,
        "leg_cross_suspect": False,
        "thinking_pose": False,
        "perching": False,
        "normal": False,
    }

    # 1) perching 최우선
    # - 좌판 앞쪽 강한 쏠림
    # - 등판 접촉 현저히 적음
    # - 전방 기울기 큼
    if (
        seat_fb_shift > 0.30 and
        tilt_est > 6.0 and
        back_total < 42
    ):
        flags["perching"] = True

    # 2) turtle_neck
    if (
        neck_forward_delta > 5.0 or
        neck_mean_delta > 6.0 or
        neck_forward_delta_delta > 4.0
    ):
        flags["turtle_neck"] = True

    # 3) forward_lean
    if (
        seat_fb_shift > 0.16 and
        spine_curve > 7.0 and
        tilt_est > 5.0
    ):
        flags["forward_lean"] = True

    # baseline 보정
    if (
        seat_fb_shift_delta > 0.12 and
        spine_curve_delta > 4.0 and
        tilt_est_delta > 3.5
    ):
        flags["forward_lean"] = True

    # 4) reclined
    if (
        seat_fb_shift < -0.10 and
        tilt_est < -4.0 and
        back_total > 85
    ):
        flags["reclined"] = True

    # 5) side_slouch
    if (
        back_lr_diff > 0.15 and
        seat_lr_diff > 0.10
    ):
        flags["side_slouch"] = True

    if (
        back_lr_diff_delta > 0.10 and
        seat_lr_diff_delta > 0.08
    ):
        flags["side_slouch"] = True

    # 6) leg_cross_suspect
    if (
        seat_lr_diff > 0.12 and
        back_lr_diff < 0.14
    ):
        flags["leg_cross_suspect"] = True

    # 7) thinking_pose
    # - forward lean/turtle neck 성격이 일부 같이 나타날 수 있음
    # - 다만 perching일 정도로 back_total이 낮으면 제외
    if not flags["perching"]:
        if (
            seat_fb_shift > 0.18 and
            neck_forward_delta > 4.0 and
            30 <= back_total <= 75 and
            tilt_est > 4.0
        ):
            flags["thinking_pose"] = True

        if (
            seat_fb_shift_delta > 0.10 and
            neck_forward_delta_delta > 2.5 and
            35 <= back_total <= 80
        ):
            flags["thinking_pose"] = True

    # normal 처리
    if not any(v for k, v in flags.items() if k != "normal"):
        flags["normal"] = True

    return flags