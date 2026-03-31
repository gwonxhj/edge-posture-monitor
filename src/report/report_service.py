from src.report.llm_report_engine import LLMReportEngine


class ReportService:

    def __init__(self):
        self.engine = LLMReportEngine()

    def build_enhanced_report(self, overall_summary, minute_summary):
        return self.engine.build_enhanced_report(
            overall_summary=overall_summary,
            minute_summary=minute_summary,
        )