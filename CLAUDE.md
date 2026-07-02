# Koladin — CIPA Investigator

## What Is This Project

Koladin is a case origination intelligence platform for plaintiff attorneys, class action firms, mass arbitration practices, litigation funders, and investors. It identifies high-value legal violations at scale — across digital privacy, consumer protection, employment, and statutory claims — before they become publicly known.

This repo contains the **CIPA Investigator skill** — a tool that scans websites for California Invasion of Privacy Act violations and generates litigation-ready PDF evidence packages.

## Current State

A working POC is in `cipa-investigator/`. It detects §631 (Wiretap) and §638.51 (Pen Register) violations and produces a law-firm-ready PDF. It has been tested successfully on monday.com, sephora.com, and rei.com.

**The immediate task is to redesign this into a fully agentic, MCP-based architecture.** The current version has too much deterministic Python logic. The goal is: Claude as orchestrator, everything else as MCP tools Claude calls.

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
├── SKILL.md                           ← Skill definition (uploaded to Claude Code)
├── AGENTS.md                          ← (to be created)
├── domain_study.docx                  ← Legal research document
├── technical_design.docx              ← Architecture document
├── trackers.py                        ← Tracker database (wiretap/pen_register classification)
├── browser.py                         ← Playwright automation (3 phases)
├── classifier.py                      ← Maps evidence to §631/§638.51 findings
├── agent_consent.py                   ← Agent 1: Claude vision detects consent banners
├── agent_navigator.py                 ← Agent 2: Claude vision decides where to browse
├── agent_legal.py                     ← Agent 3: Claude writes attorney narratives
├── reporter.py                        ← ReportLab PDF generator
└── test_phase1.py                     ← Entry point: python test_phase1.py <url>
```

## The Three Current Agents

| Agent | File | Role |
|---|---|---|
| Consent Agent | `agent_consent.py` | Looks at screenshot, detects any consent banner visually |
| Navigator Agent | `agent_navigator.py` | Decides where to browse next (max 5 iterations) |
| Legal Writer Agent | `agent_legal.py` | Writes attorney narratives + executive summary |

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
- Tools exposed via MCP: browse_page, lookup_tracker, classify_violation, score_confidence, generate_report
- Claude Code connects to the local MCP server

## How To Run Current Version

```bash
source ~/.zshrc
cd /Users/iegorkovalov/claude-code/koladin
python test_phase1.py https://www.monday.com
```

Output opens automatically in Preview as `evidence_package.pdf`.

## GitHub
https://github.com/IegorKovalov/cipa-investigator

## Key Decisions Already Made
- Playwright (not Selenium) for browser automation — better network interception, geolocation spoofing
- Hostname-only tracker matching — prevents false positives
- ReportLab for PDF — programmatic, no external dependencies
- PDF is the primary deliverable (JSON output planned for future versions)
- Local MCP server first, hosted later
- Model: claude-sonnet-4-6 for all agents currently

## Environment
- ANTHROPIC_API_KEY in ~/.zshrc
- Python 3.11 via Anaconda
- Playwright + Chromium installed
- ReportLab installed
