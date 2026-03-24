# src/report/llm_report_engine.py

import json
import subprocess
from typing import Any, Dict, List

from src.config.settings import (
    LLM_REPORT_MODE,
    LLM_MODEL_BACKEND,
    LLM_GGUF_MODEL_PATH,
    LLM_CONTEXT_LEN,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)


class LLMReportEngine:
    """
    llama.cpp + GGUF 연결을 위한 LLM-ready report engine.

    현재 단계:
    - REPORT_ENGINE=llm 으로 실행 가능
    - LLM_REPORT_MODE=mock 일 때는 실제 모델 호출 없이 동작

    향후 단계:
    - LLM_REPORT_MODE=live
    - llama.cpp subprocess 호출로 GGUF 모델 실행
    """

    def build_enhanced_report(
        self,
        overall_summary: Dict[str, Any],
        minute_summary: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(
            overall_summary=overall_summary,
            minute_summary=minute_summary,
        )

        raw_output = self._call_model(prompt)
        parsed = self._parse_output(raw_output)

        return parsed

    def _build_prompt(
        self,
        overall_summary: Dict[str, Any],
        minute_summary: List[Dict[str, Any]],
    ) -> str:
        payload = {
            "overall_summary": overall_summary,
            "minute_summary": minute_summary,
        }

        return f"""
당신은 자세 교정 리포트를 작성하는 전문가입니다.

아래 측정 요약 데이터를 바탕으로 반드시 JSON만 출력하세요.
설명 문장, 마크다운, 코드블록 없이 JSON 객체만 반환하세요.

출력 형식:
{{
  "summary_text": "문자열",
  "trend_text": "문자열",
  "exercise_recommendations": ["문자열", "문자열", "문자열"]
}}

조건:
- 한국어로 작성
- summary_text는 전체 요약 1~2문장
- trend_text는 시간 흐름 관점의 자세 변화 설명 1문장
- exercise_recommendations는 정확히 3개
- dominant_posture와 bad_posture_ratio를 반영
- 과장 없이 보수적으로 작성

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    def _call_model(self, prompt: str) -> str:
        if LLM_REPORT_MODE == "mock":
            return self._mock_response(prompt)

        if LLM_REPORT_MODE == "live":
            if LLM_MODEL_BACKEND != "llama_cpp":
                raise ValueError(f"Unsupported LLM backend: {LLM_MODEL_BACKEND}")
            return self._call_llama_cpp(prompt)

        raise ValueError(f"Unsupported LLM report mode: {LLM_REPORT_MODE}")

    def _mock_response(self, prompt: str) -> str:
        return json.dumps(
            {
                "summary_text": "전체 평균 점수는 95.0점대로 양호하며, 주요 자세는 거북목 경향으로 보입니다.",
                "trend_text": "측정 전반에서 거북목 자세가 비교적 지속적으로 관찰되었습니다.",
                "exercise_recommendations": [
                    "턱 당기기 스트레칭",
                    "어깨 열기 스트레칭",
                    "벽 자세 교정",
                ],
            },
            ensure_ascii=False,
        )

    def _call_llama_cpp(self, prompt: str) -> str:
        if not LLM_GGUF_MODEL_PATH:
            raise ValueError("LLM_GGUF_MODEL_PATH is empty")

        # 나중에 실제 llama.cpp 바이너리 경로로 맞출 예정
        # 예: /home/risepi02/llama.cpp/build/bin/llama-cli
        llama_cli_path = "/home/risepi02/llama.cpp/build/bin/llama-cli"

        cmd = [
            llama_cli_path,
            "-m",
            LLM_GGUF_MODEL_PATH,
            "-c",
            str(LLM_CONTEXT_LEN),
            "-n",
            str(LLM_MAX_TOKENS),
            "--temp",
            str(LLM_TEMPERATURE),
            "-p",
            prompt,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    def _parse_output(self, raw_output: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw_output)
        except Exception:
            return {
                "summary_text": "LLM 리포트 생성 중 출력 파싱에 실패하여 기본 요약으로 대체되었습니다.",
                "trend_text": "측정 추이를 해석하는 과정에서 오류가 발생했습니다.",
                "exercise_recommendations": [
                    "목 스트레칭",
                    "어깨 스트레칭",
                    "바른 자세 재정렬",
                ],
            }

        summary_text = str(data.get("summary_text", "")).strip()
        trend_text = str(data.get("trend_text", "")).strip()
        exercise_recommendations = data.get("exercise_recommendations", [])

        if not isinstance(exercise_recommendations, list):
            exercise_recommendations = []

        exercise_recommendations = [
            str(x).strip() for x in exercise_recommendations if str(x).strip()
        ][:3]

        while len(exercise_recommendations) < 3:
            exercise_recommendations.append("바른 자세 재정렬")

        if not summary_text:
            summary_text = "측정 요약을 생성하지 못했습니다."

        if not trend_text:
            trend_text = "자세 추이 설명을 생성하지 못했습니다."

        return {
            "summary_text": summary_text,
            "trend_text": trend_text,
            "exercise_recommendations": exercise_recommendations,
        }