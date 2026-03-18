from src.config.settings import REPORT_ENGINE
from src.report.report_enhancer import ReportEnhancer


class ReportService:
    """
    최종 리포트 생성 진입점.
    현재는 rule-based enhancer를 사용하고,
    향후 LLM 기반 enhancer로 확장 가능하도록 설계.
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

        # 향후 LLM 리포트 엔진 확장 포인트
        raise ValueError(f"Unsupported report engine: {self.engine}")