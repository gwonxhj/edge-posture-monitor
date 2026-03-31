import joblib
import pandas as pd

# generate_dataset.py / feature_extractor.py와 반드시 동일한 순서 유지
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
            self._validate_model()
            print(f"[Classifier] loaded model: {model_path}")
        except FileNotFoundError:
            print(f"[Classifier] model file not found: {model_path}")
            print("[Classifier] fallback mode -> flag-based detection only")
        except Exception as e:
            print(f"[Classifier] model load failed: {e}")
            print("[Classifier] fallback mode -> flag-based detection only")

    def _validate_model(self):
        """모델이 현재 feature 구조와 호환되는지 검증"""
        if self.model is None:
            return

        expected_n = len(FEATURE_COLUMNS)

        # sklearn 모델의 n_features_ 확인
        model_n = getattr(self.model, "n_features_in_", None)
        if model_n is not None and model_n != expected_n:
            print(
                f"[Classifier] WARNING: model expects {model_n} features, "
                f"but current code provides {expected_n} features"
            )
            print("[Classifier] model may produce incorrect predictions")
            print("[Classifier] run generate_dataset.py + train_model.py to retrain")

        # feature name 호환성 확인
        model_names = getattr(self.model, "feature_names_in_", None)
        if model_names is not None:
            model_name_list = list(model_names)
            if model_name_list != FEATURE_COLUMNS:
                mismatched = [
                    (i, m, c) for i, (m, c)
                    in enumerate(zip(model_name_list, FEATURE_COLUMNS))
                    if m != c
                ]
                if mismatched:
                    print(
                        f"[Classifier] WARNING: {len(mismatched)} feature name(s) "
                        f"differ from current code"
                    )
                    for idx, model_name, code_name in mismatched[:5]:
                        print(f"  [{idx}] model='{model_name}' vs code='{code_name}'")
                    print("[Classifier] model predictions will be unreliable!")
                    print("[Classifier] disabling model -> flag-based detection only")
                    self.disable_model_inference = True

    def predict(self, features):
        if self.model is None or self.disable_model_inference:
            return "normal"

        input_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        try:
            prediction = self.model.predict(input_df)[0]
            return prediction
        except Exception as e:
            print(f"[Classifier] predict failed: {e}")
            print("[Classifier] disabling model inference -> flag-based detection only")
            self.disable_model_inference = True
            return "normal"