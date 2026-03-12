from collections import Counter


class ReportGenerator:
    def __init__(self):
        self.score_history = []
        self.posture_history = []
        self.minute_buckets = []

    def add_sample(self, timestamp_sec, score, posture):
        self.score_history.append({
            "timestamp_sec": timestamp_sec,
            "score": score,
        })
        self.posture_history.append({
            "timestamp_sec": timestamp_sec,
            "posture": posture,
        })

    def _calc_good_bad_ratio(self, posture_duration_sec, total_sitting_sec):
        normal_sec = float(posture_duration_sec.get("normal", 0) or 0)

        if total_sitting_sec <= 0:
            return 0.0, 0.0

        good_ratio = round((normal_sec / total_sitting_sec) * 100, 2)
        bad_ratio = round(100.0 - good_ratio, 2)
        return good_ratio, bad_ratio

    def build_overall_summary(self, total_sitting_sec, posture_duration_sec):
        total_sitting_sec = round(total_sitting_sec, 2)
        good_posture_ratio, bad_posture_ratio = self._calc_good_bad_ratio(
            posture_duration_sec=posture_duration_sec,
            total_sitting_sec=total_sitting_sec,
        )

        if not self.score_history:
            return {
                "avg_score": 0,
                "total_sitting_sec": total_sitting_sec,
                "dominant_posture": None,
                "dominant_posture_ratio": 0,
                "good_posture_ratio": good_posture_ratio,
                "bad_posture_ratio": bad_posture_ratio,
                "posture_duration_sec": posture_duration_sec,
            }

        avg_score = round(
            sum(x["score"] for x in self.score_history) / len(self.score_history),
            2
        )

        postures = [x["posture"] for x in self.posture_history]
        posture_counter = Counter(postures)

        dominant_posture = None
        dominant_ratio = 0.0

        if posture_counter:
            dominant_posture, dominant_count = posture_counter.most_common(1)[0]
            dominant_ratio = round(100.0 * dominant_count / len(postures), 2)

        return {
            "avg_score": avg_score,
            "total_sitting_sec": total_sitting_sec,
            "dominant_posture": dominant_posture,
            "dominant_posture_ratio": dominant_ratio,
            "good_posture_ratio": good_posture_ratio,
            "bad_posture_ratio": bad_posture_ratio,
            "posture_duration_sec": posture_duration_sec,
        }

    def build_minute_summary(self):
        if not self.score_history:
            return []

        minute_map = {}

        for item in self.score_history:
            minute_idx = int(item["timestamp_sec"] // 60)
            minute_map.setdefault(minute_idx, {"scores": [], "postures": []})
            minute_map[minute_idx]["scores"].append(item["score"])

        for item in self.posture_history:
            minute_idx = int(item["timestamp_sec"] // 60)
            minute_map.setdefault(minute_idx, {"scores": [], "postures": []})
            minute_map[minute_idx]["postures"].append(item["posture"])

        results = []

        for minute_idx in sorted(minute_map.keys()):
            scores = minute_map[minute_idx]["scores"]
            postures = minute_map[minute_idx]["postures"]

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0

            if postures:
                counter = Counter(postures)
                dominant_posture, dominant_count = counter.most_common(1)[0]
                dominant_ratio = round(100.0 * dominant_count / len(postures), 2)

                normal_count = counter.get("normal", 0)
                good_posture_ratio = round(100.0 * normal_count / len(postures), 2)
                bad_posture_ratio = round(100.0 - good_posture_ratio, 2)
            else:
                dominant_posture = None
                dominant_ratio = 0
                good_posture_ratio = 0
                bad_posture_ratio = 0

            results.append({
                "minute_index": minute_idx,
                "avg_score": avg_score,
                "dominant_posture": dominant_posture,
                "dominant_posture_ratio": dominant_ratio,
                "good_posture_ratio": good_posture_ratio,
                "bad_posture_ratio": bad_posture_ratio,
            })

        return results