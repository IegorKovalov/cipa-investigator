# CIPA Investigator

Scans a website for California Invasion of Privacy Act (CIPA) violations and generates a law-firm-ready PDF evidence package.

## Usage

```
Run the CIPA investigator on <URL>
```

or directly:

```bash
python test_phase1.py <url>
```

## What It Does

1. Opens a real Chromium browser simulating a California user (LA geolocation, en-US locale)
2. Intercepts all third-party network requests as the page loads
3. Detects consent banners and records timing relative to tracker firing
4. Navigator Agent (Claude) autonomously browses high-value pages: checkout, forms, chat widgets
5. Legal Writer Agent (Claude) writes attorney-facing legal analysis for each finding
6. Generates `evidence_package.pdf` with violation findings, consent analysis, and technical appendix

## Output

`evidence_package.pdf` containing:
- Cover page with executive summary and violation count
- Consent analysis with screenshot
- §631 Wiretap violations (session replay tools: Hotjar, FullStory, Clarity)
- §638.51 Pen Register violations (ad pixels: Meta, Google, TikTok, Snapchat, LinkedIn)
- Technical appendix with full request log

## Requirements

```bash
pip install playwright anthropic reportlab
playwright install chromium
export ANTHROPIC_API_KEY=your_key_here
```

## Agents

| Agent | File | Role |
|---|---|---|
| Navigator Agent | agent_navigator.py | Analyzes page screenshots, decides where to browse next |
| Legal Writer Agent | agent_legal.py | Writes attorney-quality legal narrative for each tracker |

## Covered Statutes

- **§631** — Wiretap: third-party interception of communication contents in real time
- **§638.51** — Pen Register: third-party recording of routing/navigation metadata
