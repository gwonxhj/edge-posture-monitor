import csv

from src.sensor.sensor_simulator import POSTURE_LABELS, read_mock_sensor
from src.sensor.sensor_mapper import map_raw_packet
from src.core.feature_extractor import extract_features


def generate_dataset(output_path="data/posture_dataset.csv", samples_per_class=400):
    rows = []

    for label in POSTURE_LABELS:
        for _ in range(samples_per_class):
            raw_packet = read_mock_sensor(posture=label)

            # mock sensor output -> real mapper input 형식 보정
            if "frame_type" not in raw_packet:
                raw_packet["frame_type"] = "DAT"
            if "received_at_ms" not in raw_packet:
                raw_packet["received_at_ms"] = 0

            semantic_packet = map_raw_packet(raw_packet)
            extracted = extract_features(semantic_packet)
            if len(rows) == 0:
                print("[DEBUG raw_packet]")
                print(raw_packet)
                print("[DEBUG semantic_packet]")
                print(semantic_packet)
                print("[DEBUG feature_map]")
                print(extracted["feature_map"])
            rows.append(extracted["features"] + [label])

            

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
        "pitch_fused_deg",
        "pitch_lr_diff_deg",
        "imu_motion_proxy",
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