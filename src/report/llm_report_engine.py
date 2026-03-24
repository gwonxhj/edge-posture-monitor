# src/report/llm_report_engine.py

from typing import Any, Dict, List


class LLMReportEngine:
    """
    향후 실제 LLM(OpenAI / local LLM 등)으로 교체될 리포트 엔진.

    현재 단계에서는:
    - 입력 schema를 고정하고
    - 출력 schema(enhanced_report)를 유지하며
    - 실제 LLM 호출 없이 mock LLM 형태로 동작한다.

    최종 출력 schema:
    {
        "summary_text": str,
        "trend_text": str,
        "exercise_recommendations": list[str],
    }
    """

    def build_enhanced_report(
        self,
        overall_summary: Dict[str, Any],
        minute_summary: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        dominant_posture = overall_summary.get("dominant_posture") or "unknown"
        avg_score = float(overall_summary.get("avg_score", 0) or 0)
        bad_posture_ratio = float(overall_summary.get("bad_posture_ratio", 0) or 0)

        summary_text = self._build_summary_text(
            avg_score=avg_score,
            dominant_posture=dominant_posture,
            bad_posture_ratio=bad_posture_ratio,
        )

        trend_text = self._build_trend_text(
            dominant_posture=dominant_posture,
            minute_summary=minute_summary,
        )

        exercise_recommendations = self._build_exercise_recommendations(
            dominant_posture=dominant_posture
        )

        return {
            "summary_text": summary_text,
            "trend_text": trend_text,
            "exercise_recommendations": exercise_recommendations,
        }

    def _build_summary_text(
        self,
        avg_score: float,
        dominant_posture: str,
        bad_posture_ratio: float,
    ) -> str:
        score_level = self._score_level_text(avg_score)
        posture_kr = self._posture_to_korean(dominant_posture)

        return (
            f"전체 평균 점수는 {avg_score:.2f}점으로 {score_level} 수준입니다. "
            f"주요 자세는 {posture_kr}이며, 나쁜 자세 비율은 {bad_posture_ratio:.1f}%입니다."
        )

    def _build_trend_text(
        self,
        dominant_posture: str,
        minute_summary: List[Dict[str, Any]],
    ) -> str:
        posture_kr = self._posture_to_korean(dominant_posture)

        if not minute_summary:
            return "측정 데이터가 충분하지 않아 자세 추이 분석을 생성하지 못했습니다."

        first_score = float(minute_summary[0].get("avg_score", 0) or 0)
        last_score = float(minute_summary[-1].get("avg_score", 0) or 0)

        if len(minute_summary) == 1:
            return f"측정 구간 전반에서 {posture_kr} 자세가 주로 관찰되었습니다."

        if last_score > first_score + 3:
            return (
                f"초기 구간 대비 후반부 자세 점수가 다소 개선되었지만, "
                f"전체적으로는 {posture_kr} 자세 경향이 유지되었습니다."
            )

        if last_score < first_score - 3:
            return (
                f"초기 구간 대비 후반부 자세 점수가 다소 저하되었으며, "
                f"전반적으로 {posture_kr} 자세가 지속되었습니다."
            )

        return f"측정 전반에서 {posture_kr} 자세가 지속되었습니다."

    def _build_exercise_recommendations(self, dominant_posture: str) -> List[str]:
        exercise_map = {
            "turtle_neck": [
                "턱 당기기 스트레칭",
                "어깨 열기 스트레칭",
                "벽 자세 교정",
            ],
            "forward_lean": [
                "허리 신전 스트레칭",
                "플랭크",
                "고관절 스트레칭",
            ],
            "reclined": [
                "골반 세우기 연습",
                "코어 안정화 운동",
                "흉추 신전 스트레칭",
            ],
            "side_slouch": [
                "좌우 균형 스트레칭",
                "측면 코어 운동",
                "골반 정렬 스트레칭",
            ],
            "leg_cross_suspect": [
                "고관절 균형 스트레칭",
                "햄스트링 스트레칭",
                "골반 정렬 운동",
            ],
            "thinking_pose": [
                "턱 괴기 교정 스트레칭",
                "목 측면 스트레칭",
                "어깨 이완 운동",
            ],
            "perching": [
                "골반 후방 안정화 운동",
                "엉덩이 스트레칭",
                "허벅지 전면 스트레칭",
            ],
            "normal": [
                "가벼운 목 스트레칭",
                "어깨 회전 운동",
                "주기적 기립 휴식",
            ],
        }

        return exercise_map.get(
            dominant_posture,
            ["목 스트레칭", "어깨 스트레칭", "바른 자세 재정렬"],
        )

    def _score_level_text(self, avg_score: float) -> str:
        if avg_score >= 90:
            return "우수"
        if avg_score >= 75:
            return "양호"
        if avg_score >= 60:
            return "주의 필요"
        return "개선 필요"

    def _posture_to_korean(self, posture: str) -> str:
        posture_map = {
            "normal": "정자세",
            "turtle_neck": "거북목",
            "forward_lean": "상체 전방 기울기",
            "reclined": "기대앉기",
            "side_slouch": "측면 쏠림",
            "leg_cross_suspect": "다리 꼬기 의심",
            "thinking_pose": "턱 괴기 자세",
            "perching": "걸터앉기",
        }
        return posture_map.get(posture, posture)