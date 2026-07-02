"""
Consent Banner Agent — uses Claude vision to detect consent banners in screenshots.
More reliable than CSS selectors since banners vary widely across sites.
"""

import base64
import json
import anthropic

client = anthropic.Anthropic()


def detect_consent_banner(screenshot: bytes) -> dict:
    """
    Claude looks at a screenshot and determines if a consent banner is visible.
    Returns: {"detected": bool, "description": str}
    """
    screenshot_b64 = base64.standard_b64encode(screenshot).decode("utf-8")

    prompt = """Look at this webpage screenshot carefully.

Is there a cookie consent banner, privacy notice popup, or tracking consent dialog visible on the screen?

These typically look like:
- A bar at the bottom or top of the page asking about cookies or tracking
- A popup or modal asking for consent to use cookies or analytics
- A notice mentioning "cookies", "privacy", "tracking", "analytics", or "marketing"
- Any UI element asking the user to Accept, Decline, or manage preferences

Do NOT count:
- Footer links to privacy policy or cookie policy
- Navigation menu items
- General popups unrelated to privacy/consent

Respond with JSON only:
{"detected": true or false, "description": "one sentence describing what you see, or 'none' if not detected"}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=128,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        result = json.loads(text)
        detected = result.get("detected", False)
        description = result.get("description", "")
        print(f"    [Consent Agent] {'Banner detected' if detected else 'No banner'} — {description}")
        return {"detected": detected, "description": description}

    except Exception as e:
        print(f"    [Consent Agent] Error: {e} — defaulting to not detected")
        return {"detected": False, "description": "detection error"}
