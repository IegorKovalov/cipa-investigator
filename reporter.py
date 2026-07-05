"""
Generates a law-firm-ready PDF evidence package from classified CIPA findings.
Written for attorneys, not engineers.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image
)


DARK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#c0392b")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MID_GRAY = colors.HexColor("#999999")


def _styles():
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, textColor=DARK, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11, textColor=MID_GRAY, spaceAfter=4),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=13, textColor=ACCENT, spaceBefore=16, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, textColor=DARK, spaceAfter=6, leading=15),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=10, textColor=DARK, spaceAfter=2),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=MID_GRAY, spaceAfter=4),
        "finding_title": ParagraphStyle("finding_title", fontName="Helvetica-Bold", fontSize=11, textColor=DARK, spaceAfter=4),
        "warning": ParagraphStyle("warning", fontName="Helvetica-Bold", fontSize=10, textColor=ACCENT, spaceAfter=4),
    }


def generate(findings: dict, screenshots: dict, output_path: str) -> str:
    """Generate the PDF evidence package. Returns the output path."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    s = _styles()
    story = []
    summary = findings["summary"]

    # Cover
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("CIPA VIOLATION EVIDENCE PACKAGE", s["title"]))
    story.append(Paragraph(f"Prepared: {findings['scan_date']}", s["subtitle"]))
    story.append(Paragraph(f"Target: {findings['url']}", s["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))

    # Executive Summary box
    total = summary["total_trackers"]
    wt = summary["wiretap_count"]
    pr = summary["pen_register_count"]
    # Three-state consent label. 'too_late' means a banner exists but does
    # not gate the trackers — still adverse, so it reads red like 'NO'.
    consent_status = findings.get("consent_analysis", {}).get("status")
    if consent_status == "present":
        consent_label, consent_adverse = "YES", False
    elif consent_status == "too_late":
        consent_label, consent_adverse = "PRESENT BUT NON-BLOCKING", True
    else:  # 'absent' or missing
        consent_label, consent_adverse = "NO", True
    consent_value = Paragraph(consent_label, ParagraphStyle(
        "consent_val", fontName="Helvetica", fontSize=10, leading=12,
        textColor=ACCENT if consent_adverse else DARK,
    ))

    summary_data = [
        ["Trackers Identified", str(total)],
        ["§631 Wiretap Violations", str(wt)],
        ["§638.51 Pen Register Violations", str(pr)],
        ["Consent Mechanism Present", consent_value],
    ]
    confidence = findings.get("confidence")
    if confidence:
        summary_data.append([
            "Case Confidence Score",
            f"{confidence['score']}/100 ({confidence['tier'].upper()})",
        ])
    summary_table = Table(summary_data, colWidths=[3.5 * inch, 1.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (1, 2), (1, 2), ACCENT if wt > 0 else DARK),
        ("TEXTCOLOR", (1, 3), (1, 3), ACCENT if pr > 0 else DARK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.15 * inch))

    # Executive summary from Claude
    if findings.get("executive_summary"):
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(findings["executive_summary"], s["body"]))

    # Confidence score breakdown
    if confidence and confidence.get("breakdown"):
        story.append(Paragraph("CASE CONFIDENCE ASSESSMENT", s["section"]))
        rows = [[item["reason"], f"{item['points']:+d}"] for item in confidence["breakdown"]]
        rows.append(["TOTAL", f"{confidence['score']}/100"])
        ct = Table(rows, colWidths=[4.5 * inch, 1.0 * inch])
        ct.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ct)

    # Consent Analysis
    story.append(Paragraph("CONSENT ANALYSIS", s["section"]))
    consent = findings["consent_analysis"]
    if consent["status"] == "absent":
        story.append(Paragraph("FINDING: No Consent Mechanism Detected", s["warning"]))
    elif consent["status"] == "too_late":
        story.append(Paragraph("FINDING: Tracking Preceded Consent Opportunity", s["warning"]))
    else:
        story.append(Paragraph("FINDING: Consent Banner Present", s["label"]))
    story.append(Paragraph(consent["explanation"], s["body"]))

    # Screenshot — initial page state
    if "initial" in screenshots:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Initial page state at time of scan:", s["small"]))
        img_path = _save_screenshot(screenshots["initial"], "initial")
        if img_path:
            story.append(Image(img_path, width=6 * inch, height=3 * inch))

    # Wiretap Findings
    if findings["wiretap"]:
        story.append(PageBreak())
        story.append(Paragraph("§631 WIRETAP VIOLATIONS", s["section"]))
        story.append(Paragraph(
            "The following third-party tools were found intercepting the contents of user communications "
            "in real time without all-party consent, in violation of California Penal Code §631(a).",
            s["body"]
        ))
        for i, f in enumerate(findings["wiretap"], 1):
            _add_finding(story, f, i, s)

    # Pen Register Findings
    if findings["pen_register"]:
        story.append(PageBreak())
        story.append(Paragraph("§638.51 PEN REGISTER VIOLATIONS", s["section"]))
        story.append(Paragraph(
            "The following third-party tools were found recording routing, addressing, and signaling "
            "information from user sessions without court order or valid consent, in violation of "
            "California Penal Code §638.51(a).",
            s["body"]
        ))
        for i, f in enumerate(findings["pen_register"], 1):
            _add_finding(story, f, i, s)

    # Technical Appendix
    story.append(PageBreak())
    story.append(Paragraph("TECHNICAL APPENDIX — REQUEST LOG", s["section"]))
    story.append(Paragraph(
        "The following table documents all third-party tracker network requests captured during the scan session.",
        s["body"]
    ))

    all_findings = findings["wiretap"] + findings["pen_register"]
    if all_findings:
        rows = [["Tracker", "Statute", "First Seen", "Requests", "Domain"]]
        for f in all_findings:
            rows.append([
                f["tracker_name"],
                f["statute"].replace("Cal. Penal Code ", ""),
                f"{f['first_seen_seconds']}s",
                str(f["request_count"]),
                f["domain"],
            ])
        t = Table(rows, colWidths=[1.5*inch, 1.2*inch, 0.9*inch, 0.7*inch, 2.2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))
    story.append(Paragraph(
        "This evidence package was generated by automated technical analysis. "
        "All findings are based on observed network behavior and should be reviewed by qualified legal counsel.",
        s["small"]
    ))

    doc.build(story)
    _cleanup_screenshots()
    return output_path


def _add_finding(story, f, index, s):
    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
    story.append(Paragraph(f"{index}. {f['tracker_name']} — {f['domain']}", s["finding_title"]))

    meta = [
        ["Statute", f["statute"]],
        ["First Detected", f"{f['first_seen_seconds']}s after page load"],
        ["Total Requests", str(f["request_count"])],
    ]
    t = Table(meta, colWidths=[1.5 * inch, 5 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Paragraph(f["legal_basis"], s["body"]))
    story.append(Paragraph(f["consent_note"], s["small"]))


_temp_screenshots = []

def _save_screenshot(png_bytes: bytes, name: str) -> str | None:
    if not png_bytes or len(png_bytes) < 100:
        return None
    try:
        path = f"/tmp/cipa_screenshot_{name}.png"
        with open(path, "wb") as f:
            f.write(png_bytes)
        _temp_screenshots.append(path)
        return path
    except:
        return None

def _cleanup_screenshots():
    for path in _temp_screenshots:
        try:
            os.remove(path)
        except:
            pass
