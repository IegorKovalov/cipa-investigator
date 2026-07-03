# Consent Timing Analysis

CIPA requires ALL-PARTY consent BEFORE interception begins. The entire
consent analysis is a race between two timestamps:

- **T-tracker**: when the first third-party tracker request fired
  (from `get_network_log` — `first_seen_s` per host)
- **T-banner**: when a consent mechanism first became visible to the user
  (from your own observation of timestamped screenshots)

## The three outcomes

**`absent`** — no consent banner or opt-in mechanism appeared at any point
in the session. Strongest case: every tracker request is interception
without any opportunity to consent. A privacy-policy link in the footer is
NOT consent. Terms-of-service acceptance at checkout is NOT consent for
trackers that fired on the landing page.

**`too_late`** — a banner exists, but trackers fired before it appeared
(T-tracker < T-banner), or fired while it was displayed but before any
user choice. Still a strong case for every request with timestamp before
the user could have consented. Document exactly which hosts fired early
and at what second.

**`present`** — the banner appeared before any tracker fired, and trackers
only loaded after affirmative acceptance. Weakest case. Even here, check:
does clicking "Reject" actually stop the trackers? Trackers that keep
firing after rejection are their own violation — test this if a reject
option exists.

## What counts as a consent mechanism

Look for it VISUALLY in screenshots — never rely on CSS selectors or
element names. Banners come as bottom bars, modals, corner cards, and
interstitials, in any language. If you are unsure whether something is a
consent banner (e.g. a newsletter popup), it is not one — newsletter
popups, paywalls, and cookie-free "we use cookies" notices with no
choice offered do not give the user a way to refuse and thus cannot
establish consent anyway.

## Common traps

- A banner with only an "OK/Got it" button and no reject option is
  notice, not consent — classify by timing anyway, but note the defect.
- Trackers often fire on EVERY navigation. A banner accepted on page 1
  arguably covers page 2 — but requests from page 1 pre-acceptance remain
  violations.
- Screenshot the banner itself when present ('banner' label) — the PDF
  should show what the user saw.
