# Southwest Rapid Rewards (`providers/southwest.py`)

Verified 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.

## Flow

1. Warm-up: `https://www.southwest.com/`, wait 10 s.
2. Open the booking **form**, prefilled from URL parameters (note: `/air/booking/?`, not `select-depart.html`):
   `https://www.southwest.com/air/booking/?adultsCount=1&departureDate=2026-12-01&departureTimeOfDay=ALL_DAY&destinationAirportCode=LAX&fareType=POINTS&originationAirportCode=DAL&passengerType=ADULT&returnDate=&tripType=oneway`
3. Wait for the "Search flights" button, wait 8 s more, click it. The page moves to `select-depart.html` and POSTs
   `https://www.southwest.com/api/air-booking/v1/air-booking/page/air/booking/shopping` with
   `{"adultPassengersCount":"1","adultsCount":"1","departureDate":"2026-12-01","departureTimeOfDay":"ALL_DAY","destinationAirportCode":"LAX","fareType":"POINTS","int":"HOMEQBOMAIR","originationAirportCode":"DAL","passengerType":"ADULT","promoCode":"","returnDate":"","returnTimeOfDay":"ALL_DAY","tripType":"oneway","application":"air-booking","site":"southwest"}`.
   The provider catches that response (HTTP 200, ~60-120 KB, arrives within a few seconds of the click).

The request carries `x-api-key`, `x-app-id: air-booking`, `x-channel-id`, `x-user-experience-id` and a set of
bot-protection headers (`ee30zvqlwf-a/-b/-c/-d/-f/-z`) computed by the page's own script. The provider never builds
the request itself; it only clicks.

**The results deep link does not work.** Navigating straight to
`/air/booking/select-depart.html?...` (with or without a home-page warm-up, 2 of 2 tries) makes the page fire the
shopping call immediately; the API answers HTTP 400 (254-byte body, not captured) and the page falls back to the
form showing "Sorry, we found some errors... We are unable to process your request." The same search through
form + click succeeded 7 of 7 times. The 8 s wait before the click was never shortened, so it is unknown whether
the delay or the click is what matters.

## Response → output

`data.searchResults.airProducts[0].details[]`, one per itinerary:

| Output | Source |
|---|---|
| segment `flight` | `segments[].marketingCarrierCode` + `flightNumber` |
| `from` / `to` | `segments[].originationAirportCode` / `destinationAirportCode` |
| `dep` / `arr` | `segments[].departureDateTime` / `arrivalDateTime` (local, `2026-12-01T06:15:00.000-06:00`, cut to minutes) |
| `aircraft` | `segments[].aircraftEquipmentType`, raw code (`7S7`, `7M8`, `73H` seen; no name table) |
| `operated_by` | `segments[].operatingCarrierCode` (`WN` → Southwest; only `WN` seen) |
| `duration_min` | `details[].totalDuration` (minutes, includes layovers; equals the page's "14h 20m") |
| `miles` | `fareProducts.ADULT.<family>.fare.totalFare.value` (`currencyCode: "POINTS"`) |
| `tax`, `currency` | `...fare.totalTaxesAndFees.value` / `.currencyCode` (`5.60` `USD` on every domestic fare seen) |
| `seats` | `...fare.seatsLeft` (1-5 seen, absent on most fares → `None`) |
| `brand` | fare family through `BRANDS` |

Fare families are the four columns of the page, left to right: `WGARED` Basic, `PLURED` Choice, `ANYRED` Choice
Preferred, `BUSRED` Choice Extra. Every product reports `cabinInfo[].cabin: "ECO"`, so all map to `economy`
(Choice Extra is extra-legroom economy) and `mixed` is always false. The provider returns one fare per itinerary:
the cheapest family whose `availabilityStatus` is `AVAILABLE`, with its column name as `brand`. A sold-out
family has `availabilityStatus: "UNAVAILABLE"` and no `fare` (page shows "Unavailable"); an itinerary with no
available family is dropped.

A `segments[]` entry is one flight number. A through flight that lands on the way without a plane change stays
one segment (`numberOfStops: 1`, the legs are in `stopsDetails[]`); the intermediate airport is not output.

`data.searchResults.fareSummary[]` holds the per-family minimum for the day; unused.

## Empty results

- Both airports served, no itinerary (ITO→ISP): the API answers **HTTP 400**
  `{"notifications":{"formErrors":[{"code":"ERROR__NO_FLIGHTS_AVAILABLE","errorDetail":"AIS Error: No routes exist",...,"trackingCode":"400521204"}]},"success":false}` → `[]`.
- Airport Southwest does not serve (LAX→JFK): the form does not prefill that field, shows "Enter a valid
  arrival airport." and makes no API call. The provider waits 30 s for the call, then reads that text → `[]`.
- Any other non-200 or `success: false` answer raises `ProviderError` with the first 300 bytes of the body.

## Checked against the page (2026-12-01)

DAL→LAX: WN 1396 13,000 +$5.60; WN 4362 / 1397 / 1401 14,500 +$5.60; 201/146 via HOU 22,000 +$5.60.
BWI→HNL: 479/294 via LAS 43,500 +$5.60 (14h 20m = 860 min); 270/2619 via PHX Basic "Unavailable", Choice
59,500 +$5.60; 1501/2502 via LAX 22,500 +$5.60. All equal to the provider output (26 and 11 itineraries).

## Limits observed

No CAPTCHA or challenge page. About 16 page loads in 15 minutes (home, form, deep link), searches ≥12 s apart,
up to 2 searches per browser session; nothing slowed down or started failing. Higher rates and longer sessions
were not tried. The response header `terms-of-service` states that unauthorized use of fare data is prohibited
by the site's Terms & Conditions.

## Not verified

- `seats`: the count comes from the API only; the page text captured showed no "N left" wording to compare with.
- The 400 body of the rejected deep-link call, and whether it differs from a block on the form path.
- "Enter a valid departure airport." (unserved origin) is assumed by analogy with the arrival message.
- `adults` > 1, international routes (taxes above $5.60, non-USD), a date outside the booking window
  (the form says "Now accepting reservations through August 02, 2027"), partner-operated segments.
- Aircraft code meanings (`7S7` in particular) were not looked up.
