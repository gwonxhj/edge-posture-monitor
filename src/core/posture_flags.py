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
    seat_fb_shift_delta = delta_map.get("seat_fb_shift_delta", seat_fb_shift)
    neck_mean_delta = delta_map.get("neck_mean_delta", 0.0)
    neck_forward_delta_delta = delta_map.get(
        "neck_forward_delta_delta",
        neck_forward_delta,
    )
    spine_curve_delta = delta_map.get("spine_curve_delta", spine_curve)
    pitch_fused_deg_delta = delta_map.get(
        "pitch_fused_deg_delta",
        pitch_fused_deg,
    )
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
        seat_fb_shift > 0.28 and
        pitch_fused_deg > 5.5 and
        back_total < 30
    ):
        flags["perching"] = True

    # 2) turtle_neck
    # - 목 전방이 분명해야 하며
    # - 단순 thinking_pose 수준의 약한 전방 이동은 제외
    if (
        (neck_forward_delta > 5.5 and neck_mean_delta > 4.0) or
        (neck_mean_delta > 6.5) or
        (neck_forward_delta_delta > 4.5 and pitch_fused_deg > 3.0)
    ):
        flags["turtle_neck"] = True

    # 3) forward_lean
    # - 몸통 전체가 앞으로 기울어진 자세
    # - thinking_pose보다 좌판 전방 쏠림과 척추 굴곡이 더 커야 함
    if (
        seat_fb_shift > 0.20 and
        spine_curve > 8.5 and
        pitch_fused_deg > 5.5 and
        back_total >= 36
    ):
        flags["forward_lean"] = True

    # baseline 보정
    if (
        seat_fb_shift_delta > 0.14 and
        spine_curve_delta > 4.5 and
        pitch_fused_deg_delta > 3.5 and
        back_total >= 36
    ):
        flags["forward_lean"] = True

    # 4) reclined
    if (
        seat_fb_shift < -0.10 and
        pitch_fused_deg < -4.0 and
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
    # - 몸통 전체 붕괴보다는 상부/목 중심의 약한 전방 자세
    # - perching, turtle_neck는 제외
    # - forward_lean보다 좌판 전방 쏠림과 척추 굴곡이 약해야 함
    if not flags["perching"] and not flags["turtle_neck"]:
        if (
            0.04 < seat_fb_shift <= 0.16 and
            2.0 < neck_forward_delta <= 5.0 and
            38 <= back_total <= 90 and
            1.5 <= pitch_fused_deg <= 5.0 and
            spine_curve < 6.5
        ):
            flags["thinking_pose"] = True

        if (
            0.03 < seat_fb_shift_delta <= 0.10 and
            1.0 < neck_forward_delta_delta <= 3.5 and
            38 <= back_total <= 90 and
            spine_curve_delta < 3.0
        ):
            flags["thinking_pose"] = True

    # normal 처리
    if not any(v for k, v in flags.items() if k != "normal"):
        flags["normal"] = True

    return flags