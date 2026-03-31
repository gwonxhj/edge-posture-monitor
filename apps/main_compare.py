from src.core.posture_classifier import PostureClassifier
from src.core.rule_based_classifier import RuleBasedPostureClassifier
from src.sensor.sensor_simulator import read_mock_sensor, POSTURE_LABELS
from src.sensor.sensor_mapper import map_raw_packet
from src.core.feature_extractor import extract_features
from src.core.posture_mapper import to_display_label
from src.core.posture_flags import detect_posture_flags


def main():
    ml_classifier = PostureClassifier()
    rule_classifier = RuleBasedPostureClassifier()

    for posture in POSTURE_LABELS:
        print(f"\n######## TEST POSTURE: {posture} ########")
        for i in range(3):
            raw_packet = read_mock_sensor(posture=posture)
            semantic_packet = map_raw_packet(raw_packet)

            extracted = extract_features(semantic_packet)
            features = extracted["features"]
            feature_map = extracted["feature_map"]
            delta_map = extracted["delta_map"]

            ml_result = ml_classifier.predict(features)
            rule_result = rule_classifier.predict(features)
            flags = detect_posture_flags(feature_map, delta_map)

            active_flags = [k for k, v in flags.items() if v]

            print(f"===== SAMPLE {i + 1} =====")
            print("Input posture:", posture)
            print("Features:", [round(x, 4) for x in features])
            print("Rule-based :", rule_result, "->", to_display_label(rule_result))
            print("Sklearn    :", ml_result, "->", to_display_label(ml_result))
            print("Flags      :", active_flags)
            print()


if __name__ == "__main__":
    main()