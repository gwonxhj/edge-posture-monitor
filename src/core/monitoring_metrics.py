def clamp(value, low, high):
    return max(low, min(high, value))


def score_to_level(score):
    if score >= 80:
        return "good"
    if score >= 50:
        return "warning"
    return "danger"


def similarity_score(current, baseline, danger_range):
    """
    baseline 대비 얼마나 벗어났는지 보고 0~100 안정도 점수 반환
    danger_range 이상 벗어나면 0점에 가깝게 처리
    """
    delta = abs(current - baseline)
    score = 100 * (1 - (delta / danger_range))
    return round(clamp(score, 0, 100), 1)


def build_monitoring_metrics(feature_map, baseline):
    """
    feature_map, baseline 모두 dict 기준
    앱 실시간 UI용 안정도 점수 생성
    """

    if baseline is None:
        return {
            "loadcell": {
                "balance_score": 0,
                "balance_level": "warning",
            },
            "spine_tof": {
                "score": 0,
                "level": "warning",
            },
            "neck_tof": {
                "score": 0,
                "level": "warning",
            },
        }

    # 현재값
    back_lr_diff = feature_map.get("back_lr_diff", 0.0)
    seat_lr_diff = feature_map.get("seat_lr_diff", 0.0)
    spine_curve = feature_map.get("spine_curve", 0.0)
    neck_mean = feature_map.get("neck_mean", 0.0)

    # baseline
    baseline_back_lr = baseline.get("back_lr_diff", 0.0)
    baseline_seat_lr = baseline.get("seat_lr_diff", 0.0)
    baseline_spine_curve = baseline.get("spine_curve", 0.0)
    baseline_neck_mean = baseline.get("neck_mean", 0.0)

    # 로드셀 균형 점수
    back_balance_score = similarity_score(
        back_lr_diff, baseline_back_lr, danger_range=0.25
    )
    seat_balance_score = similarity_score(
        seat_lr_diff, baseline_seat_lr, danger_range=0.25
    )
    loadcell_balance_score = round((back_balance_score + seat_balance_score) / 2.0, 1)

    # 등판 ToF 안정도
    spine_tof_score = similarity_score(
        spine_curve, baseline_spine_curve, danger_range=15.0
    )

    # 목 ToF 안정도
    neck_tof_score = similarity_score(
        neck_mean, baseline_neck_mean, danger_range=18.0
    )

    return {
        "loadcell": {
            "balance_score": loadcell_balance_score,
            "balance_level": score_to_level(loadcell_balance_score),
        },
        "spine_tof": {
            "score": spine_tof_score,
            "level": score_to_level(spine_tof_score),
        },
        "neck_tof": {
            "score": neck_tof_score,
            "level": score_to_level(neck_tof_score),
        },
    }