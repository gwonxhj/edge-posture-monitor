# src/report/llm_report_engine.py

import json
import time
from typing import Any, Dict, List

from src.config.settings import (
    LLM_REPORT_MODE,
    LLM_MODEL_BACKEND,
    LLM_GGUF_MODEL_PATH,
    LLM_CONTEXT_LEN,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)

POSTURE_LABEL_KR = {
    "turtle_neck": "거북목 성향",
    "forward_lean": "몸통 전방 기울어짐",
    "side_slouch": "좌우 비대칭 기울어짐",
    "leg_cross_suspect": "하체 좌우 불균형 의심",
    "thinking_pose": "책상 앞 숙임 자세",
    "reclined": "뒤로 기대는 자세",
    "perching": "의자 끝에 걸터앉은 자세",
    "normal": "비교적 안정적인 자세",
}


class LLMReportEngine:
    def __init__(self):
        self.model = None
        if LLM_REPORT_MODE == "live":
            self._load_model()

    def _load_model(self):
        try:
            from llama_cpp import Llama
            if not LLM_GGUF_MODEL_PATH:
                print("[LLM] ERROR: LLM_GGUF_MODEL_PATH is empty")
                return
            print(f"[LLM] Loading model: {LLM_GGUF_MODEL_PATH} ...")
            load_start = time.time()
            self.model = Llama(
                model_path=LLM_GGUF_MODEL_PATH,
                n_ctx=4096,
                n_threads=4,
                verbose=False,
            )
            print(f"[LLM] Model loaded in {time.time()-load_start:.1f}s")
        except ImportError:
            print("[LLM] llama-cpp-python not installed. Run: pip install llama-cpp-python")
            self.model = None
        except Exception as e:
            print(f"[LLM] Model load failed: {e}")
            self.model = None

    def build_enhanced_report(self, overall_summary, minute_summary):
        prompt = self._build_prompt(overall_summary, minute_summary)
        print("[LLM] Generating report...")
        gen_start = time.time()
        raw_output = self._call_model(prompt)
        elapsed = time.time() - gen_start
        print(f"[LLM] Report generated in {elapsed:.1f}s")
        print(f"[LLM] Raw output: {raw_output[:200]}...")
        return self._parse_output(raw_output, overall_summary)

    def _build_prompt(self, overall_summary, minute_summary):
        oj = json.dumps(overall_summary, ensure_ascii=False, indent=2)
        mj = json.dumps(minute_summary, ensure_ascii=False, indent=2)

        dominant = overall_summary.get("dominant_posture", "normal")
        dominant_kr = POSTURE_LABEL_KR.get(dominant, dominant)
        avg_score = overall_summary.get("avg_score", 0)
        total_sec = overall_summary.get("total_sitting_sec", 0)
        bad_ratio = overall_summary.get("bad_posture_ratio", 0)
        durations = overall_summary.get("posture_duration_sec", {})

        duration_lines = []
        for k, v in durations.items():
            if v > 0:
                kr = POSTURE_LABEL_KR.get(k, k)
                pct = (v / total_sec * 100) if total_sec > 0 else 0
                duration_lines.append(f"  - {kr}: {v:.1f}초 ({pct:.1f}%)")

        duration_text = "\n".join(duration_lines) if duration_lines else "  데이터 없음"

        system_msg = (
            "당신은 자세 교정 전문가입니다. "
            "센서 측정 데이터를 분석하여 사용자의 앉는 습관을 진단하고, "
            "구체적이고 실용적인 교정 피드백을 제공합니다. "
            "의학적 진단은 하지 않으며, 자세 경향과 생활 습관 교정에 집중합니다."
        )

        user_msg = (
            "아래는 의자에 앉아있는 동안 측정된 자세 분석 데이터입니다.\n\n"
            f"측정 시간: {total_sec:.0f}초 ({total_sec/60:.1f}분)\n"
            f"평균 점수: {avg_score:.1f}점 (100점 만점)\n"
            f"주요 자세: {dominant_kr}\n"
            f"나쁜 자세 비율: {bad_ratio:.1f}%\n\n"
            f"자세별 지속 시간:\n{duration_text}\n\n"
            f"분 단위 요약:\n{mj}\n\n"
            "위 데이터를 바탕으로 아래 JSON 형식으로 자세 분석 리포트를 작성해주세요.\n"
            "반드시 JSON만 출력하고, 마크다운이나 설명 텍스트는 포함하지 마세요.\n\n"
            "조건:\n"
            "- posture_analysis: 전체 자세 분석 (3~5문장, 어떤 자세가 얼마나 관찰되었는지, 어떤 문제가 있는지 구체적으로)\n"
            "- trend_analysis: 시간 흐름에 따른 자세 변화 추세 분석 (2~3문장, 초반/중반/후반 비교)\n"
            "- exercise_recommendations: 관찰된 자세에 맞는 구체적인 교정 운동 3개 (운동 이름과 간단한 방법 포함)\n"
            "- summary: 종합 요약 및 생활 습관 개선 조언 (2~3문장)\n\n"
            '{"posture_analysis": "...", "trend_analysis": "...", "exercise_recommendations": ["...", "...", "..."], "summary": "..."}'
        )

        return (
            "<|im_start|>system\n" + system_msg + "<|im_end|>\n"
            "<|im_start|>user\n" + user_msg + "<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    def _call_model(self, prompt):
        if LLM_REPORT_MODE == "mock":
            return self._mock_response(prompt)
        if LLM_REPORT_MODE == "live":
            return self._call_llama_cpp_python(prompt)
        raise ValueError(f"Unsupported LLM report mode: {LLM_REPORT_MODE}")

    def _call_llama_cpp_python(self, prompt):
        if self.model is None:
            print("[LLM] Model not loaded, falling back to rule-based")
            return ""
        try:
            output = self.model(
                prompt,
                max_tokens=1024,
                temperature=0.3,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["<|im_end|>", "<|im_start|>"],
            )
            text = output["choices"][0]["text"].strip()
            if "{" in text and not text.rstrip().endswith("}"):
                text = text.rstrip() + "}"
            print(f"[LLM] Raw output length: {len(text)} chars")
            return text
        except Exception as e:
            print(f"[LLM] Inference failed: {e}")
            return ""

    def _mock_response(self, prompt):
        return json.dumps({
            "posture_analysis": "전체 평균 점수는 양호하며, 주요 자세 경향이 관찰되었습니다.",
            "trend_analysis": "측정 전반에서 특정 자세가 비교적 지속적으로 관찰되었습니다.",
            "exercise_recommendations": [
                "턱 당기기 스트레칭 (chin tuck)",
                "어깨 열기 스트레칭",
                "벽 기대 자세 교정",
            ],
            "summary": "자세 패턴이 확인되어 생활 습관 교정이 권장됩니다.",
        }, ensure_ascii=False)

    def _parse_output(self, raw_output, overall_summary=None):
        overall_summary = overall_summary or {}
        posture = overall_summary.get("dominant_posture", "normal")
        posture_kr = POSTURE_LABEL_KR.get(posture, posture)
        parsed_data = None
        if raw_output:
            try:
                parsed_data = json.loads(raw_output)
            except json.JSONDecodeError:
                start = raw_output.find("{")
                end = raw_output.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        parsed_data = json.loads(raw_output[start:end+1])
                    except json.JSONDecodeError:
                        pass
        if parsed_data is None:
            print("[LLM] JSON parsing failed, using rule-based fallback")
            return self._rule_based_fallback(overall_summary)
        pa = str(parsed_data.get("posture_analysis", parsed_data.get("summary_text", ""))).strip()
        ta = str(parsed_data.get("trend_analysis", parsed_data.get("trend_text", ""))).strip()
        sm = str(parsed_data.get("summary", "")).strip()
        ex = parsed_data.get("exercise_recommendations", [])
        if not isinstance(ex, list):
            ex = []
        ex = [str(x).strip() for x in ex if str(x).strip()][:3]
        while len(ex) < 3:
            ex.append("바른 자세 재정렬")
        if not pa:
            pa = f"주요 자세는 {posture_kr}이며, 자세 데이터 분석이 완료되었습니다."
        if not ta:
            ta = "시간 흐름에 따른 자세 변화 추이가 확인되었습니다."
        if not sm:
            sm = f"{posture_kr} 중심의 자세 패턴이 확인되어 생활 습관 교정이 권장됩니다."
        return {
            "summary_text": pa,
            "trend_text": ta,
            "exercise_recommendations": ex,
            "summary": sm,
        }

    def _rule_based_fallback(self, overall_summary):
        posture = overall_summary.get("dominant_posture", "normal")
        posture_kr = POSTURE_LABEL_KR.get(posture, posture)
        avg_score = overall_summary.get("avg_score", 0)
        bad_ratio = overall_summary.get("bad_posture_ratio", 0)
        total_sec = overall_summary.get("total_sitting_sec", 0)
        durations = overall_summary.get("posture_duration_sec", {})

        bad_postures = []
        for k, v in durations.items():
            if k != "normal" and v > 0:
                kr = POSTURE_LABEL_KR.get(k, k)
                pct = (v / total_sec * 100) if total_sec > 0 else 0
                bad_postures.append(f"{kr} {v:.0f}초({pct:.0f}%)")

        bad_detail = ", ".join(bad_postures) if bad_postures else "없음"

        exercise_map = {
            "turtle_neck": [
                "턱 당기기 스트레칭 (chin tuck) - 턱을 목 쪽으로 당기고 10초 유지, 10회 반복",
                "어깨 열기 스트레칭 - 양팔을 뒤로 벌려 가슴을 열고 15초 유지",
                "벽 기대 자세 교정 - 벽에 등과 머리를 붙이고 1분간 유지",
            ],
            "forward_lean": [
                "허리 신전 스트레칭 - 엎드려 상체를 들어올리고 15초 유지",
                "코어 강화 플랭크 - 30초씩 3세트",
                "고관절 펴기 스트레칭 - 런지 자세에서 앞쪽 고관절 15초 이완",
            ],
            "side_slouch": [
                "좌우 균형 스트레칭 - 양쪽으로 번갈아 측면 스트레칭 15초씩",
                "측면 코어 운동 - 사이드 플랭크 20초씩 좌우 3세트",
                "골반 정렬 스트레칭 - 바닥에 누워 무릎을 좌우로 교대 눕히기",
            ],
            "leg_cross_suspect": [
                "고관절 좌우 밸런스 스트레칭 - 나비 자세로 양쪽 고관절 이완 30초",
                "골반 정렬 운동 - 브릿지 자세 10회씩 3세트",
                "햄스트링 이완 스트레칭 - 한 다리씩 펴서 발끝 잡기 15초",
            ],
            "thinking_pose": [
                "목-등 상부 스트레칭 - 고개를 좌우로 천천히 기울이기 10초씩",
                "어깨 후인 자세 연습 - 어깨를 뒤로 모으고 10초 유지",
                "흉추 가동성 운동 - 의자에 앉아 상체 좌우 회전 10회",
            ],
            "reclined": [
                "골반 세우기 연습 - 좌골로 앉는 감각 익히기",
                "복부 긴장 유지 운동 - 앉은 상태에서 배에 힘주고 10초 유지 반복",
                "허리 중립자세 연습 - 수건을 허리에 대고 등받이 활용",
            ],
            "perching": [
                "엉덩이 깊게 앉기 연습 - 의자 안쪽까지 엉덩이를 밀어넣기",
                "코어 브레이싱 운동 - 배에 힘을 주고 바른 자세 30초 유지",
                "고관절 안정화 운동 - 의자에 앉아 한 다리씩 들어올리기 10회",
            ],
        }
        exercises = exercise_map.get(posture, [
            "목 스트레칭 - 고개를 좌우 앞뒤로 천천히 10초씩",
            "어깨 스트레칭 - 양팔을 머리 위로 올려 15초 유지",
            "골반 정렬 운동 - 브릿지 자세 10회씩 3세트",
        ])

        return {
            "summary_text": (
                f"총 {total_sec:.0f}초 측정 중 평균 점수 {avg_score:.1f}점입니다. "
                f"주요 자세는 {posture_kr}이며, 나쁜 자세 비율은 {bad_ratio:.1f}%입니다. "
                f"관찰된 나쁜 자세: {bad_detail}."
            ),
            "trend_text": f"측정 기간 동안 {posture_kr}이(가) 가장 많이 관찰되었으며, 자세 교정 습관이 필요합니다.",
            "exercise_recommendations": exercises,
            "summary": f"{posture_kr} 중심의 자세 패턴이 확인되었습니다. 위 운동을 매일 2~3회 실시하여 자세를 개선해보세요.",
        }