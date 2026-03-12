POSTURE_NORMAL = "normal"
POSTURE_TURTLE = "turtle_neck"
POSTURE_FORWARD = "forward_lean"
POSTURE_RECLINED = "reclined"
POSTURE_SIDE_SLOUCH = "side_slouch"
POSTURE_LEG_CROSS = "leg_cross_suspect"
POSTURE_THINKING = "thinking_pose"

COMBO_FORWARD_TURTLE = "forward_lean + turtle_neck"
COMBO_SIDE_LEG = "side_slouch + leg_cross"

POSTURE_WEIGHT = {

    "turtle_neck": 0.2,
    "forward_lean": 0.2,
    "thinking_pose": 0.2,

    "reclined": 0.1,
    "leg_cross_suspect": 0.1,

    "side_slouch": 0.3,

    "forward_lean + turtle_neck": 0.3,
    "side_slouch + leg_cross": 0.3,

    "normal": 0.0
}