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
        self.model = joblib.load(model_path)

    def predict(self, features):
        input_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        prediction = self.model.predict(input_df)[0]
        return prediction