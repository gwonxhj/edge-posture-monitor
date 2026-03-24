from src.config.settings import REPORT_ENGINE
from src.report.report_enhancer import ReportEnhancer
from src.report.llm_report_engine import LLMReportEngine

class ReportService:
    """
    최종 리포트 생성 진입점

    지원 엔진:
    - rule: 기존 rule-based enhancer
    - llm : 향후 실제 LLM으로 교체될 LLM-ready 엔진

    주의:
    두 엔진 모두 동일한 최종 출력 schema를 유지해야 한다.
    """

    def __init__(self):
        self.engine = REPORT_ENGINE

    def build_enhanced_report(self, overall_summary, minute_summary):
        if self.engine == "rule":
            enhancer = ReportEnhancer()
            return enhancer.build_enhanced_report(
                overall_summary=overall_summary,
                minute_summary=minute_summary,
            )
        
        if self.engine == "llm":
            enhancer = LLMReportEngine()
            return enhancer.build_enhanced_report(
                overall_summary=overall_summary,
                minute_summary=minute_summary,
            )
        
        raise ValueError(f"Unsupported report engine: {self.engine}")