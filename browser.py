import time
from playwright.sync_api import sync_playwright
from trackers import get_tracker
from agent_navigator import decide_next_action


def _dismiss_modals(page):
    """Close any overlays blocking interaction."""
    for sel in ["[aria-label='Close']", "[aria-label='close']", "button[class*='close']", ".modal-close", "[data-dismiss='modal']"]:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(0.5)
        except:
            continue
    for text in ["continue to", "stay on", "proceed"]:
        try:
            el = page.get_by_text(text, exact=False)
            if el.first.is_visible():
                el.first.click()
                time.sleep(0.5)
                break
        except:
            continue


def _detect_consent_banner(page) -> dict:
    """
    Checks whether a real consent banner is present.
    Returns banner info. We don't chase the decline button —
    presence/absence of a banner and its timing is the legal signal.
    """
    result = {"detected": False, "selector": None}
    # Only selectors that indicate real consent UI (not footer links)
    for sel in ["[id*='cookie']", "[class*='cookie']", "[id*='consent']", "[class*='consent']", "[id*='gdpr']", "[aria-label*='cookie']", "[aria-label*='consent']"]:
        try:
            el = page.query_selector(sel)
            if not el or not el.is_visible():
                continue
            box = el.bounding_box()
            if not box or box["width"] < 200 or box["height"] < 50:
                continue
            if not el.query_selector("button"):
                continue
            result["detected"] = True
            result["selector"] = sel
            return result
        except:
            continue
    return result


def capture(url: str, headless: bool = False) -> dict:
    """
    Browses the target URL, captures all third-party tracker requests,
    records consent banner state, and walks key user flows.
    Returns structured evidence data.
    """
    evidence = {
        "url": url,
        "requests": [],
        "screenshots": {},
        "consent": {
            "banner_detected": False,
            "banner_time": None,
            "requests_before_banner": [],
        },
        "flows_walked": [],
    }

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Los_Angeles",
            geolocation={"latitude": 34.0522, "longitude": -118.2437},
            permissions=["geolocation"],
        )
        page = context.new_page()

        def on_request(request):
            tracker = get_tracker(request.url)
            if tracker:
                elapsed = round(time.time() - start_time, 3)
                entry = {
                    "timestamp": elapsed,
                    "url": request.url,
                    "method": request.method,
                    "tracker": tracker,
                    "post_data": request.post_data or "",
                }
                evidence["requests"].append(entry)
                print(f"  [{elapsed}s] {tracker['type'].upper()} — {tracker['name']} → {request.url[:80]}")

        page.on("request", on_request)

        # Phase 1: Initial load
        print(f"\n[1] Loading {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        _dismiss_modals(page)
        evidence["screenshots"]["initial"] = page.screenshot(full_page=False)
        pre_banner_count = len(evidence["requests"])
        print(f"    Screenshot captured")

        # Phase 2: Consent banner check
        print(f"\n[2] Checking for consent banner...")
        banner = _detect_consent_banner(page)
        if banner["detected"]:
            banner_time = round(time.time() - start_time, 3)
            evidence["consent"]["banner_detected"] = True
            evidence["consent"]["banner_time"] = banner_time
            evidence["consent"]["requests_before_banner"] = evidence["requests"][:pre_banner_count]
            evidence["screenshots"]["banner"] = page.screenshot(full_page=False)
            print(f"    Banner detected at {banner_time}s — {len(evidence['consent']['requests_before_banner'])} trackers fired before it")
        else:
            evidence["consent"]["requests_before_banner"] = evidence["requests"][:pre_banner_count]
            print(f"    No consent banner detected — {pre_banner_count} trackers fired with no consent mechanism")

        # Phase 3: Claude-driven agentic browsing
        print(f"\n[3] Claude agent walking user flows...")
        max_iterations = 5
        failed_urls = []

        for i in range(max_iterations):
            screenshot = page.screenshot(full_page=False)
            decision = decide_next_action(
                screenshot=screenshot,
                url=page.url,
                flows_walked=evidence["flows_walked"],
                requests_found=evidence["requests"],
                failed_urls=failed_urls,
            )

            action = decision.get("action", "done")
            target = decision.get("target", "")

            if action == "done":
                print(f"    Agent finished after {i} iterations")
                break

            elif action == "search":
                try:
                    for sel in ["input[type='search']", "input[placeholder*='search' i]", "input[name*='search' i]", "[role='search'] input"]:
                        search = page.query_selector(sel)
                        if search and search.is_visible():
                            search.click()
                            time.sleep(0.3)
                            for char in target:
                                search.type(char, delay=80)
                            time.sleep(1)
                            evidence["flows_walked"].append(f"search:{target}")
                            evidence["screenshots"][f"search_{i}"] = page.screenshot(full_page=False)
                            break
                except Exception as e:
                    print(f"    Search failed: {e}")

            elif action == "navigate":
                try:
                    nav_url = f"{url.rstrip('/')}{target}" if target.startswith("/") else target
                    page.goto(nav_url, wait_until="domcontentloaded", timeout=8000)
                    time.sleep(1)
                    _dismiss_modals(page)
                    evidence["flows_walked"].append(f"navigate:{target}")
                    evidence["screenshots"][f"nav_{i}"] = page.screenshot(full_page=False)
                except Exception as e:
                    print(f"    Navigation failed: {e}")
                    failed_urls.append(target)

            elif action == "fill_form":
                try:
                    for form in page.query_selector_all("form")[:1]:
                        for inp in form.query_selector_all("input[type='text'], input[type='email'], input[type='tel']")[:3]:
                            if inp.is_visible():
                                inp.click()
                                inp.type("test@example.com", delay=80)
                                time.sleep(0.3)
                        evidence["flows_walked"].append("fill_form")
                        evidence["screenshots"][f"form_{i}"] = page.screenshot(full_page=False)
                        print(f"    Form filled")
                        break
                except Exception as e:
                    print(f"    Form fill failed: {e}")

            elif action == "open_chat":
                try:
                    for sel in ["[data-testid*='chat']", "[class*='chat-button']", "[class*='intercom']", "[id*='chat']"]:
                        btn = page.query_selector(sel)
                        if btn and btn.is_visible():
                            btn.click()
                            time.sleep(1)
                            evidence["flows_walked"].append("open_chat")
                            evidence["screenshots"][f"chat_{i}"] = page.screenshot(full_page=False)
                            break
                except Exception as e:
                    print(f"    Chat open failed: {e}")

        evidence["screenshots"]["final"] = page.screenshot(full_page=False)
        browser.close()

    print(f"\n[Done] Captured {len(evidence['requests'])} tracker requests across {len(evidence['flows_walked'])} flows")
    return evidence
