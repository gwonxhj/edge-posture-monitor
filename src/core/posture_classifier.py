import joblib
import pandas as pd


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
    "pitch_fused_deg",
    "pitch_lr_diff_deg",
    "imu_motion_proxy",
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