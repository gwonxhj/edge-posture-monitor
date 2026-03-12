from collections import defaultdict


class CalibrationManager:
    def __init__(self, sample_rate_hz=50):
        self.sample_rate_hz = sample_rate_hz
        self.reset()

    def reset(self):
        self.collected_count = 0
        self.feature_sums = defaultdict(float)
        self.feature_keys = None

    def add_feature_map_sample(self, feature_map: dict):
        if self.feature_keys is None:
            self.feature_keys = list(feature_map.keys())

        for key in self.feature_keys:
            self.feature_sums[key] += float(feature_map[key])

        self.collected_count += 1

    def is_enough_samples(self, duration_sec=10):
        required_samples = int(duration_sec * self.sample_rate_hz)
        return self.collected_count >= required_samples

    def get_baseline(self):
        if self.collected_count == 0:
            raise ValueError("No calibration samples collected")

        baseline = {}
        for key in self.feature_keys:
            baseline[key] = self.feature_sums[key] / self.collected_count

        return baseline

    def run_calibration_loop(
        self,
        receiver,
        mapper_func,
        feature_extractor_func,
        duration_sec=10,
        verbose=True,
    ):
        self.reset()

        required_samples = int(duration_sec * self.sample_rate_hz)

        if verbose:
            print(f"[Calibration] Start: collecting {required_samples} samples...")

        while self.collected_count < required_samples:
            raw_packet = receiver.read_real_sensor()
            if raw_packet is None:
                continue

            semantic_packet = mapper_func(raw_packet)
            extracted = feature_extractor_func(semantic_packet, baseline=None)
            feature_map = extracted["feature_map"]

            self.add_feature_map_sample(feature_map)

            if verbose and self.collected_count % self.sample_rate_hz == 0:
                sec = self.collected_count / self.sample_rate_hz
                print(f"[Calibration] {sec:.0f}s collected...")

        baseline = self.get_baseline()

        if verbose:
            print("[Calibration] Done.")
            print("[Calibration] Baseline:")
            for k, v in baseline.items():
                print(f"  {k}: {v:.4f}")

        return baseline