EXERCISE_TRIGGER_SEC = 5

class ReportEnhancer:
    """
    LLM 없이 리포트 해석을 담당하는 rule-based 엔진
    """

    

    def build_enhanced_report(self, overall_summary, minute_summary):
        return {
            "summary_text": self._build_summary_text(overall_summary),
            "trend_text": self._build_trend_text(minute_summary),
            "exercise_recommendations": self._build_exercise(overall_summary),
        }

    def _build_summary_text(self, summary):
        dominant = summary.get("dominant_posture")
        score = summary.get("avg_score", 0)
        bad_ratio = summary.get("bad_posture_ratio", 0)

        level = self._score_to_level(score)

        if dominant is None:
            return (
                f"전체 평균 점수는 {score}점으로 {level} 수준입니다. "
                f"측정 데이터가 충분하지 않아 주요 자세를 특정하기 어렵습니다."
            )

        return (
            f"전체 평균 점수는 {score}점으로 {level} 수준입니다. "
            f"주요 자세는 {dominant}이며, "
            f"나쁜 자세 비율은 {bad_ratio}%입니다."
        )

    def _build_trend_text(self, minute_summary):
        if not minute_summary:
            return "분석할 분 단위 자세 데이터가 부족합니다."

        postures = [
            item["dominant_posture"]
            for item in minute_summary
            if item.get("dominant_posture") is not None
        ]

        if not postures:
            return "분석할 자세 추이 데이터가 부족합니다."

        first = postures[0]
        last = postures[-1]

        counts = {}
        for posture in postures:
            counts[posture] = counts.get(posture, 0) + 1

        dominant = max(counts, key=counts.get)

        if len(counts) == 1:
            return f"측정 전반에서 {dominant} 자세가 지속되었습니다."

        if first == last:
            return (
                f"자세가 여러 형태로 변화했지만, 전반적으로 {dominant} 자세 비중이 가장 높았습니다."
            )

        return (
            f"초반에는 {first} 자세 양상이 나타났고, "
            f"후반에는 {last} 자세 양상으로 변화했습니다. "
            f"전체적으로는 {dominant} 자세 비중이 가장 높았습니다."
        )

    def _build_exercise(self, summary):
        posture_duration_sec = summary.get("posture_duration_sec", {}) or {}

        recommendations = []

        if posture_duration_sec.get("turtle_neck", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "턱 당기기 스트레칭",
                "어깨 열기 스트레칭",
                "벽 자세 교정",
            ])

        if posture_duration_sec.get("forward_lean", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "허리 신전 스트레칭",
                "플랭크",
                "고관절 스트레칭",
            ])

        if posture_duration_sec.get("side_slouch", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "좌우 밸런스 스트레칭",
                "측면 코어 운동",
                "골반 정렬 운동",
            ])

        if posture_duration_sec.get("reclined", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "흉추 가동성 스트레칭",
                "골반 중립 자세 연습",
            ])

        if posture_duration_sec.get("perching", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "햄스트링 스트레칭",
                "엉덩이-허리 안정화 운동",
            ])

        if posture_duration_sec.get("thinking_pose", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "목-등 상부 스트레칭",
                "어깨 후인 자세 연습",
            ])

        if posture_duration_sec.get("leg_cross_suspect", 0) >= EXERCISE_TRIGGER_SEC:
            recommendations.extend([
                "고관절 좌우 밸런스 스트레칭",
                "골반 정렬 운동",
            ])

        # 중복 제거 + 순서 유지
        unique_recommendations = []
        seen = set()
        for item in recommendations:
            if item not in seen:
                seen.add(item)
                unique_recommendations.append(item)

        if not unique_recommendations:
            unique_recommendations = [
                "가벼운 목/어깨 스트레칭",
                "바른 착석 자세 유지 연습",
            ]

        return unique_recommendations

    def _score_to_level(self, score):
        if score >= 85:
            return "우수"
        elif score >= 70:
            return "보통"
        elif score >= 50:
            return "주의"
        return "위험"