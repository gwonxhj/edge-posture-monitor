def detect_posture_flags(feature_map, delta_map=None):
    if delta_map is None:
        delta_map = {}

    back_lr_diff = feature_map["back_lr_diff"]
    seat_lr_diff = feature_map["seat_lr_diff"]
    seat_fb_shift = feature_map["seat_fb_shift"]
    neck_mean = feature_map["neck_mean"]
    neck_forward_delta = feature_map["neck_forward_delta"]
    spine_curve = feature_map["spine_curve"]
    pitch_fused_deg = feature_map["pitch_fused_deg"]
    back_total = feature_map["back_total"]

    # baseline delta
    seat_fb_shift_delta = delta_map.get("seat_fb_shift_delta", 0.0)
    neck_mean_delta = delta_map.get("neck_mean_delta", 0.0)
    neck_forward_delta_delta = delta_map.get("neck_forward_delta_delta", 0.0)
    spine_curve_delta = delta_map.get("spine_curve_delta", 0.0)
    pitch_fused_deg_delta = delta_map.get("pitch_fused_deg_delta", 0.0)
    back_lr_diff_delta = delta_map.get("back_lr_diff_delta", 0.0)
    seat_lr_diff_delta = delta_map.get("seat_lr_diff_delta", 0.0)
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

    # 1) perching
    # baseline 대비 좌판 전방 쏠림이 커지고,
    # 전방 기울기 증가 + 등판 접촉 감소가 동시에 나타나는 경우
    if (
        seat_fb_shift_delta > 0.20 and
        pitch_fused_deg_delta > 4.0 and
        back_total < 28 and
        back_total_delta < -12
    ):
        flags["perching"] = True

    # 2) turtle_neck
    # 절대값보다는 baseline 대비 목 전방 이동 증가를 우선 판단
    if (
        (neck_mean_delta > 10.0 and neck_forward_delta_delta > 7.0) or
        (neck_mean_delta > 14.0) or
        (neck_forward_delta_delta > 9.0 and pitch_fused_deg_delta > 4.0)
    ):
        flags["turtle_neck"] = True

    # 3) forward_lean
    # 몸통 전체의 전방 이동: 좌판 전방 쏠림 + 척추 곡률 증가 + 전방 pitch 증가
    if (
        seat_fb_shift_delta > 0.16 and
        spine_curve_delta > 8.0 and
        pitch_fused_deg_delta > 4.0 and
        back_total >= 32
    ):
        flags["forward_lean"] = True

    # 4) reclined
    # 뒤로 기대는 자세: baseline 대비 후방 이동 + 음수 pitch 증가 + 등판 접촉 증가
    if (
        seat_fb_shift_delta < -0.12 and
        pitch_fused_deg_delta < -3.0 and
        back_total > 90 and
        back_total_delta > 8
    ):
        flags["reclined"] = True

    # 5) side_slouch
    # 절대 좌우차보다 baseline 대비 좌우 불균형 증가를 우선 판단
    if (
        back_lr_diff_delta > 0.18 and
        seat_lr_diff_delta > 0.12
    ):
        flags["side_slouch"] = True

    # 6) leg_cross_suspect
    # 좌판 좌우 불균형은 커졌지만, 등판 좌우 불균형은 상대적으로 크지 않은 경우
    if (
        seat_lr_diff_delta > 0.14 and
        back_lr_diff_delta < 0.10
    ):
        flags["leg_cross_suspect"] = True

    # 7) thinking_pose
    # 약한 전방 자세: turtle_neck / perching / forward_lean보다 약한 단계
    if not flags["perching"] and not flags["turtle_neck"] and not flags["forward_lean"]:
        if (
            0.05 < seat_fb_shift_delta <= 0.16 and
            2.0 < neck_forward_delta_delta <= 6.0 and
            32 <= back_total <= 95 and
            1.5 <= pitch_fused_deg_delta <= 4.5 and
            spine_curve_delta < 6.0
        ):
            flags["thinking_pose"] = True

    # normal 처리
    if not any(v for k, v in flags.items() if k != "normal"):
        flags["normal"] = True

    return flags