"""
최종 형태

You are a posture correction expert.

User posture summary:
- avg_score: 72
- dominant_posture: turtle_neck
- bad_posture_ratio: 65%

Tasks:
1. Explain posture issues
2. Suggest 3 exercises
3. Provide short summary

Answer in Korean.
"""

class ReportLLMService:
    """
    측정 종료 후 리포트 기반 LLM 피드백 생성 서비스
    """

    def generate_feedback(self, overall_summary, minute_summary):
        """
        overall_summary: build_overall_summary 결과
        minute_summary: build_minute_summary 결과

        return:
        {
            "posture_analysis": "...",
            "trend_analysis": "...",
            "exercise_recommendations": [...]
        }
        """

        # TODO: 실제 LLM 연결 전 임시 로직
        posture = overall_summary.get("dominant_posture")

        exercise_map = {
            "turtle_neck": [
                "목 뒤 스트레칭 (chin tuck)",
                "어깨 열기 스트레칭",
                "벽 기대 자세 교정"
            ],
            "forward_lean": [
                "허리 신전 스트레칭",
                "코어 강화 플랭크",
                "고관절 펴기 스트레칭"
            ],
            "side_slouch": [
                "좌우 균형 스트레칭",
                "측면 코어 운동",
                "골반 정렬 스트레칭"
            ],
        }

        return {
            "posture_analysis": f"주요 자세는 {posture} 입니다.",
            "trend_analysis": "시간에 따른 자세 변화 분석은 추후 LLM 적용 예정",
            "exercise_recommendations": exercise_map.get(posture, []),
        }