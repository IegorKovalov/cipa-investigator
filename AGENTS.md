# Agents & Tools

## Architecture in one sentence

Claude (the Claude Code session) is the single orchestrating agent; every
deterministic capability is an MCP tool served by `mcp_server.py`, and the
investigation methodology lives in `prompts/`.

## The orchestrator

| | |
|---|---|
| Who | Claude, running the `cipa-investigator` skill |
| Instructions | `prompts/orchestrator.md` (+ `consent_analysis.md`, `legal_reasoning.md`) |
| Decides | where to browse, when evidence is sufficient, how each host classifies, all attorney narratives |
| Never decides | timestamps, request counts, the confidence arithmetic, PDF layout — those are tool facts |

The three POC-era agents are absorbed into the orchestrator role:
consent detection (was `agent_consent.py`) happens whenever Claude looks at
a screenshot; navigation strategy (was `agent_navigator.py`, capped at 5
iterations) is now open-ended; legal writing (was `agent_legal.py`) is the
narrative fields of the findings JSON.

## MCP tools (`mcp_server.py`)

### Stateful — act on one live browser session (`tools/browser_tool.py`)

The server holds a single Playwright session between calls; the CIPA case
is a timeline of one continuous visit, so all timestamps share one clock.

| Tool | Input → Output |
|---|---|
| `start_investigation` | url → opens CA-simulated browser, starts clock + network capture |
| `take_screenshot` | label → image + capture time; stored for the PDF |
| `navigate` | path or URL → new page state + requests triggered |
| `click_element` | visible text → clicks it (banners, chat launchers, links) |
| `type_text` | field hint + text → types keystroke-by-keystroke (generates §631 evidence) |
| `scroll_page` | times → reveals lazy content/trackers |
| `get_network_log` | new_only → third-party requests grouped by host, timestamped, known-tracker annotated |
| `get_investigation_status` | — → session timeline, screenshot labels, totals |
| `end_investigation` | — → closes browser (screenshots survive for the report) |

### Deterministic reference (`tools/tracker_tool.py`, `tools/report_tool.py`)

Kept deterministic on purpose: the same evidence must always produce the
same classification and score — reproducibility is what makes the package
defensible.

| Tool | Input → Output |
|---|---|
| `lookup_tracker` | domain → classification, statute, litigation history, or reasoning guidance |
| `score_confidence` | violation counts + consent status → 0-100 score with itemized breakdown |
| `generate_report` | findings JSON (schema in `prompts/legal_reasoning.md`) → PDF evidence package |

## History

The original deterministic POC (`test_phase1.py`, `browser.py`,
`classifier.py`, `agent_consent.py`, `agent_navigator.py`,
`agent_legal.py`) was deleted after the MCP flow was validated end-to-end
on monday.com (2026-07-03). Its logic now lives in the tools (`trackers.py`,
`reporter.py`), the deterministic scoring rubric, and the `prompts/`.
The full history remains in git if the baseline is ever needed.
