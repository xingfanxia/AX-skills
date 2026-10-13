# JetBlue TrueBlue (`providers/jetblue.py`)

Verified 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.

## Flow

1. Navigate straight to the results deep link (no home-page warm-up was needed; cold loads worked every time):
   `https://www.jetblue.com/booking/flights?from=JFK&to=LAX&depart=2026-12-01&isMultiCity=false&noOfRoute=1&adults=1&children=0&infants=0&sharedMarket=false&roundTripFaresFlag=false&usePoints=true`
2. The page itself POSTs `https://www.jetblue.com/api/ecom/cb-flight-search/v1/search/NGB` with
   `{"awardBooking":true,"travelerTypes":[{"type":"ADULT","quantity":1}],"searchComponents":[{"from":"JFK","to":"LAX","date":"2026-12-01"}]}`.
   The provider catches that response during the navigation (about 2-4 s after `goto`).
3. The answer is **HTTP 201** (not 200), `{"status":{"transactionStatus":"success"},"data":{"searchResults":[…]},"version":"v0.152.0"}`.
   That is why the provider uses `page.expect_response` directly: `Browser.json_after` only accepts status 200.

The old `jbrest.jetblue.com/lfs-rwb/outboundLFS` endpoint (`itinerary[]`/`bundles[]`) is no longer called by the page.

Calling the API with a bare in-page `fetch` (content-type only) returns 401 "Access denied due to missing
subscription key". The page's own request carries an `ocp-apim-subscription-key` header (a fixed value from the
site's JS bundle, same across the three searches observed) plus `adrum`, `x-b3-traceid`, `x-b3-spanid`. Replaying
with that header was not tried; navigating avoids depending on the key.

## Response → output

`data.searchResults[0].productOffers[]`, one per itinerary:

| Output | Source |
|---|---|
| segment `flight` | `originAndDestination[0].flightSegments[].flightInfo.marketingAirlineCode` + `marketingFlightNumber` |
| `from` / `to` | segment `departure.airport` / `arrival.airport` |
| `dep` / `arr` | segment `departure.date` / `arrival.date` (local, `YYYY-MM-DDTHH:MM:SS`, cut to minutes) |
| `aircraft` | segment `aircraft` (IATA type: `223`, `32Q`, `32S`), named through the small `AIRCRAFT` table, else the raw code. `aircraftCode` (`3NL`, `3NS`) looks like JetBlue's own configuration code and is ignored |
| `operated_by` | `flightInfo.operatingAirlineCode` (`B6` → JetBlue, other carriers stay as the 2-letter code) |
| `duration_min` | `originAndDestination[0].totalDuration` (minutes, includes layovers) |
| `miles` | `offers[].price[]` entry with `currency == "FFCURRENCY"` |
| `tax`, `currency` | the other `price[]` entry (`USD` seen) |
| `seats` | `offers[].seatsRemaining.count` (1-9 seen; 9 is probably a cap). The page prints "N left at this price" only for small counts (1-3 seen) |
| `brand`, `cabin` | `offers[].brand.brandId` through the `BRANDS` table |
| `mixed` | `offers[].offerSegmentInfo[].cabinClass` differ between segments |

Brand ids (names from the site's CMS `…/flight-result/fare-review-fo2-details-all` and `…/brandGroups`):
Main column `DN` Main Base, `AN` Main, `GR` Main Flex → economy; EvenMore column `DE` Base, `EN`, `ER` Flex →
premium (extra-legroom economy; the API itself calls it `Economy`); Mint column `MN`, `MR` Flex (`DM` Mint Base
listed in CMS) → business; BlueFirst column `DZ`, `ZN`, `ZR` → first. The API reports Mint as `cabinClass: "First"`
on an all-Mint itinerary and `"Business"` on a mixed one (economy feeder + Mint), so the cabin comes from the brand,
not from that field. Unknown brand ids fall back to the offer's `cabinClass`. The provider keeps the cheapest
offer per cabin; `soldOut` offers are skipped. The page's column price is the same cheapest brand while its
"Include Base" box is ticked (the default).

A route/date with nothing returns 201 success with `productOffers: []` (seen for JFK→NRT) → `[]`.
`alternateDateOffers[]` holds the ±3-day cheapest price strip (date, brand, price); unused.

## Checked against the page (2026-12-01)

JFK→LAX B6 123: 24,300 / 37,000 / 193,600 pts +$5.60; B6 523: 19,700 / 32,600 (1 left) / 193,600. JFK→LHR
B6 1107: 30,400 / 39,900 / 164,900 (1 left) +$5.60; B6 418+1620 via BOS: Mint 190,800 (3 left, mixed). All equal
to the provider output.

## Limits observed

No CAPTCHA, challenge page or block in 6 result-page loads spaced ≥10 s apart (3 of them back to back in one
browser session). Higher rates were not tried. Each load pulls about 75 JSON requests, mostly CMS and trackers.

## Not verified

- Partner-operated awards: only B6-operated segments were seen; CMS lists partner brand groups (`A1`, `A2`, `W2`,
  `A5`, `W5` economy/premium; `J1`, `J2`, `M1`, `Z2`, `J5` business/first) that would go through the `cabinClass` fallback.
- BlueFirst (`DZ`/`ZN`/`ZR`) and Mint Base (`DM`) offers were never returned; their mapping comes from CMS names only.
- `adults` > 1, non-USD taxes, `soldOut: true` offers, segments with a `stopAirport`, error bodies other than the 401 above.
