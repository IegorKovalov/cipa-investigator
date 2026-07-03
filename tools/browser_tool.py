"""
Stateful browser session for CIPA investigations.

The MCP server holds ONE live Playwright session across tool calls.
This is deliberate: the legal case is a timeline of a single continuous
visit (trackers fired at Xs, banner appeared at Ys, user never consented),
so request timestamps and consent timing only mean something if every
tool call acts on the same open browser.
"""

import time
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from trackers import get_tracker

# Simulated California visitor — required for CIPA jurisdiction
CA_CONTEXT = {
    "viewport": {"width": 1280, "height": 800},
    "user_agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "locale": "en-US",
    "timezone_id": "America/Los_Angeles",
    "geolocation": {"latitude": 34.0522, "longitude": -118.2437},
    "permissions": ["geolocation"],
}


def _base_domain(host: str) -> str:
    """Naive registrable domain: last two labels (monday.com, hotjar.com)."""
    parts = (host or "").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


class InvestigationSession:
    def __init__(self):
        self._pw = None
        self.browser = None
        self.page = None
        self.start_time = None
        self.target_url = None
        self.first_party = None
        self.requests = []        # every third-party request, in firing order
        self._log_cursor = 0      # for get_network_log(new_only=True)
        self.screenshots = {}     # label -> png bytes (reused in the PDF)
        self.events = []          # timeline of session actions

    @property
    def active(self) -> bool:
        return self.page is not None

    def elapsed(self) -> float:
        return round(time.time() - self.start_time, 3)

    def _note(self, event: str):
        self.events.append({"t": self.elapsed(), "event": event})

    def _on_request(self, request):
        host = urlparse(request.url).hostname or ""
        if not host or _base_domain(host) == self.first_party:
            return
        try:
            post_data = request.post_data or ""
        except Exception:
            post_data = ""
        self.requests.append({
            "t": self.elapsed(),
            "host": host,
            "method": request.method,
            "url": request.url,
            "has_post_data": bool(post_data),
        })

    async def start(self, url: str, headless: bool = True) -> dict:
        if self.active:
            await self.close()
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=headless)
        context = await self.browser.new_context(**CA_CONTEXT)
        page = await context.new_page()

        self.start_time = time.time()
        self.target_url = url.rstrip("/")
        self.first_party = _base_domain(urlparse(url).hostname or "")
        self.requests = []
        self._log_cursor = 0
        self.screenshots = {}
        self.events = []

        page.on("request", self._on_request)
        self.page = page
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        self._note(f"loaded {url}")
        return await self.page_state()

    async def page_state(self) -> dict:
        return {
            "session_elapsed_s": self.elapsed(),
            "current_url": self.page.url,
            "title": await self.page.title(),
            "third_party_requests_total": len(self.requests),
        }

    async def navigate(self, target: str) -> dict:
        before = len(self.requests)
        url = f"{self.target_url}{target}" if target.startswith("/") else target
        await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await self.page.wait_for_timeout(1500)
        self._note(f"navigated to {target}")
        state = await self.page_state()
        state["new_requests_triggered"] = len(self.requests) - before
        return state

    async def click_text(self, text: str) -> dict:
        before = len(self.requests)
        await self.page.get_by_text(text, exact=False).first.click(timeout=5000)
        await self.page.wait_for_timeout(1500)
        self._note(f"clicked '{text}'")
        state = await self.page_state()
        state["new_requests_triggered"] = len(self.requests) - before
        return state

    async def type_text(self, field: str, text: str) -> dict:
        """Type into an input matched by placeholder, label, or name attribute.
        Typed character-by-character — session replay tools capture keystrokes,
        so realistic typing is itself evidence generation."""
        before = len(self.requests)
        target = None
        for locator in (
            self.page.get_by_placeholder(field, exact=False),
            self.page.get_by_label(field, exact=False),
            self.page.locator(f"input[name*='{field}' i]"),
            self.page.locator(f"input[type='{field}']"),
        ):
            try:
                if await locator.first.is_visible(timeout=1500):
                    target = locator.first
                    break
            except Exception:
                continue
        if target is None:
            raise RuntimeError(f"No visible input matching '{field}' found")
        await target.click()
        await target.press_sequentially(text, delay=80)
        await self.page.wait_for_timeout(1000)
        self._note(f"typed into '{field}'")
        state = await self.page_state()
        state["new_requests_triggered"] = len(self.requests) - before
        return state

    async def scroll(self, times: int = 1) -> dict:
        for _ in range(max(1, times)):
            await self.page.mouse.wheel(0, 600)
            await self.page.wait_for_timeout(500)
        self._note(f"scrolled x{times}")
        return await self.page_state()

    async def screenshot(self, label: str) -> tuple[bytes, float]:
        png = await self.page.screenshot(full_page=False)
        t = self.elapsed()
        self.screenshots[label] = png
        self._note(f"screenshot '{label}'")
        return png, t

    def network_log(self, new_only: bool = True) -> dict:
        reqs = self.requests[self._log_cursor:] if new_only else self.requests
        if new_only:
            self._log_cursor = len(self.requests)

        hosts = {}
        for r in reqs:
            h = hosts.setdefault(r["host"], {
                "host": r["host"],
                "requests": 0,
                "first_seen_s": r["t"],
                "last_seen_s": r["t"],
                "methods": set(),
                "sample_url": r["url"][:140],
                "sends_post_data": False,
            })
            h["requests"] += 1
            h["first_seen_s"] = min(h["first_seen_s"], r["t"])
            h["last_seen_s"] = max(h["last_seen_s"], r["t"])
            h["methods"].add(r["method"])
            h["sends_post_data"] = h["sends_post_data"] or r["has_post_data"]

        entries = []
        for h in sorted(hosts.values(), key=lambda x: x["first_seen_s"]):
            h["methods"] = sorted(h["methods"])
            known = get_tracker(f"https://{h['host']}/")
            h["known_tracker"] = (
                {"name": known["name"], "type": known["type"]} if known else None
            )
            entries.append(h)

        return {
            "session_elapsed_s": self.elapsed(),
            "showing": "new since last call" if new_only else "entire session",
            "third_party_requests_total": len(self.requests),
            "hosts": entries,
        }

    def status(self) -> dict:
        return {
            "active": self.active,
            "target_url": self.target_url,
            "session_elapsed_s": self.elapsed() if self.active else None,
            "third_party_requests_total": len(self.requests),
            "screenshots_taken": list(self.screenshots.keys()),
            "timeline": self.events,
        }

    async def close(self) -> dict:
        stats = {
            "third_party_requests_total": len(self.requests),
            "duration_s": self.elapsed() if self.start_time else 0,
        }
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()
        self.browser = None
        self.page = None
        self._pw = None
        return stats


# The one session the MCP server holds between tool calls
SESSION = InvestigationSession()
