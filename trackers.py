# Known third-party tracker domains and their classification
# wiretap = captures contents (§631)
# pen_register = captures routing/metadata (§638.51)

TRACKERS = {
    # Session replay — wiretap §631
    "fullstory.com":       {"name": "FullStory",         "type": "wiretap",      "description": "Session replay tool that records keystrokes and form inputs in real time"},
    "rs.fullstory.com":    {"name": "FullStory",         "type": "wiretap",      "description": "Session replay tool that records keystrokes and form inputs in real time"},
    "hotjar.com":          {"name": "Hotjar",            "type": "wiretap",      "description": "Session replay and heatmap tool that captures user keystrokes and interactions"},
    "script.hotjar.com":   {"name": "Hotjar",            "type": "wiretap",      "description": "Session replay and heatmap tool that captures user keystrokes and interactions"},
    "clarity.ms":          {"name": "Microsoft Clarity", "type": "wiretap",      "description": "Session replay tool by Microsoft that records user sessions including form inputs"},
    "logrocket.com":       {"name": "LogRocket",         "type": "wiretap",      "description": "Session replay tool that records user sessions and console logs"},
    "mouseflow.com":       {"name": "Mouseflow",         "type": "wiretap",      "description": "Session replay tool capturing mouse movement, clicks, and form inputs"},
    "inspectlet.com":      {"name": "Inspectlet",        "type": "wiretap",      "description": "Session replay tool that records keystrokes and form field data"},
    "smartlook.com":       {"name": "Smartlook",         "type": "wiretap",      "description": "Session replay tool recording user interactions and form inputs"},
    "luckyorange.com":     {"name": "Lucky Orange",      "type": "wiretap",      "description": "Session replay and chat tool capturing user keystrokes"},

    # Live chat — wiretap §631
    "intercom.io":         {"name": "Intercom",          "type": "wiretap",      "description": "Third-party live chat platform intercepting user-to-business communications"},
    "widget.intercom.io":  {"name": "Intercom",          "type": "wiretap",      "description": "Third-party live chat platform intercepting user-to-business communications"},
    "drift.com":           {"name": "Drift",             "type": "wiretap",      "description": "Third-party live chat platform intercepting communications in real time"},
    "tawk.to":             {"name": "Tawk.to",           "type": "wiretap",      "description": "Third-party live chat service intercepting user communications"},
    "zendesk.com":         {"name": "Zendesk",           "type": "wiretap",      "description": "Third-party customer support platform intercepting chat communications"},
    "zopim.com":           {"name": "Zendesk Chat",      "type": "wiretap",      "description": "Third-party chat platform intercepting user communications"},
    "crisp.chat":          {"name": "Crisp",             "type": "wiretap",      "description": "Third-party live chat service intercepting communications"},

    # Tracking pixels / analytics — pen register §638.51
    "connect.facebook.net":   {"name": "Meta Pixel",       "type": "pen_register", "description": "Meta tracking pixel recording URL paths, navigation, and user actions"},
    "facebook.com":           {"name": "Meta",              "type": "pen_register", "description": "Meta platform receiving navigation and routing data"},
    "google-analytics.com":   {"name": "Google Analytics",  "type": "pen_register", "description": "Google Analytics recording URL paths, referrers, and navigation sequences"},
    "analytics.google.com":   {"name": "Google Analytics",  "type": "pen_register", "description": "Google Analytics recording URL paths, referrers, and navigation sequences"},
    "googletagmanager.com":   {"name": "Google Tag Manager", "type": "pen_register", "description": "Tag manager deploying tracking scripts and recording navigation data"},
    "googlesyndication.com":  {"name": "Google Ads",        "type": "pen_register", "description": "Google advertising platform recording navigation and routing signals"},
    "doubleclick.net":        {"name": "Google DoubleClick", "type": "pen_register", "description": "Google ad platform recording user navigation paths"},
    "tiktok.com":             {"name": "TikTok Pixel",      "type": "pen_register", "description": "TikTok tracking pixel recording URL navigation and user actions"},
    "analytics.tiktok.com":   {"name": "TikTok Analytics",  "type": "pen_register", "description": "TikTok analytics recording navigation and routing data"},
    "snap.com":               {"name": "Snapchat Pixel",    "type": "pen_register", "description": "Snapchat tracking pixel recording navigation signals"},
    "tr.snapchat.com":        {"name": "Snapchat Pixel",    "type": "pen_register", "description": "Snapchat tracking pixel recording navigation signals"},
    "linkedin.com":           {"name": "LinkedIn Insight",  "type": "pen_register", "description": "LinkedIn tracking tag recording navigation and routing data"},
    "ads.linkedin.com":       {"name": "LinkedIn Ads",      "type": "pen_register", "description": "LinkedIn advertising platform recording navigation signals"},
    "pinterest.com":          {"name": "Pinterest Tag",     "type": "pen_register", "description": "Pinterest tracking tag recording navigation and user actions"},
    "twitter.com":            {"name": "X/Twitter Pixel",   "type": "pen_register", "description": "X/Twitter tracking pixel recording navigation data"},
    "t.co/i/adsct":           {"name": "X/Twitter",         "type": "pen_register", "description": "X/Twitter tracking recording navigation signals"},
    "segment.com":            {"name": "Segment",           "type": "pen_register", "description": "Customer data platform recording and routing user navigation data to third parties"},
    "cdn.segment.com":        {"name": "Segment",           "type": "pen_register", "description": "Customer data platform recording and routing user navigation data to third parties"},
    "mixpanel.com":           {"name": "Mixpanel",          "type": "pen_register", "description": "Analytics platform recording user navigation paths and actions"},
    "amplitude.com":          {"name": "Amplitude",         "type": "pen_register", "description": "Analytics platform recording navigation sequences and user actions"},
    "heap.io":                {"name": "Heap",              "type": "pen_register", "description": "Analytics platform recording all user interactions and navigation"},
    "optimizely.com":         {"name": "Optimizely",        "type": "pen_register", "description": "A/B testing platform recording navigation paths and variant exposure"},
    "klaviyo.com":            {"name": "Klaviyo",           "type": "pen_register", "description": "Email marketing platform recording navigation and routing signals"},
}


def get_tracker(url: str) -> dict | None:
    """Check if a URL belongs to a known tracker. Returns tracker info or None."""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
    except:
        hostname = ""

    for domain, info in TRACKERS.items():
        # Match on hostname only, not full URL, to avoid false positives
        if hostname == domain or hostname.endswith("." + domain):
            return {**info, "domain": domain}
    return None
