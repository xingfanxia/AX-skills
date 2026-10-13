# Etihad Guest (`providers/etihad.py`)

Verified 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.
Miles search is open to guests: the results page shows "Values are displayed in miles" without any login prompt.

## Flow

1. Navigate straight to the results deep link (cold loads worked every time, no home-page warm-up). The
   etihad.com widget's "Book with Etihad Guest Miles" toggle leads to the same page:
   `https://digital.etihad.com/book/search?LANGUAGE=EN&CHANNEL=DESKTOP&B_LOCATION=AUH&E_LOCATION=JFK&TRIP_TYPE=O&CABIN=E&TRAVELERS=ADT&TRIP_FLOW_TYPE=AVAILABILITY&DATE_1=202612010000&WDS_ENABLE_MILES_TOGGLE=TRUE&FLOW=AWARD`
   - `CABIN=E` makes the page ask for `commercialFareFamilies:["ECONOMY","BUSINESS"]`; `CABIN=F` asks for `["FIRST"]`
     only. Hence `all_cabins = False`: economy and business share one cached page load, first is a second load,
     premium returns `[]` without a load (no premium-economy family was ever seen). `cabin=None` does both loads.
   - `TRAVELERS=ADT,ADT` for two adults (verified: the request carries two travellers).
2. The page (Amadeus Digital Commerce) gets a guest token from `POST https://api-des.etihad.com/v1/security/oauth2/token/initialization`
   (client credentials baked into the site) and then POSTs
   `https://api-des.etihad.com/airlines/EY/v2/search/air-bounds?guestOfficeId=&language=en&useTest=false` with
   `{"commercialFareFamilies":[…],"itineraries":[{"originLocationCode","destinationLocationCode","departureDateTime":"2026-12-01T00:00:00.000","isRequestedBound":true}],"travelers":[{"passengerTypeCode":"ADT"}],"searchPreferences":{"showMilesPrice":true,"showSoldOut":true,"maxFlightCombinationsPerBound":25},"frequentFlyer":{…},"corporateCodes":[…]}`.
   The `frequentFlyer` block is a fixed placeholder card the page sends for every guest. The provider catches the
   response during navigation (about 7 s after `goto`); it does not replay the call or handle the token itself.
3. The page also calls `air-bounds` for the **next day** ("Next day departure") and `air-calendars`; the provider
   matches the request body's `departureDateTime` to pick the right one.
4. That first answer is capped and can miss itineraries (AUH-JFK: 7 groups, without the EY+AA connection). The page
   lists 5, then "Show more flights" repeats the same POST **without** `maxFlightCombinationsPerBound` (8 groups).
   When the first answer has more than 5 groups the provider clicks that button and uses the second answer; if the
   button or its response does not appear it falls back to the capped answer. With 5 or fewer groups there is no
   button, so whether an uncapped query would add anything there is unverified.
5. Empty market: HTTP **200** with `{"errors":[{"code":"7959","title":"NO FLIGHTS FOUND","detail":"NO FARE FOUND FOR REQUESTED ITINERARY"}]}`
   (seen for AUH-JFK first class) → `[]`. Any other answer without `data` raises `ProviderError`.

## Response → output

`data.airBoundGroups[]` is one itinerary each; `dictionaries` resolves ids.

| Output | Source |
|---|---|
| segments | `boundDetails.segments[].flightId` → `dictionaries.flight[id]` |
| `flight` | `marketingAirlineCode` + `marketingFlightNumber` |
| `from` / `to`, `dep` / `arr` | `departure`/`arrival` `.locationCode`, `.dateTime` (local with offset, cut to minutes) |
| `aircraft`, `operated_by` | `aircraftCode` / `operatingAirlineCode` through `dictionaries.aircraft` / `.airline` (upper-case names, re-cased) |
| `duration_min` | `boundDetails.duration` (seconds, includes connections) |
| fares | `airBounds[]`, one per fare family; entries with `status.value == "soldOut"` are skipped; cheapest miles per cabin kept |
| `cabin` | `dictionaries.fareFamilyWithServices[fareFamilyCode].cabin`: `eco` / `business` / `first` |
| `miles` | `prices.unitPrices[0].milesConversion.convertedMiles.base` (per traveller) |
| `tax`, `currency` | `prices.unitPrices[0].prices[0].totalTaxes`, `.currencyCode` (AED from AUH; other origins not checked) |
| `seats` | lowest `availabilityDetails[].quota` over the segments (9 looks like a cap; the page prints "N Seats left" for small counts) |
| `mixed` | `isMixedCabin` |
| `brand` | `fareFamilyCode` |

Fare families: `YGVALUE/YGCOMFORT/YGDELUXE`, `JG…`, `FGCOMFORT/FGDELUXE` are GuestSeat awards (fixed chart miles,
"Promo" badge on the page, booking classes N/I/O). Codes without the `G` (`YVALUE`, `JVALUE`, `FCOMFORT`, …) are
revenue seats priced in miles (hundreds of thousands in premium cabins). Both are bookable with miles and both are
returned; `brand` tells them apart. The site names them all just Value / Comfort / Deluxe.

`convertedMiles.base` + `totalTaxes` is what the page prints ("From 60,000 +AED1,065"). `convertedMiles.total` with
`remainingNonConverted.total` is the other payment split (taxes paid in miles too) and is ignored.
With several travellers the page prints the party total; the provider reports per traveller.

## Checked against the page (2026-12-01)

AUH-JFK: EY 1 60,000 + AED 1,065 economy / 464,957 + AED 2,675 business; EY 7 + B6 517 66,000 + AED 1,115;
EY 65 + AA 141 75,000 + AED 1,225, business "Not available". AUH-LHR: EY 61 30,000 + AED 565 / 439,317 + AED 1,445 /
first 772,099 + AED 1,445 "3 Seats left"; EY 67 first 140,000 + AED 1,445. All equal to the provider output.

## Limits and unknowns

- Akamai bot telemetry (`sensor_data` posts) runs on both hosts; no challenge, CAPTCHA or block in 14 page loads
  spaced 10 s or more apart. Higher rates were not tried.
- A search costs one page load per cabin group (economy/business, first); the provider spaces its own loads by `pace`.
- Not verified: origins outside the UAE (currency), partner-only markets, dates beyond the schedule horizon,
  children/infants, other error codes than 7959.
