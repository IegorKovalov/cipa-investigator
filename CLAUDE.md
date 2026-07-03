# Koladin — CIPA Investigator

## What Is This Project

Koladin is a case origination intelligence platform for plaintiff attorneys, class action firms, mass arbitration practices, litigation funders, and investors. It identifies high-value legal violations at scale — across digital privacy, consumer protection, employment, and statutory claims — before they become publicly known.

This repo contains the **CIPA Investigator skill** — a tool that scans websites for California Invasion of Privacy Act violations and generates litigation-ready PDF evidence packages.

## Current State

The MCP-based agentic architecture is **built and validated end-to-end**: `mcp_server.py` exposes 12 tools (stateful browser session + deterministic reference tools), methodology lives in `prompts/`, roles are documented in `AGENTS.md`, and the server is registered in `.mcp.json`. Claude orchestrates; Python is tools only. The legacy deterministic pipeline has been deleted.

**Validated on monday.com** (2026-07-03): a full investigation ran through the MCP tools — CA-simulated session, consent-timing analysis, keystroke test on the signup form, classification of ~15 third-party hosts, deterministic scoring (87/100 STRONG), and a 7-page PDF. Confirmed Hotjar session-replay wiretap (§631) plus 12 pen registers (§638.51) firing before/without consent.

**Next:** run the remaining known-good targets (sephora.com, rei.com); consider surfacing "banner present but non-blocking" more explicitly in the PDF summary (currently shows "Consent Mechanism Present: YES" for the `too_late` case).

## Legal Context (Read This First)

### §631 — Wiretap
Third-party tools that intercept the **contents** of user communications in real time. Examples: Hotjar, FullStory, Microsoft Clarity, Mouseflow. Records keystrokes, mouse movements, form inputs. Hebrew analogy: האזנת סתר.

### §638.51 — Pen Register  
Third-party tools that record **routing/addressing metadata** — URLs visited, navigation paths, session identifiers. Examples: Meta Pixel, Google Analytics, TikTok Pixel, LinkedIn Insight, Snapchat Pixel. Hebrew analogy: רישום מטא-דאטה.

### Consent Rule
CIPA requires **all-party consent BEFORE interception begins**. A footer privacy link is not consent. A banner that appears after trackers fire is too late. No banner = strongest case.

### Jurisdiction
California geolocation must be simulated: LA coordinates (34.0522, -118.2437), America/Los_Angeles timezone, en-US locale.

## Current File Structure

Flat — the repo root IS the project, no nested folders. One git repo, remote: github.com/IegorKovalov/cipa-investigator.

```
koladin/
├── CLAUDE.md                          ← You are here
├── SKILL.md                           ← Skill definition (drives the MCP flow)
├── AGENTS.md                          ← Orchestrator + tool roles, inputs, outputs
├── .mcp.json                          ← Registers the local MCP server with Claude Code
├── mcp_server.py                      ← FastMCP server exposing 12 tools
├── tools/
│   ├── browser_tool.py                ← Stateful Playwright session (start/navigate/type/screenshot/network log)
│   ├── tracker_tool.py                ← lookup_tracker + deterministic confidence scoring
│   └── report_tool.py                 ← Validates findings JSON → reporter.py
├── prompts/
│   ├── orchestrator.md                ← Investigation methodology + stopping criteria
│   ├── consent_analysis.md            ← Consent-timing reasoning
│   └── legal_reasoning.md             ← Statute mapping + findings JSON schema
├── trackers.py                        ← Tracker database (wiretap/pen_register classification)
├── reporter.py                        ← ReportLab PDF generator (+ confidence score section)
├── domain_study.docx                  ← Legal research document
└── technical_design.docx              ← Architecture document
```

## The Orchestrator

Claude runs the whole investigation via the MCP tools; the three former
agents (consent detection, navigation, legal writing) are now absorbed
into that single orchestrator role. See `AGENTS.md` for the full breakdown.

## What Needs To Be Built Next

### Goal: Fully Agentic MCP Architecture

Replace the current deterministic Python orchestration with Claude as the central orchestrator calling MCP tools.

**Target structure:**
```
koladin/
├── CLAUDE.md
├── SKILL.md
├── AGENTS.md                          ← Document all agents, roles, inputs, outputs
│
├── mcp_server.py                      ← Local MCP server exposing tools to Claude
│
├── tools/
│   ├── browser_tool.py                ← browse_page(url) → screenshot + network requests
│   ├── tracker_tool.py                ← lookup_tracker(domain) → classification
│   └── report_tool.py                 ← generate_report(findings) → PDF
│
├── prompts/
│   ├── orchestrator.md                ← Main investigation prompt + reasoning instructions
│   ├── consent_analysis.md            ← How to reason about consent timing
│   └── legal_reasoning.md             ← How to map findings to statutes
│
└── trackers.py                        ← Stays as-is
```

**Key principles:**
- No hardcoded navigation limits (Claude decides when it has enough evidence)
- No hardcoded CSS selectors for consent detection (Claude uses vision)
- No hardcoded tracker matching in orchestration (Claude reasons about domains)
- Claude calls tools, reads results, reasons, calls next tool
- Add **case confidence scoring** (0-100) — critical for Koladin's value prop

### Case Confidence Score
This is what makes Koladin a case origination platform, not just a scanner:
```
Score: 87/100
- §631 violation confirmed: +40
- No consent mechanism: +25
- 6 pen register violations: +15
- High request volume: +7
- Known litigated tracker: +10
- Deduction (IP outside CA): -10
```

### MCP Server Approach
- Local MCP server for now (move to hosted later — same architecture)
- 12 tools exposed via MCP: stateful browser session (start_investigation, navigate, click_element, type_text, scroll_page, take_screenshot, get_network_log, get_investigation_status, end_investigation) + reference tools (lookup_tracker, score_confidence, generate_report)
- Claude Code connects to the local MCP server via `.mcp.json` (loaded at startup — restart Claude Code in this dir if tools are missing)

## How To Run

Restart Claude Code in this directory so it loads `.mcp.json`, then ask:

```
Run the CIPA investigator on https://www.monday.com
```

Claude drives the investigation through the MCP tools (methodology in
`prompts/`), writes `evidence_package.pdf`, and ends the session.

## GitHub
https://github.com/IegorKovalov/cipa-investigator

## Key Decisions Already Made
- Playwright (not Selenium) for browser automation — better network interception, geolocation spoofing
- Hostname-only tracker matching — prevents false positives
- ReportLab for PDF — programmatic, no external dependencies
- PDF is the primary deliverable (JSON output planned for future versions)
- Local MCP server first, hosted later
- Confidence scoring and classification stay deterministic (reproducibility for a legal deliverable); Claude's judgment is in evidence-gathering and narratives
- Claude Code itself is the orchestrator model — no per-agent model config anymore

## Environment
- ANTHROPIC_API_KEY in ~/.zshrc
- Python 3.11 via Anaconda
- Playwright + Chromium installed
- ReportLab installed
