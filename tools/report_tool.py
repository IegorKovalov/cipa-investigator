"""
PDF report generation tool — validates Claude-authored findings and
hands them to the existing ReportLab generator (reporter.py).
"""

from datetime import datetime

from reporter import generate

FINDING_KEYS = {
    "tracker_name", "domain", "statute", "first_seen_seconds",
    "request_count", "legal_basis", "consent_note", "sample_url",
}


def build_report(findings: dict, screenshots: dict, output_path: str) -> str:
    for key in ("url", "wiretap", "pen_register", "consent_analysis"):
        if key not in findings:
            raise ValueError(f"findings missing required key: '{key}'")
    if findings["consent_analysis"].get("status") not in ("absent", "too_late", "present"):
        raise ValueError("consent_analysis.status must be 'absent', 'too_late', or 'present'")
    if "explanation" not in findings["consent_analysis"]:
        raise ValueError("consent_analysis missing 'explanation'")

    for section in ("wiretap", "pen_register"):
        for f in findings[section]:
            missing = FINDING_KEYS - set(f)
            if missing:
                raise ValueError(f"{section} finding '{f.get('tracker_name', '?')}' missing keys: {sorted(missing)}")

    findings.setdefault("scan_date", datetime.now().strftime("%B %d, %Y"))
    findings.setdefault("summary", {})
    findings["summary"].setdefault("total_trackers", len(findings["wiretap"]) + len(findings["pen_register"]))
    findings["summary"].setdefault("wiretap_count", len(findings["wiretap"]))
    findings["summary"].setdefault("pen_register_count", len(findings["pen_register"]))
    findings["summary"].setdefault("no_consent_mechanism", findings["consent_analysis"]["status"] == "absent")
    findings["summary"].setdefault("trackers_before_banner", 0)

    return generate(findings, screenshots, output_path)
