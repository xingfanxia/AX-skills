# Qatar Airways Privilege Club (Avios) — login required, no provider

Status on 2026-10-13: **login required**. No `providers/qatar.py` exists; nothing behind the sign-in wall was probed.

## What was observed (signed out, headless Chrome via `_browser.Browser`, 2 home-page loads + 1 results load)

- Home page `https://www.qatarairways.com/en/homepage.html` (document 200, no block, no CAPTCHA). The
  booking widget is the custom element `app-nbx-explore`; its controls live in a shadow root, so
  `document.querySelectorAll` and Playwright text locators do not reach them. The survey drove it by
  viewport coordinates at 1440x900 after "Accept all" on the cookie banner.
- Signed out, the widget accepts everything up to the search: tick **"Book using Avios"**, One way,
  From `DOH`, To `LHR`, pick 1 Dec 2026 in the calendar, "Continue". No sign-in prompt so far. The
  calendar shown with Avios ticked is still the cash one (QAR prices from
  `POST /dapi/public/bff/web/affinity-search/affinity-fare-calendars`,
  body `{"cabinClass":"ECONOMY","itineraries":[{"departureDate","origin","destination"}],"channel":"WEB_DESKTOP"}`).
- Pressing **"Search flights"** with Avios ticked does not navigate. It opens a popup window
  `https://www.qatarairways.com/en/Privilege-Club/login.mobile.html`, title
  **"Log in to Privilege Club | Qatar Airways"**, body **"Log in to your account"** / "Email address or
  membership number" / "Log in" / "Not yet a Privilege Club member? Join now". The main page stays on
  the home page and makes no flight-search call. Reproduced twice. The site shows no sentence saying
  an account is needed; the login popup is the whole response.
- Control in the same session: untick "Book using Avios", press "Search flights" again, and the page
  navigates to the results app and loads cash fares:
  `https://www.qatarairways.com/app/booking/flight-selection?widget=QR&searchType=F&addTaxToFare=Y&minPurTime=0&selLang=en&tripType=O&fromStation=DOH&toStation=LHR&departing=2026-12-01&bookingClass=E&adults=1&children=0&infants=0&ofw=0&teenager=0&flexibleDate=off&allowRedemption=N`
  which calls `POST /dapi/public/bff/web/flight-search/fare-calendars` and
  `POST /dapi/public/bff/web/flight-search/flight-offers` (94 KB JSON; body starts
  `{"channel":"WEB_DESKTOP","itineraries":[{"origin","destination","departureDate","isRequested":true}],"cabinClass":"ECONOMY","ignoreInvalidPromoCode":true,"passengers":[...]}`).
  So the wall is specific to the Avios search, not to searching.
- The older link `https://booking.qatarairways.com/nsp/views/fareSelection.xhtml?...&bookAward=true`
  loads an empty "Choose a flight" shell; the live results app is `/app/booking/flight-selection`.
- Bot protection: Akamai sensor POSTs (`sensor_data`) answered 201, nothing blocked. The login popup
  carries a reCAPTCHA badge. `nbxBookingWebRules.json` mentions `recaptchaV3TokenTimeoutInSec`.

## Not verified

- The Avios results URL. The cash URL ends `allowRedemption=N`, so the Avios one is presumably the
  same path with a redemption flag set; it was not opened, because the site's own widget sends a
  signed-out visitor to sign-in first and this tool does not go around a sign-in wall.
- `/content/dam/nbxbooking/nbxBookingWebRules.json` contains `"enableGuestRedemption": true` and
  `"allowRedemptionFlow": true`. What they switch on is unknown; the widget still demanded sign-in.
- Everything about the Avios response: cabins per search, seats, taxes currency, partner flights.

## If this is revisited

A provider needs a signed-in Privilege Club session (as `ana-award` does for ANA), which this tool's
no-credentials rule excludes today. With one, the cash `flight-offers` request shape above is the place
to start comparing. Evidence: `~/.agents/scratch/data/award-flights/qatar/` — `r2/login-popup.png`
(the wall), `r2/s7.png` (form filled, Avios ticked), `r2/s10-cash.png` and `r2/index.txt` rows 92
(cash control), `r2.log` (event order), `flow.py` (the click-flow helper, follows popups).
