---
description: Run a CIPA privacy-violation investigation on a URL and produce a PDF evidence package
argument-hint: <url>
---

Run a full CIPA (California Invasion of Privacy Act) investigation on: $ARGUMENTS

If the argument above is empty, ask the user for the target URL before doing anything else.

Invoke the `cipa-investigator` skill and follow its methodology:

1. Read `prompts/orchestrator.md`, `prompts/consent_analysis.md`, and `prompts/legal_reasoning.md`.
2. Drive the investigation through the `cipa-investigator` MCP tools:
   `start_investigation` → document the pre-consent state (screenshot + `get_network_log`) → walk communication surfaces (forms, chat, search) with `navigate` / `type_text` / `click_element` → classify every third-party host (`lookup_tracker`) → `score_confidence` → write the attorney narratives → `generate_report` → `end_investigation`.
3. Report back the confidence score, the §631/§638.51 findings, and the path to `evidence_package.pdf`.

You decide when the evidence is sufficient — there is no fixed iteration count. Every claim must trace to a timestamped request or screenshot from the session.
