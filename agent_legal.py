"""
Legal Writer Agent — synthesizes CIPA findings into attorney-facing narratives.
Receives structured evidence and returns polished legal analysis for the PDF report.
"""

import json
import anthropic

client = anthropic.Anthropic()


def write_legal_narrative(findings: dict) -> dict:
    """
    Claude writes attorney-facing legal analysis for each violation.
    Replaces template text with reasoned legal narrative.
    Returns updated findings dict.
    """
    print("\n[Legal Writer] Writing legal narrative...")

    all_violations = findings["wiretap"] + findings["pen_register"]
    if not all_violations:
        return findings

    violations_text = ""
    for v in all_violations:
        violations_text += f"""
Tracker: {v['tracker_name']}
Domain: {v['domain']}
Statute: {v['statute']}
First detected: {v['first_seen_seconds']}s after page load
Total requests: {v['request_count']}
Sample URL: {v['sample_url']}
---"""

    consent = findings["consent_analysis"]

    prompt = f"""You are a privacy attorney drafting an evidence package for a CIPA lawsuit.

Target website: {findings['url']}
Consent status: {consent['status']} — {consent['explanation']}

The following third-party trackers were detected:
{violations_text}

For each tracker, write a concise legal analysis (3-4 sentences) explaining:
1. What the tracker does technically
2. Which specific CIPA statute element it satisfies
3. Why the absence/inadequacy of consent makes this actionable

Write in attorney language — precise, factual, no hedging. Do not use bullet points.
Reference the specific statute section (§631(a) or §638.51(a)) in each analysis.

Respond with JSON only:
{{
  "narratives": {{
    "TrackerName": "legal analysis text...",
    ...
  }},
  "executive_summary": "2-3 sentence summary of the overall violation pattern for the cover page"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        result = json.loads(text)

        narratives = result.get("narratives", {})
        for violation in findings["wiretap"] + findings["pen_register"]:
            name = violation["tracker_name"]
            if name in narratives:
                violation["legal_basis"] = narratives[name]

        findings["executive_summary"] = result.get("executive_summary", "")
        print(f"    [Legal Writer] Narrative written for {len(narratives)} trackers")

    except Exception as e:
        print(f"    [Legal Writer] Narrative generation error: {e} — keeping template text")

    return findings
