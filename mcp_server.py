"""
CIPA Investigator MCP server.

Claude is the orchestrator; this server is the hands. It exposes a
stateful browser session plus deterministic reference tools (tracker
lookup, confidence scoring, PDF generation). Investigation methodology
lives in prompts/, not here.

Run: python mcp_server.py  (stdio transport, launched by Claude Code
via .mcp.json)
"""

import json

from mcp.server.fastmcp import FastMCP, Image

from tools.browser_tool import SESSION
from tools import tracker_tool, report_tool

mcp = FastMCP("cipa-investigator")


def _json(data) -> str:
    return json.dumps(data, indent=2, default=str)


def _require_session():
    if not SESSION.active:
        raise RuntimeError("No active investigation. Call start_investigation first.")


@mcp.tool()
async def start_investigation(url: str, headless: bool = True) -> str:
    """Open a browser as a simulated California visitor (LA geolocation,
    Pacific timezone) and load the target URL. Starts the session clock and
    third-party network capture. Only one investigation runs at a time;
    starting a new one closes the previous session."""
    state = await SESSION.start(url, headless=headless)
    await SESSION.screenshot("initial")
    state["note"] = (
        "Initial screenshot captured as 'initial'. Call take_screenshot to view "
        "the page and check for a consent banner, and get_network_log to see "
        "which third parties fired during page load."
    )
    return _json(state)


@mcp.tool()
async def take_screenshot(label: str) -> list:
    """Capture the current viewport. The label names the screenshot for the
    final PDF (e.g. 'initial', 'banner', 'checkout'). Returns the capture
    time in seconds since session start — compare against network log
    timestamps to establish consent timing."""
    _require_session()
    png, t = await SESSION.screenshot(label)
    return [f"Screenshot '{label}' captured at {t}s since session start.", Image(data=png, format="png")]


@mcp.tool()
async def navigate(target: str) -> str:
    """Navigate the live session to a path ('/pricing') or absolute URL.
    The session clock and network capture continue — cookies and consent
    state persist, as they would for a real visitor."""
    _require_session()
    return _json(await SESSION.navigate(target))


@mcp.tool()
async def click_element(text: str) -> str:
    """Click the first visible element containing the given text
    (button, link, cookie-banner option, chat launcher)."""
    _require_session()
    return _json(await SESSION.click_text(text))


@mcp.tool()
async def type_text(field: str, text: str) -> str:
    """Type into an input matched by placeholder, label, or name attribute
    (e.g. field='email', text='test@example.com'). Types character by
    character — if a session replay tool is present, keystrokes will appear
    in the network log, which is direct §631 evidence."""
    _require_session()
    return _json(await SESSION.type_text(field, text))


@mcp.tool()
async def scroll_page(times: int = 1) -> str:
    """Scroll down (600px per step) to reveal content and trigger
    scroll-activated trackers."""
    _require_session()
    return _json(await SESSION.scroll(times))


@mcp.tool()
def get_network_log(new_only: bool = True) -> str:
    """Third-party requests captured by the session, grouped by host with
    first/last seen timestamps, request counts, methods, and whether POST
    data was sent. Hosts matching the known-tracker database are annotated;
    for unknown hosts use lookup_tracker and reason about the vendor.
    new_only=True returns only activity since the previous call."""
    _require_session()
    return _json(SESSION.network_log(new_only=new_only))


@mcp.tool()
def get_investigation_status() -> str:
    """Session timeline: elapsed time, actions taken, screenshots stored,
    and total third-party request count. Use to decide whether evidence
    is sufficient to stop."""
    return _json(SESSION.status())


@mcp.tool()
def lookup_tracker(domain_or_url: str) -> str:
    """Look up a host in the known-tracker database. Returns the
    classification (wiretap §631 / pen_register §638.51), litigation
    history, and description — or reasoning guidance if unknown."""
    return _json(tracker_tool.lookup(domain_or_url))


@mcp.tool()
def score_confidence(
    wiretap_count: int,
    pen_register_count: int,
    consent_status: str,
    total_tracker_requests: int,
    litigated_tracker_present: bool,
    visitor_simulated_in_california: bool = True,
) -> str:
    """Deterministic case confidence score (0-100) with itemized breakdown.
    consent_status: 'absent' | 'too_late' | 'present'. Include the returned
    object as 'confidence' in the findings passed to generate_report."""
    return _json(tracker_tool.score_confidence(
        wiretap_count=wiretap_count,
        pen_register_count=pen_register_count,
        consent_status=consent_status,
        total_tracker_requests=total_tracker_requests,
        litigated_tracker_present=litigated_tracker_present,
        visitor_simulated_in_california=visitor_simulated_in_california,
    ))


@mcp.tool()
def generate_report(findings_json: str, output_path: str = "evidence_package.pdf") -> str:
    """Generate the law-firm-ready PDF evidence package. findings_json is a
    JSON object with: url, consent_analysis {status, explanation},
    wiretap [], pen_register [] (each finding: tracker_name, domain, statute,
    first_seen_seconds, request_count, legal_basis, consent_note, sample_url),
    plus optional executive_summary and confidence (from score_confidence).
    Screenshots taken during the session are embedded automatically.
    See prompts/legal_reasoning.md for the full schema."""
    findings = json.loads(findings_json)
    path = report_tool.build_report(findings, SESSION.screenshots, output_path)
    return f"Evidence package written to {path}"


@mcp.tool()
async def end_investigation() -> str:
    """Close the browser and end the session. Call after the report is
    generated (screenshots stay available until a new session starts)."""
    stats = await SESSION.close()
    return _json(stats)


if __name__ == "__main__":
    mcp.run()
