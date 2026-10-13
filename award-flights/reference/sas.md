# SAS EuroBonus (flysas.com) — protocol notes

Verified 2026-10-13 from one residential IP that the site geolocated to Luxembourg (`pos=lu`, prices in EUR).
No sign-in is needed to see points prices. The date tabs say "It is mandatory to log in for booking tickets
with points" and the cart button becomes LOG IN once a fare is selected; that only gates booking.

## URLs
- Warm-up: `https://www.flysas.com/en/` (wait ~12 s). A results load without it never called the API.
- Results deep link (searches by itself, no form click):
  `https://www.flysas.com/en/book/flights?search=OW_{ORG}-{DST}-{YYYYMMDD}_a{adults}c0i0y0&view=upsell&bookingFlow=points`
- The page's own call (GET, same origin, cookies only, no special headers seen):
  `https://www.flysas.com/api/offers/flights?to={DST}&from={ORG}&outDate={YYYYMMDD}&adt=1&chd=0&inf=0&yth=0&bookingFlow=points&pos=lu&channel=web&displayType=upsell`
  `pos` is chosen by the site from geolocation; the provider never builds this URL, it only catches the response.

## How the page gets to the API call (and why it sometimes does not)
Angular app `components.flysas.com/v1/book-ui-upsell`. Before searching it loads a hidden frame
`/v1/airbus-boeing/WKoG50iJAWKxPbv`, which posts `imperva-iframe-loaded` to the top window; then
`api2.flysas.com/searchpanel/validate?...` and the offers call follow within ~3 s of navigation.
Cloudflare sits in front. On bad loads it answers the hidden frame with 403 and starts a Turnstile widget
(`challenges.cloudflare.com/.../turnstile/...`) that does not clear in headless Chrome; the page then stays on
"Searching for available flights, please wait..." and the offers call is never made. An in-page `fetch` of
the offers URL in that state returns the 403 "Just a moment..." page, so it is no way around; do not use it.
Seen: 5 stalled loads out of 13 results loads. Four were in a burst of loads 1-2 minutes apart and one came
after a 4-minute pause; 0 stalls in the last 5 loads, made after 5-7 minute pauses, including three searches
15 s apart inside one session. The provider reloads
once after 20 s, then raises `ProviderError`.

Noise to ignore: a red "Something went wrong. Please try again later." banner is on every load, good or bad
(the cms calls `/v2/cms-www-api/content/privacy/` and `/v2/cms-s4s-components/fragments/cep/` answer 403).

## Response -> fields
- `outboundFlights` is an object `F0..Fn`; sorted by `ranking` (the page's order).
- Segment: `marketingCarrier.code` + `flightNumber`; `departureAirport.code` / `arrivalAirport.code`;
  `departureDateTimeInLocal` / `arrivalDateTimeInLocal` (first 16 chars); `airCraft.name`;
  `operatingCarrier.name` when present (e.g. "SAS Connect"), else `marketingCarrier.name`.
- `duration_min`: `connectionDuration` "HH:MM:SS", hours can exceed 24 ("27:20:00").
- Fares: `cabins[CABIN][BRAND].products[ID]`. Every product is emitted (a cabin can hold both a BONUS and a
  FLEX product); the page's grid shows only the cheapest per cabin (`lowestFares`).
  - cabin: key `ECONOMY` -> economy, `PREMIUM` -> premium (premium economy, old "SAS Plus"). `BUSINESS`,
    `PLUS`, `GO`, `FIRST` are mapped by name but were never seen; an unknown key is skipped.
  - miles: `price.pointsAfterDiscount`, else `price.points` (equal in every sample; no discount seen).
  - tax: `price.totalTax`, currency `price.currency`. This is the cart's "+ N EUR Taxes & carrier-imposed
    fees". `price.totalPrice` is the cash-fare equivalent and equals `totalTax` only for BONUS products.
  - seats: minimum `fares[].avlSeats` over segments. 9 means "9 or more"; the page prints "N left" below 9.
  - mixed: `fares[].cabinClass` differs between segments (M = economy, Y = premium seen). Never seen true.
  - brand: `productName`.
- Two kinds of product come back in the same list:
  `ECONOMY BONUS` / `PREMIUM BONUS` (codes SNEUES / SNEUPS, base fare 0) are real award seats, e.g. 30 000 p
  + EUR 91.38 CPH-EWR; `FLEX` / `PREMIUM FLEX` (NEUEF / NEUPF) are cash fares priced in points at roughly
  200 p per EUR of base fare, e.g. 379 356 p. A date with only FLEX products has no award seats.
- No availability: HTTP 200 `{"errors":[{"errorCode":"225050","errorMessage":"Unfortunately, we can't offer
  any availability for selected cities & bookingType"}],"links":[]}` -> `[]`. Seen for ARN-NRT and CPH-NRT.
  Any other error code raises, with the body in the message.
- `tabsInfo.outboundInfo` holds the lowest points price for the day before and after (not used).

## Not verified
- Business cabin, partner-operated (SkyTeam) itineraries and mixed-cabin products: none appeared on
  CPH-EWR / ARN-EWR in December 2026, so their key names and whether partners are sold here are unknown.
- More than one adult; the `c0i0y0` (child, infant, youth) counts.
- Whether another `pos` changes currency or prices.
- The answer for a market SAS sells but with no flights on the date (may be an error code other than 225050).
- ARN-EWR numbers were parsed but not compared with the rendered page; CPH-EWR was (see sample runs under
  `~/.agents/scratch/data/award-flights/sas/`).
