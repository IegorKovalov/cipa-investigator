"""
Maps raw browser evidence to CIPA legal findings.
Each finding states which statute applies, what was captured, and why it qualifies.
"""

from datetime import datetime


def classify(evidence: dict) -> dict:
    """
    Takes raw evidence from browser.py and returns structured legal findings
    mapped to §631 (wiretap) and §638.51 (pen register).
    """
    findings = {
        "url": evidence["url"],
        "scan_date": datetime.now().strftime("%B %d, %Y"),
        "wiretap": [],       # §631 violations
        "pen_register": [],  # §638.51 violations
        "consent_analysis": _analyze_consent(evidence),
        "summary": {},
    }

    # Deduplicate by tracker name — one finding per tracker, not per request
    seen_trackers = {}
    for req in evidence["requests"]:
        tracker = req["tracker"]
        name = tracker["name"]
        if name in seen_trackers:
            seen_trackers[name]["request_count"] += 1
            seen_trackers[name]["first_seen"] = min(seen_trackers[name]["first_seen"], req["timestamp"])
        else:
            seen_trackers[name] = {
                "name": name,
                "type": tracker["type"],
                "domain": tracker["domain"],
                "description": tracker["description"],
                "first_seen": req["timestamp"],
                "request_count": 1,
                "sample_url": req["url"],
            }

    for name, tracker in seen_trackers.items():
        finding = _build_finding(tracker, evidence["consent"])
        if tracker["type"] == "wiretap":
            findings["wiretap"].append(finding)
        else:
            findings["pen_register"].append(finding)

    findings["summary"] = {
        "total_trackers": len(seen_trackers),
        "wiretap_count": len(findings["wiretap"]),
        "pen_register_count": len(findings["pen_register"]),
        "no_consent_mechanism": not evidence["consent"]["banner_detected"],
        "trackers_before_banner": len(evidence["consent"]["requests_before_banner"]),
    }

    return findings


def _analyze_consent(evidence: dict) -> dict:
    """Produces a plain-English consent analysis for the legal report."""
    consent = evidence["consent"]

    if not consent["banner_detected"]:
        status = "absent"
        explanation = (
            "No consent banner or opt-in mechanism was detected at any point during the session. "
            "All tracking activity occurred without the user being presented any opportunity to consent or refuse. "
            "Under CIPA, consent must be obtained before interception begins. "
            "A privacy policy link in the footer does not constitute valid consent."
        )
    elif consent["requests_before_banner"]:
        n = len(consent["requests_before_banner"])
        status = "too_late"
        explanation = (
            f"A consent banner was detected at {consent['banner_time']}s after page load, "
            f"but {n} tracker request(s) had already fired before the banner appeared. "
            "The user had no opportunity to consent before tracking began. "
            "CIPA requires consent prior to interception, not after."
        )
    else:
        status = "present"
        explanation = (
            f"A consent banner was detected at {consent['banner_time']}s. "
            "Trackers loaded after the banner appeared. "
            "Whether this constitutes valid consent depends on the clarity and prominence of the banner."
        )

    return {"status": status, "explanation": explanation}


def _build_finding(tracker: dict, consent: dict) -> dict:
    """Builds a single legal finding for one tracker."""
    if tracker["type"] == "wiretap":
        statute = "Cal. Penal Code §631"
        legal_basis = (
            f"{tracker['name']} operates as a third-party session replay or live communication interception tool. "
            f"Its scripts execute within the target website and transmit the contents of user communications — "
            f"including keystrokes, form inputs, and real-time interactions — to {tracker['domain']} servers. "
            f"This constitutes interception of communication contents by a third party without all-party consent, "
            f"satisfying the elements of §631(a)."
        )
    else:
        statute = "Cal. Penal Code §638.51"
        legal_basis = (
            f"{tracker['name']} functions as a pen register by recording routing, addressing, and signaling information "
            f"transmitted during the user's session — including URL paths visited, navigation sequences, referrer data, "
            f"and behavioral signals — and transmitting this information to {tracker['domain']}. "
            f"This meets the statutory definition of a pen register under §638.50(b) and its installation "
            f"without court order or valid prior consent constitutes a violation of §638.51(a)."
        )

    consent_note = ""
    if not consent["banner_detected"]:
        consent_note = "No consent mechanism was presented to the user at any point in the session."
    elif tracker["first_seen"] < (consent["banner_time"] or float("inf")):
        consent_note = f"This tracker fired at {tracker['first_seen']}s — before the consent banner appeared at {consent['banner_time']}s."
    else:
        consent_note = "Tracker loaded after consent banner appeared. Validity of consent mechanism remains subject to review."

    return {
        "tracker_name": tracker["name"],
        "domain": tracker["domain"],
        "statute": statute,
        "first_seen_seconds": tracker["first_seen"],
        "request_count": tracker["request_count"],
        "legal_basis": legal_basis,
        "consent_note": consent_note,
        "sample_url": tracker["sample_url"],
    }
