# Koladin — CIPA Investigator

Scans a website for California Invasion of Privacy Act (CIPA) violations and
produces a law-firm-ready PDF evidence package with a 0–100 case confidence
score. Claude drives the whole investigation through a local MCP server; the
Python code is just tools.

- **§631 (wiretap)** — third parties intercepting communication *contents*
  (session replay, keystroke capture, third-party chat). Evidence lives in
  request POST bodies.
- **§638.51 (pen register)** — third parties recording routing *metadata*
  (URLs, navigation, referrers, IDs). Evidence usually lives in URL params.

## How it's wired (three pieces)

| Piece | File(s) | Loaded when |
|---|---|---|
| MCP server (14 tools) | `mcp_server.py`, `tools/` | Claude Code session starts (`.mcp.json`) |
| Skill (methodology) | `.claude/skills/cipa-investigator/SKILL.md`, `prompts/` | Session starts |
| Slash command | `.claude/commands/cipa.md` | Session starts |

All three are read **once, when a Claude Code session starts**. After changing
any of them — or after first cloning — quit and reopen Claude Code in this
folder. "Restart" means the Claude Code **session**, never the machine.

## One-time setup

```bash
pip install -r requirements.txt
playwright install chromium
```

The MCP server is registered in [.mcp.json](.mcp.json). It launches
`mcp_server.py` with `python3` from the project folder — so no absolute
paths, and the same config works on any machine (see "Different machine").

## Running an investigation

Open Claude Code in this directory and use any of:

```
/cipa https://www.example.com
/cipa-investigator https://www.example.com
Run the CIPA investigator on https://www.example.com
```

- `/cipa <url>` — the everyday entry point. Short, shows a `<url>` hint. **Use this.**
- `/cipa-investigator <url>` — the skill itself; identical result. It also
  triggers automatically from plain-English requests ("investigate X for
  privacy violations").
- Natural language — fires the skill without any slash.

They all run the same methodology (`prompts/orchestrator.md`). Output is
`evidence_package.pdf` in this folder.

> **Bot-protected sites** (Akamai/Cloudflare, e.g. Sephora): if the first
> screenshot says "Access Denied" with zero requests, the headless browser was
> blocked. Ask to retry headed — the orchestrator does this automatically.

## Using it on a different machine or session

**Different session, same machine:** nothing to do — just open Claude Code in
this folder. The skill, command, and MCP server all live in the repo.

**Different machine:**

1. `git clone https://github.com/IegorKovalov/cipa-investigator.git` and `cd` in.
2. `pip install -r requirements.txt` + `playwright install chromium`.
3. Open Claude Code in the repo folder. `/cipa` and the MCP tools appear.

No `.mcp.json` editing needed — it uses `python3` and a project-relative
path, so it works as-is on any machine. `.claude/` (skill + slash command)
travels with the repo too. The only requirement: `python3` must be the
Python where you ran `pip install` (a virtualenv or Conda env is fine —
just install into whatever `python3` your shell uses).

If after a restart the CIPA tools don't appear, `python3` on that machine
points somewhere without the packages. Fix: either `pip install -r
requirements.txt` into that `python3`, or set `command` in `.mcp.json` to
the full path from `which python3`.

## Output

`evidence_package.pdf`:
- Executive summary, violation counts, and case confidence score (0–100)
- Consent analysis with timing evidence and screenshots
- §631 findings (with the intercepted content quoted, when confirmed)
- §638.51 findings (ad pixels, analytics)
- Confidence breakdown and a technical request-log appendix

## Repo layout

```
mcp_server.py            FastMCP server (14 tools)
tools/browser_tool.py    stateful Playwright session + POST-body capture
tools/tracker_tool.py    lookup_tracker + deterministic confidence score
tools/report_tool.py     validate findings JSON -> reporter.py
prompts/                 orchestrator + consent + legal-reasoning methodology
trackers.py              known-tracker classification database
reporter.py              ReportLab PDF generator
.claude/skills/…         the skill    .claude/commands/cipa.md  the slash command
AGENTS.md                orchestrator + per-tool roles
```
