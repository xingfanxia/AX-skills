# Korean Air SKYPASS (koreanair.com) — not implemented: award search requires log-in

Status as of 2026-10-13: **login required**. There is no `providers/korean.py`.

## What was observed (headless Chrome via `providers/_browser.Browser`, no account)

- `https://www.koreanair.com/us/en` answers 200 and redirects to `https://www.koreanair.com/`
  (US / English, origin prefilled from geolocation). No CAPTCHA and no block page; the Akamai
  `sensor_data` posts answer 201. A cookie banner ("Accept all" / "Accept essential only") covers the
  booking widget and intercepts clicks until one of its buttons is pressed.
- The booking widget has a two-way switch: "Book" | "Book with miles". The same widget is served at
  `https://www.koreanair.com/booking/search` (title "Flight Search - Book Airline Ticket").
- Clicking "Book with miles" as an anonymous visitor does not switch the form. It opens the site's
  "Log in" dialog (tabs "User ID" / "SKYPASS Number", fields "User ID", "Password", "Log in",
  "Sign Up", "Continue with Facebook / Google / Line / Apple"). The URL stays `https://www.koreanair.com/`
  and the click triggers no `/api/` request. The widget stays on the cash "Book" tab behind the dialog.
- The dialog carries no explanatory sentence; the gate is the dialog itself. Related wording in the
  site's passenger-selector strings (`languageInfo/en/C?name=passinger-select`): "When booking for two
  or more passengers, only the logged-in member's mileage can be used."

So the site does not offer an award search form, let alone miles results, without a SKYPASS log-in.

## Not tried, on purpose

- Any `/api/fly/award/...` or other award endpoint called directly. No award request was ever issued by
  the page, so none of its URL, request body or response shape was observed; the hint that such
  endpoints exist is from memory and unverified.
- A guessed award results deep link (the award form never rendered, so the site showed no such URL).
- Signing in. The rule for this tool was no account and no credentials.
- The cash "Book" search: outside this tool's purpose.

## If this is picked up again

A Korean Air provider needs a decision to use a signed-in SKYPASS session (as `ana-award` does for ANA).
With one: dismiss the cookie banner, click "Book with miles", fill the form, and record the traffic of
the results page with `sniff.py`-style response logging to find the award availability call.
Useful anonymous endpoints seen on the home page: `/api/et/uiCommon/c/a/airportList?flowType=RE&langCode=en`
(airports), `/api/et/route/c/a/getReservationAirport?directionType=D&flowType=RE&langCode=en&nationCode=us&tripType=RO`
(bookable origins), `/api/et/uiCommon/c/i/languageInfo/en/C?name=<block>` (UI strings).

Evidence under `~/.agents/scratch/data/award-flights/korean/`: `home/` (sniff of the home page),
`booking/` (sniff of `/booking/search`), `miles_tab/page.png` and `page.txt` (the log-in dialog after
clicking "Book with miles"), `scripts/click_miles.py` (the click script). Total cost: 5 page loads.
