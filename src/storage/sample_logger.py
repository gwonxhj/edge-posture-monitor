import csv
import json
import os
from datetime import datetime


class SampleLogger:
    def __init__(self, output_dir="sample_logs", enabled=True):
        self.output_dir = output_dir
        self.enabled = enabled
        self.filepath = None
        self.fieldnames = None

        if self.enabled:
            os.makedirs(self.output_dir, exist_ok=True)

    def start_session_log(self, user_id: str, session_id: int):
        if not self.enabled:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_user-{user_id}_session-{session_id}.csv"
        self.filepath = os.path.join(self.output_dir, filename)
        self.fieldnames = None

    def _flatten_sample(
        self,
        user_id,
        session_id,
        raw_packet,
        semantic_packet,
        feature_map,
        delta_map,
        predicted,
        flags,
        label=None,
        source="runtime",
    ):
        row = {
            "logged_at": datetime.now().isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "frame_type": raw_packet.get("frame_type"),
            "timestamp_ms": semantic_packet.get("timestamp_ms"),
            "label": label if label is not None else "",
            "predicted_posture": predicted,
            "source": source,
            "flags_json": json.dumps(flags, ensure_ascii=False),
        }

        # raw packet
        for i, v in enumerate(raw_packet.get("loadcell", [])):
            row[f"raw_loadcell_{i}"] = v

        for i, v in enumerate(raw_packet.get("tof_1d", [])):
            row[f"raw_tof1d_{i}"] = v

        for i, v in enumerate(raw_packet.get("tof_3d", [])):
            row[f"raw_tof3d_{i}"] = v

        for i, v in enumerate(raw_packet.get("mpu", [])):
            row[f"raw_mpu_{i}"] = v

        # semantic packet - loadcell
        loadcell = semantic_packet.get("loadcell", {})
        for section_name, section_values in loadcell.items():
            for key, value in section_values.items():
                row[f"loadcell_{section_name}_{key}"] = value

        # semantic packet - spine tof
        spine = semantic_packet.get("tof", {}).get("spine", {})
        for key, value in spine.items():
            row[f"spine_{key}"] = value

        # semantic packet - head summary
        head_summary = semantic_packet.get("tof", {}).get("head_summary", {})
        for key, value in head_summary.items():
            row[f"head_{key}"] = value

        # semantic packet - imu
        imu = semantic_packet.get("imu", {})
        for key, value in imu.items():
            row[f"imu_{key}"] = value

        # feature map
        for key, value in feature_map.items():
            row[f"feature_{key}"] = value

        # delta map
        for key, value in delta_map.items():
            row[f"delta_{key}"] = value

        return row

    def log_sample(
        self,
        user_id,
        session_id,
        raw_packet,
        semantic_packet,
        feature_map,
        delta_map,
        predicted,
        flags,
        label=None,
        source="runtime",
    ):
        if not self.enabled or self.filepath is None:
            return

        row = self._flatten_sample(
            user_id=user_id,
            session_id=session_id,
            raw_packet=raw_packet,
            semantic_packet=semantic_packet,
            feature_map=feature_map,
            delta_map=delta_map,
            predicted=predicted,
            flags=flags,
            label=label,
            source=source,
        )

        if self.fieldnames is None:
            self.fieldnames = list(row.keys())

            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerow(row)
            return

        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(row)