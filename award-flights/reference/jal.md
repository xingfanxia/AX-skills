# Japan Airlines JAL Mileage Bank (jal.co.jp) — not implemented: award search requires JMB login

Status as of 2026-10-13: **login required**. There is no `providers/jal.py`.

## What was observed (headless Chrome via `providers/_browser.Browser`, no account)

Entry page: `https://www.jal.co.jp/en-jp/book.html?top=mv_2` (200, no CAPTCHA, no block page; Akamai
sensor posts answer 200/201). Clicking the "Award tickets" tab and then its "International Flights"
sub-tab shows the "JAL International Award Tickets" panel with two links. Neither has an href; each
submits a hidden form on the page:

| Link text | onclick | Form submitted |
|---|---|---|
| Search using specific criteria | `JLJS_InterBookings.intAwardBookingJP()` | `intAwdFrm` |
| Search by Seat Availability Check Calendar | `JLJS_InterBookings.affinityJP()` | `intAffinityFrm` (sets `SEARCH_CASSETTE_ID`) |

Both links produce the same redirect chain and end on the member login page, before any search form,
calendar, flight or miles figure is shown:

1. `https://www121.jal.co.jp/JmbWeb/JR/Dispatcher_en.do` → 302
2. `https://jallogin.jal.co.jp/sso/AuthorizationEndpoint?scope=openid%20client&acr_values=4&design=JL001N&response_type=code&redirect_uri=https://www121.jal.co.jp/JmbWeb/JR/Dispatcher_en.do&…` → 302
3. `https://jallogin.jal.co.jp/sso/InternalAuthoriEndpoint/?…` → 302
4. `https://jallogin.jal.co.jp/contents/login?AUTH_TYPE=AUTH_THREEKEY_LOW&SITE_ID=co&…` → 200, title "JAL | Member Login"

Login page wording: "Member login / Log in with a password / JMB membership number (7 or 9 digits) /
Password / Log in", plus "Log in with a passkey" ("Passkey authentication is offered exclusively for
residents of Japan.") and "Log in with another account". `GET jallogin.jal.co.jp/account/checkAutoSession`
answers 401. The login page also loads a device-risk collector (`jallogin-ts.jal.co.jp/risk-collect/…`).

So the availability calendar is not an open, day-level view: it sits behind the same login as the
criteria search. No award data of any kind (availability, miles, taxes, flights) was reachable signed out.

## Not tried, on purpose

- Signing in, or calling anything on `www121.jal.co.jp/JmbWeb/` around the login redirect.
- Other regional sites (for example the America-region JAL site). Only the `en-jp` entry point named in
  the task was followed, so whether another region's award search is open is unknown.
- Partner-airline and oneworld award links on the same panel (`javascript:void(0)` anchors, not followed).

## If this is picked up again

A JAL provider needs a decision to use a signed-in JMB session (as `ana-award` does for ANA). After
login the flow continues at `www121.jal.co.jp/JmbWeb/JR/Dispatcher_en.do`; nothing past that point
(search form fields, results endpoint, response shape) was observed here.

Evidence: `~/.agents/scratch/data/award-flights/jal/01` (criteria link; `criteria.png`, `page.txt`) and
`jal/02` (calendar link; `calendar.png`, `index.txt` is the JSON request log). Earlier survey:
`~/.agents/scratch/data/award-flights/survey-a/jal/` and `survey-a/jal.0*.log`.
Cost of this investigation: 2 loads of the entry page plus 2 redirects to the login page.
