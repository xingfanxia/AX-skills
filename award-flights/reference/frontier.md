# Frontier Miles (flyfrontier.com) — protocol notes

Verified 2026-10-13, signed out, headless Chrome via `_browser.Browser`. Provider: `providers/frontier.py`.

## Request
- Deep link (works cold; no home-page warm-up, no click):
  `GET https://booking.flyfrontier.com/Flight/InternalSelect?o1=DEN&d1=LAS&dd1=Dec%2001,%202026&ADT=1&loy=true&promo=&ftype=Miles`
  - `dd1` is `Mon DD, YYYY` (English month abbreviation), `ADT` adults, `ftype=Miles` + `loy=true` select miles pricing.
  - Answers 302 to `https://booking.flyfrontier.com/Flight/Select` (session cookie carries the search).
- A second search in the same browser session simply replaces the first; three back-to-back searches ~11 s apart worked.

## Where the data is
- No JSON response. The `/Flight/Select` HTML (~1.3 MB) has an inline script
  `FlightData = '{&quot;calendarLink&quot;:…}';` — HTML-escaped JSON on one line (~165 KB). The provider
  reads it from the document response body with a regex and `html.unescape`.
- `POST /Flight/GetLowFareAvailability` (~110 KB) fires later; presumably the date ribbon / low-fare calendar. Not used, not inspected.

## Field mapping (`FlightData.journeys[0].flights[]`)
| output | source |
|---|---|
| segments | `legs[]`: `carrierCode` + `flightNumber`, `departureStation`, `arrivalStation`, `departureDate` / `arrivalDate` (local, `YYYY-MM-DDTHH:MM:SS`) |
| operated_by | `legs[].carrierText` when non-empty, else carrier code (`F9` -> Frontier). Only empty `carrierText` was seen |
| aircraft | not published -> `None` |
| duration_min | last leg `arrivalDateUtc` minus first leg `departureDateUtc` (matches the page's "3 hrs 44 min") |
| miles | `standardFare` — in a miles search this holds miles, not dollars |
| tax (USD) | `milesFare` (5.6 nonstop, 11.2 for most connections) |
| seats | leading number of `milesFareFareSeatsRemaining` (`"3 Seats Left!"`, `"1 Seat Left!"`), else `None` |
| brand | constant `"Basic Fare"` |

Guards: `FlightData.fareTypeBy` must be `"Miles"` and the journey's stations/date must match the request,
otherwise `ProviderError` (the same page sells in dollars; `standardFare` would then be dollars). Flights with
no `standardFare` or empty `milesFareKey` are skipped (none seen).

## Cabin / brand decision
Frontier is single-cabin. The results table has four columns: Basic Fare, Economy Bundle, Premium Bundle,
Business Bundle. Bundles are the base fare plus extras (bags, seat choice, UpFront Plus seat) for additional
miles: `milesBundleFareEcob` / `Prem` / `Busi` (e.g. 2000 / 4000 / 8000, larger on higher fare classes), or
cash when "Use miles for bundles" is unchecked (`economyBundleFare` etc.). Basic is therefore always the
cheapest and is the only fare returned, as `economy`. "Business Bundle" is not a business cabin.

## Empty market and errors
- Unserved airport (DEN->HNL): still 200 at `/Flight/Select`, `journeys[0].flights` is `null`, and the page
  shows "ERROR — At least one entered or selected airport code is invalid…". The message is also in the HTML as
  `window._mfq.push(["tag", "error: …"])`. Provider returns `[]` for the airport-code message, raises
  `ProviderError` with the text for any other error tag, and returns `[]` when there are no flights and no error.
- No `FlightData` in the response at all -> `ProviderError` (blocked / changed).

## Limits observed
- No CAPTCHA, block or slowdown in 7 page loads spaced >= 10 s apart from one residential IP. `pace = 10`.

## Checked against the page (2026-12-01)
- DEN-LAS F9 2015 06:41: 5000 mi + 5.6 -> page "5000 mi + $6"; DEN-ONT-LAS 09:20: 20000 + 11.2 -> "20000 mi + $12".
- DEN-MCO F9 4646 06:41: 15000 + 5.6 -> "15000 mi + $6", 3 hrs 44 min; DEN-DTW-MCO 16:00: 22500 + 11.2 -> "22500 mi + $12".
- The page rounds taxes to whole dollars; the cents exist only in `FlightData`.

## Not verified
- Seats-left: present in the data but not in the page's visible text signed out, so not compared to a display.
- A served city pair with no flights on the date (assumed `flights` null/empty, possibly with a different error text — that would currently raise).
- Codeshare/other-carrier legs (`carrierText`), `ADT` > 1 (whether prices stay per person), dates near the schedule end.
- Whether signed-in members see different (elite / cardholder) miles prices.
