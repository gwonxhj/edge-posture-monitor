from src.sensor.sensor_simulator import read_mock_sensor
from src.sensor.sensor_mapper import map_raw_packet
from src.core.feature_extractor import extract_features
from src.core.posture_classifier import PostureClassifier
from src.core.posture_score import PostureScoreEngine
from src.core.posture_mapper import to_display_label
from src.core.posture_flags import detect_posture_flags


def main():
    classifier = PostureClassifier()
    score_engine = PostureScoreEngine(sample_rate_hz=50)

    scenario = [
        ("normal", 2),
        ("turtle_neck", 5),
        ("forward_lean", 5),
        ("reclined", 4),
        ("side_slouch", 4),
        ("leg_cross_suspect", 5),
        ("thinking_pose", 4),
        ("perching", 4),
        ("normal", 2),
    ]

    sample_idx = 1

    # mock 데모에서 1 step = 5초로 가정
    step_samples = 250

    for posture_name, repeat_count in scenario:
        print(f"\n######## SCENARIO: {posture_name} x {repeat_count} ########")
        for _ in range(repeat_count):
            raw_packet = read_mock_sensor(posture=posture_name)
            semantic_packet = map_raw_packet(raw_packet)

            extracted = extract_features(semantic_packet)
            features = extracted["features"]
            feature_map = extracted["feature_map"]
            delta_map = extracted["delta_map"]

            predicted = classifier.predict(features)
            flags = detect_posture_flags(feature_map, delta_map)

            state = score_engine.update(
                posture=predicted,
                flags=flags,
                step_samples=step_samples,
            )

            active_flags = [k for k, v in flags.items() if v]

            print(f"=== SAMPLE {sample_idx} ===")
            print("Input posture     :", posture_name)
            print("Predicted posture :", predicted, "->", to_display_label(predicted))
            print("Active flags      :", active_flags)
            print("Score             :", state["score"])
            print("Duration (sec)    :", state["current_duration_sec"])
            print("Alert             :", state["alert"])
            print("Alert stage       :", state["alert_stage"])
            print("Penalty applied   :", state["penalty_applied"])
            print()

            sample_idx += 1


if __name__ == "__main__":
    main()