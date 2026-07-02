"""
Navigator Agent — decides where to browse next during a CIPA investigation.
Looks at a screenshot of the current page and returns the next action to take.
"""

import base64
import json
import anthropic

client = anthropic.Anthropic()


def decide_next_action(screenshot: bytes, url: str, flows_walked: list, requests_found: list, failed_urls: list = None) -> dict:
    """
    Claude looks at the current page state and decides the next investigative action.
    Returns: {"action": "search"|"navigate"|"fill_form"|"open_chat"|"done", "target": str, "reason": str}
    """
    screenshot_b64 = base64.standard_b64encode(screenshot).decode("utf-8")

    trackers_seen = list({r["tracker"]["name"] for r in requests_found})
    flows_summary = ", ".join(flows_walked) if flows_walked else "none yet"
    failed_summary = ", ".join(failed_urls) if failed_urls else "none"

    prompt = f"""You are a CIPA privacy investigator analyzing a website for tracking violations.

Current page: {url}
Flows already walked: {flows_summary}
Trackers detected so far: {", ".join(trackers_seen) if trackers_seen else "none yet"}
Failed/blocked URLs (do NOT retry these): {failed_summary}

Look at the screenshot and decide the single most valuable next action to expose tracking behavior.

Choose one action:
- "search": type a query into the search bar (target = the query text)
- "navigate": go to a specific path (target = the path, e.g. "/checkout")
- "fill_form": fill out a visible form with fake data (target = "email_form" or "contact_form")
- "open_chat": click on a live chat widget if visible (target = "chat_widget")
- "done": we have enough evidence, stop browsing (target = "")

Prioritize flows that expose the most tracking: checkout, health/personal info forms, live chat, account creation.
Avoid login pages, logout, pages already visited, and any URL listed in failed/blocked URLs above.

Respond with valid JSON only:
{{"action": "...", "target": "...", "reason": "one sentence explaining why this exposes tracking"}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )

    try:
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        result = json.loads(text)
        print(f"    [Navigator] {result['action']} → {result['target']} ({result['reason']})")
        return result
    except Exception as e:
        print(f"    [Navigator] parse error: {e} — defaulting to done")
        return {"action": "done", "target": "", "reason": "parse error"}
