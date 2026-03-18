def build_final_report_payload(
    overall_summary,
    minute_summary,
    enhanced_report,
):
    return {
        "overall_summary": overall_summary,
        "minute_summary": minute_summary,
        "enhanced_report": enhanced_report,
    }