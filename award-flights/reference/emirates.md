# Emirates Skywards (Classic Rewards) — login required, no provider

Status on 2026-10-13: **login required**. No `providers/emirates.py` exists; nothing below the sign-in wall was probed.

## What was observed (signed out, headless Chrome via `_browser.Browser`, 2 page loads)

- Booking widget: `https://www.emirates.com/us/english/book/` (document 200, no block, no CAPTCHA).
- The widget has trip tabs Return / One way / Multicity, then airports, dates, passengers, class, promo code.
  There is no "Classic Rewards" / "Book with Miles" toggle for a signed-out visitor. In its place the
  widget shows a link with the exact text **"Log in to book Classic Rewards"**.
- That link goes to the Skywards SSO page
  `https://accounts.emirates.com/us/english/sso/v2/login?clientId=...&callbackUrl=/us/english/book/&redirectUrl=https://www.emirates.com/service/bex/auth/callback&pub=us/english&channelName=EKCOM_BEX`
  (title "Login to Emirates | Emirates", form "Email or Emirates Skywards number" + "Password").
- The widget's own station lookups are made with rewards off:
  `GET /service/hmp/stations?module=ONLINE_BOOKING&requestedPoint=ORIGIN&emiratesRewards=false`
  (also `requestedPoint=DESTINATION`, and `/service/hmp/stations/<IATA>?...`). The `emiratesRewards`
  flag is presumably what a signed-in session flips; not tested.
- Other JSON on the page: `/service/header?c=us&l=english&a=tier,visitor`, `/service/geo`,
  `/service/hmp/stations/content?siteLocale=en-US`, `/service/publications`. None carries fares.
- Bot protection: Akamai sensor POSTs (`sensor_data`) on the page; they answered 201 and nothing was blocked.

## Not verified

- The miles search results URL and its JSON (old hints: `https://www.emirates.com/service/search-results`,
  a `fly10.emirates.com` IBE flow). Neither was opened: the site puts miles search behind sign-in, and the
  tool's rule is not to call an API around a sign-in wall.
- Whether a signed-in session gets all cabins in one response, seat counts, or carrier surcharges split out.

## If this is revisited

A provider would need a signed-in Skywards session (as `ana-award` does for ANA), which this tool's
no-credentials rule excludes today. Evidence: `~/.agents/scratch/data/award-flights/emirates/`
(`s1/page.png`, `s1/page.txt`, `s1/index.txt`, `login_wall.png`, `login_wall.txt`).
