"""
Reference tools: tracker classification lookup and case confidence scoring.

Both are deliberately deterministic. A legal deliverable must be
reproducible — the same evidence always yields the same classification
and the same score. Claude's judgment goes into WHAT evidence to gather
and the narratives, not into the arithmetic.
"""

from urllib.parse import urlparse

from trackers import get_tracker

# Trackers with established CIPA litigation history — strengthens the case
LITIGATED_TRACKERS = {
    "Meta Pixel", "Meta", "Hotjar", "FullStory", "Microsoft Clarity",
    "Mouseflow", "TikTok Pixel", "TikTok Analytics", "Google Analytics",
    "LinkedIn Insight", "Snapchat Pixel",
}


def lookup(domain_or_url: str) -> dict:
    url = domain_or_url if "://" in domain_or_url else f"https://{domain_or_url}/"
    host = urlparse(url).hostname or domain_or_url
    info = get_tracker(url)
    if info:
        return {
            "known": True,
            "host": host,
            "name": info["name"],
            "type": info["type"],
            "statute": "Cal. Penal Code §631" if info["type"] == "wiretap" else "Cal. Penal Code §638.51",
            "description": info["description"],
            "litigation_history": info["name"] in LITIGATED_TRACKERS,
        }
    return {
        "known": False,
        "host": host,
        "guidance": (
            "Not in the known-tracker database. Reason about the vendor's product: "
            "session replay / live chat / keystroke capture = wiretap (§631); "
            "analytics / advertising pixel / navigation tracking = pen register (§638.51); "
            "CDN, fonts, payment processors, or first-party infrastructure = likely no violation."
        ),
    }


def score_confidence(
    wiretap_count: int,
    pen_register_count: int,
    consent_status: str,
    total_tracker_requests: int,
    litigated_tracker_present: bool,
    visitor_simulated_in_california: bool = True,
) -> dict:
    """Case confidence score 0-100 with an itemized breakdown.

    consent_status: 'absent' (no banner at any point), 'too_late'
    (trackers fired before the banner appeared), or 'present'
    (banner appeared before any tracker fired).
    """
    breakdown = []
    score = 0

    if wiretap_count > 0:
        score += 40
        breakdown.append({"points": 40, "reason": f"§631 wiretap violation confirmed ({wiretap_count} tracker(s))"})

    consent_points = {"absent": 25, "too_late": 15, "present": 0}
    if consent_status not in consent_points:
        raise ValueError("consent_status must be 'absent', 'too_late', or 'present'")
    pts = consent_points[consent_status]
    if pts:
        label = "No consent mechanism" if consent_status == "absent" else "Trackers fired before consent banner"
        score += pts
        breakdown.append({"points": pts, "reason": label})

    if pen_register_count > 0:
        pts = min(round(pen_register_count * 2.5), 15)
        score += pts
        breakdown.append({"points": pts, "reason": f"{pen_register_count} pen register violation(s) (§638.51)"})

    if total_tracker_requests >= 100:
        volume_pts = 7
    elif total_tracker_requests >= 40:
        volume_pts = 5
    elif total_tracker_requests >= 15:
        volume_pts = 3
    else:
        volume_pts = 0
    if volume_pts:
        score += volume_pts
        breakdown.append({"points": volume_pts, "reason": f"High request volume ({total_tracker_requests} tracker requests)"})

    if litigated_tracker_present:
        score += 10
        breakdown.append({"points": 10, "reason": "Tracker(s) with established CIPA litigation history"})

    if not visitor_simulated_in_california:
        score -= 10
        breakdown.append({"points": -10, "reason": "Deduction: visitor not simulated in California"})

    score = max(0, min(100, score))
    if score >= 75:
        tier = "strong"
    elif score >= 50:
        tier = "viable"
    else:
        tier = "weak"

    return {"score": score, "tier": tier, "breakdown": breakdown}
