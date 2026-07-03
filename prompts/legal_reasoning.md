# Legal Reasoning — Mapping Evidence to Statutes

## §631 — Wiretap (contents)

A third party intercepts the CONTENTS of user communications in real time.
The touchstone: does the tool receive what the user *said or typed*, or a
reconstruction of it?

Qualifies: session replay (keystroke/mouse/form capture), third-party live
chat (the vendor's servers carry the user's messages), search-term capture,
form-field harvesting.

Evidence that makes it concrete: POST requests to the vendor firing DURING
typing (use `type_text` and watch the log), the vendor's script recording
before any consent.

## §638.51 — Pen register (routing metadata)

A third party records ROUTING, ADDRESSING, or SIGNALING information:
URLs visited, navigation sequence, referrers, session/device identifiers.
Ad pixels and analytics are the archetypes (Meta Pixel, GA4, TikTok,
LinkedIn Insight). The tool doesn't need message contents — the pattern
of where the user went is the violation.

## Not violations — do not include

CDNs, font/asset hosts, payment processors doing payment, first-party
subdomains, tag managers alone (but what they LOAD may violate — attribute
findings to the loaded tracker, not the manager), captcha/anti-fraud
(context-dependent; exclude unless it demonstrably profiles navigation).
When genuinely uncertain about an unknown host after `lookup_tracker` and
reasoning about the vendor, leave it out of findings and mention it in the
executive summary as unresolved. Over-claiming weakens the package.

## Findings JSON schema (for generate_report)

```json
{
  "url": "https://target.com",
  "executive_summary": "2-4 sentences for an attorney: what was found, how strong the case is, what makes it actionable.",
  "consent_analysis": {
    "status": "absent | too_late | present",
    "explanation": "Plain-English timing analysis with concrete seconds and counts."
  },
  "wiretap": [
    {
      "tracker_name": "Hotjar",
      "domain": "hotjar.com",
      "statute": "Cal. Penal Code §631",
      "first_seen_seconds": 2.1,
      "request_count": 14,
      "legal_basis": "What the tool does, what it transmitted, why that satisfies the statute's elements — written for an attorney.",
      "consent_note": "Where this tracker's first request falls relative to the consent timeline.",
      "sample_url": "https://script.hotjar.com/..."
    }
  ],
  "pen_register": [ { "...same shape, statute §638.51": "" } ],
  "confidence": { "score": 87, "tier": "strong", "breakdown": [] }
}
```

`confidence` comes verbatim from `score_confidence`. Timestamps and counts
must match the session's network log exactly — attorneys will check.

## Narrative voice

Attorney-facing, factual, specific: "At 2.1 seconds after page load —
before any consent mechanism appeared — Hotjar's script began transmitting
form input to script.hotjar.com." Never speculative ("may", "could
potentially") in the legal_basis; if it's speculative, it doesn't belong
in findings.
