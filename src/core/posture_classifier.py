import joblib
import pandas as pd

# saved_models/posture_rf.pkl이 학습될 때 사용한 옛 컬럼명을 유지
# 현재 feature 값은 새 값(pitch_fused_deg / pitch_lr_diff_deg / imu_motion_proxy)이지만
# DataFrame 컬럼명만 옛 이름으로 맞춰서 호환되게 한다.
FEATURE_COLUMNS = [
    "back_lr_diff",
    "back_upper_lower_ratio",
    "seat_lr_diff",
    "seat_fb_shift",
    "neck_mean",
    "neck_lr_diff",
    "spine_curve",
    "spine_variation",
    "neck_forward_delta",
    "gyro_y_filt",
    "tilt_est",
    "motion_level",
    "back_right_total",
    "back_left_total",
    "seat_right_total",
    "seat_left_total",
    "seat_front_total",
    "seat_rear_total",
]


class PostureClassifier:
    def __init__(self, model_path="saved_models/posture_rf.pkl"):
        self.model = None
        self.model_path = model_path
        self.disable_model_inference = False

        try:
            self.model = joblib.load(model_path)
            print(f"[Classifier] loaded model: {model_path}")
        except Exception as e:
            print(f"[Classifier] model load failed: {e}")
            print("[Classifier] fallback mode enabled -> always returns 'normal'")

    def predict(self, features):
        if self.model is None or self.disable_model_inference:
            return "normal"

        input_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        try:
            prediction = self.model.predict(input_df)[0]
            return prediction
        except Exception as e:
            print(f"[Classifier] predict failed: {e}")
            print("[Classifier] disabling model inference and falling back to 'normal'")
            self.disable_model_inference = True
            return "normal"