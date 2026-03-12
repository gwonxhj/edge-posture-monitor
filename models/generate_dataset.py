import csv

from src.sensor_simulator import POSTURE_LABELS, read_mock_sensor
from src.sensor_mapper import map_raw_packet
from src.feature_extractor import extract_features


def generate_dataset(output_path="data/posture_dataset.csv", samples_per_class=400):
    rows = []

    for label in POSTURE_LABELS:
        for _ in range(samples_per_class):
            raw_packet = read_mock_sensor(posture=label)
            semantic_packet = map_raw_packet(raw_packet)
            features = extract_features(semantic_packet)
            rows.append(features + [label])

    header = [
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
        "label",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Dataset saved to {output_path}")
    print(f"Total samples: {len(rows)}")


if __name__ == "__main__":
    generate_dataset()