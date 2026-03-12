def detect_combo(posture_set):

    if "forward_lean" in posture_set and "turtle_neck" in posture_set:
        return "forward_lean + turtle_neck"

    if "side_slouch" in posture_set and "leg_cross_suspect" in posture_set:
        return "side_slouch + leg_cross"

    return None