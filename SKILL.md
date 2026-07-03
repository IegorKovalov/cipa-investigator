---
name: cipa-investigator
description: Scans a website for California Invasion of Privacy Act (CIPA) violations and generates a law-firm-ready PDF evidence package. Use when asked to investigate a website for privacy violations, tracking, wiretap, or pen register issues.
---

# CIPA Investigator

Investigates a website for CIPA violations (§631 wiretap, §638.51 pen
register) and produces a litigation-ready PDF evidence package with a
case confidence score.

## How to run an investigation

You are the investigator. Use the `cipa-investigator` MCP tools
(`start_investigation`, `take_screenshot`, `navigate`, `get_network_log`,
`lookup_tracker`, `score_confidence`, `generate_report`, ...).

**Before starting, read these three files — they are the methodology:**

1. `prompts/orchestrator.md` — investigation flow and stopping criteria
2. `prompts/consent_analysis.md` — how to reason about consent timing
3. `prompts/legal_reasoning.md` — statute mapping + findings JSON schema

Then: `start_investigation(url)` → document the pre-consent state →
walk communication surfaces (forms, chat, search) → classify every
third-party host → `score_confidence` → write the narratives →
`generate_report` → `end_investigation`.

There is no fixed iteration count — you decide when the evidence is
sufficient. Every claim must trace to a timestamped request or screenshot
from the session.

## Output

`evidence_package.pdf`:
- Executive summary + violation counts + case confidence score (0-100)
- Consent analysis with timing evidence and screenshots
- §631 findings (session replay, third-party chat) with attorney narratives
- §638.51 findings (ad pixels, analytics) with attorney narratives
- Confidence score breakdown and technical appendix (request log)

## Requirements

```bash
pip install "mcp[cli]" playwright reportlab
playwright install chromium
```

MCP server is registered in `.mcp.json` (stdio, local). If the tools are
missing, restart Claude Code in this directory to pick it up.

## Covered statutes

- **§631** — Wiretap: third-party interception of communication contents in real time
- **§638.51** — Pen Register: third-party recording of routing/navigation metadata
