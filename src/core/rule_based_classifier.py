class RuleBasedPostureClassifier:
    def predict(self, features):
        back_lr_diff = features[0]
        back_upper_lower_ratio = features[1]
        seat_lr_diff = features[2]
        seat_fb_shift = features[3]
        neck_mean = features[4]
        neck_lr_diff = features[5]
        spine_curve = features[6]
        spine_variation = features[7]
        neck_forward_delta = features[8]
        gyro_y_filt = features[9]
        tilt_est = features[10]
        back_right_total = features[12]
        back_left_total = features[13]

        back_total = back_right_total + back_left_total

        if seat_fb_shift > 0.30 and back_total < 38 and tilt_est > 6.0:
            return "perching"

        if seat_fb_shift > 0.18 and neck_forward_delta > 4.5 and 38 <= back_total <= 70 and tilt_est > 4.0:
            return "thinking_pose"

        if neck_forward_delta > 6.0 and tilt_est < 6.0 and seat_fb_shift < 0.18:
            return "turtle_neck"

        if seat_fb_shift > 0.16 and spine_curve > 7.0 and tilt_est > 6.0 and back_total >= 35:
            return "forward_lean"

        if seat_fb_shift < -0.10 and tilt_est < -4.0 and back_total > 95:
            return "reclined"

        if back_lr_diff > 0.18 and seat_lr_diff > 0.10:
            return "side_slouch"

        if seat_lr_diff > 0.14 and back_lr_diff < 0.14 and abs(seat_fb_shift) < 0.15:
            return "leg_cross_suspect"

        return "normal"