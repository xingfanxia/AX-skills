# Qantas Frequent Flyer (`providers/qantas.py`)

Verified 2026-10-13 from one residential IP (US), headless installed Chrome via `_browser.Browser`, no sign-in.
Reward results are shown to signed-out visitors; the results page only offers "Log in" as an option.

## Flow

1. Warm-up: `https://www.qantas.com/en-au/book/flights` (the booking widget page), wait 6 s.
2. The widget (`form#fsw-form`) is a plain form POST to
   `https://book.qantas.com/qf-booking/dyn/air/tripflow.redirect`. With one-way + the "Rewards" switch on, it posted:
   `depAirports=SYD&destAirports=LAX&travelDates=202612010000&numberOfAdults=1&numberOfYoungAdults=0&numberOfChildren=0&numberOfInfants=0&travelClass=ECO&searchOption=F&QFdeviceType=desktop&PAGE_FROM=/bookingError/v1/redirect/en-au/book/flights#fsw-form&USER_LANG=EN&USER_LOCALE=EN_AU&int_cam=au:bookflight:top:newfsw:en:flights&isClassicView=TRUE`
   `isClassicView=TRUE` is the Rewards switch (`searchOption` stays `F`). A return trip would put two values in
   `travelDates` (`out,back`); not used.
   The provider builds a form with these fields inside the qantas.com page and submits it (same origin and
   referer as the widget). It does not drive the widget itself because the widget's deep link
   (`…/book/flights?departureAirportCode=SYD&arrivalAirportCode=LAX&travelClass=ECO&tripType=O&usePoints=true&departureDate=2026-12-01`)
   prefills everything but parses the date as UTC, so on a machine west of UTC it selects the previous day.
3. Akamai answers the POST with a JS challenge that the browser resubmits by itself
   (`tripflow.redirect?akamai-challenge-resubmit=true`); no CAPTCHA was shown. The page lands on
   `https://book.qantas.com/qf-booking/dyn/air/booking/FFCO?SITE=QFQFQFBI&LANGUAGE=GB&TAB_ID=…` (Amadeus, Angular).
4. That page POSTs, among others (all under `/qf-booking/dyn/air/booking/`):
   - `flexPricerAvailabilityActionFromLoad` → the availability JSON (about 0.8 MB), 10-45 s after the form post.
   - `routeHappyAction` → amenities per flight (aircraft type), about 1 s later.
   - `preAvailabilityActionFromLoad`, `flexPricerCalendarActionFromLoad` (the ±date price strip); unused.
   The provider listens for the first two. Their request bodies carry an encrypted `ENC` session blob, so they
   cannot be built by hand; only the page can make them.
5. Before the next search the provider reloads the qantas.com widget page (so every search costs two page loads).
   Posting the form from the results page itself was not tried.

## Response → output

`modelInput.availability`, `bounds[0]` (one-way):

| Output | Source |
|---|---|
| itinerary | `listItineraries.itineraries[]`; its fares are `flights[<itemId>].listRecommendation` (fare family → recommendation) |
| segment `flight` | `segments[].airline.code` + `flightNumber` |
| `from` / `to` | `beginLocationCode` / `endLocationCode` are terminal-tagged (`SYD1`, `BNEI`, `HND3`); the IATA code is `listItineraries.locations[<code>].locationCode` |
| `dep` / `arr` | `beginDate` / `endDate`: epoch ms of the airport-local wall time read as UTC (format in UTC, no zone math) |
| `operated_by` | `operatingCarrierNameForDisplay` (e.g. `Qantaslink - Sunstate Airlines`, `American Airlines`) |
| `aircraft` | `routeHappyAction` → `amenityMapping["SYD-LAX-QF-11-20261201-ECON"]` lists ids; the one whose `amenityDictionary[id].type == "aircraft"` gives `displayText` (`A380 (jumbo)`, `787 (widebody)`). `None` if that call is missing |
| `duration_min` | itinerary `duration` (ms, includes layovers) |
| `cabin` | `bounds[0].ffCodeToAssociatedCabin[<ff>]`: `ACEECO`→E, `ACEPRM`→P, `ACEBUS`→B, `ACEFIR`→F |
| `miles` | `priceForOne.convertedBaseFare` (`milesCost` is null; `convertedCashMiles` is a points-for-everything figure the page does not show) |
| `tax`, `currency` | `priceForOne.tax`, `priceForOne.currency.code` (AUD). The page rounds it up to whole dollars (250.19 → "+ $251") |
| `seats` | `nbLastSeatsAvailable` (1-5 seen, else null). The page shows only "Seats nearly gone" for those |
| `mixed` | `mixedCabins` non-empty (lists the segments flown in a lower cabin) |
| `brand` | `listFareFamily.fareFamilies[<ff>].rewardPlusName` when `isRewardPlus`, else `.name`: "Economy Classic Plus" vs "Economy Classic Reward" |

Classic Reward (fixed points table, limited seats, includes partner airlines) and Classic Plus (dynamic price,
Qantas flights only) share the fare-family codes; `isRewardPlus` on the recommendation tells them apart, and one
itinerary has at most one of the two per cabin. Both are returned; filter on `brand` for Classic Reward only.
On 2026-12-01 both test routes had Classic Plus only.

One search returns all four cabins: the form asks for `travelClass=ECO`, the model says
`requestedMarginalCabins: E,P,B,F`, and the page's Cabin dropdown ("All", Economy, …) re-filters the same
availability response (switching to "All" made only calendar calls). Not checked: whether a `travelClass=BUS`
search would list extra itineraries that have no economy reward at all.

A city search covers its airports (SYD→NRT returned HND and NRT flights). An empty market (SYD→USH) still returns
the availability JSON, with no itineraries; the page says "No Classic Reward fares / There are no flights within
14 days of your searched dates." → `[]`. `modelInput.listMessages.messages` is where Amadeus puts errors; none seen.

## Checked against the page (searched 2026-10-13)

SYD→LAX 2026-12-01: QF 11 136,100 + $251 (250.19); QF 522 + QF 15 184,900 + $299 (298.14). SYD→NRT 2026-12-01
("All" cabins view): QF 59 192,600 + $184 / business 421,800 + $385; QF 25 134,200 + $184 / premium 228,500 +
$236 / business 421,800 + $385; QF 506 + QF 61 134,900 + $232 / business 403,300 + $456. SYD→LAX 2026-12-03:
QF 11 Classic Plus 115,300 + $251; AA 72 Classic 48,200 + $332. All equal to the provider output (tax rounded up).

## Limits observed

No CAPTCHA or block in about 16 page loads over 15 minutes (8 result pages), spaced ≥10 s. A search takes
35-60 s end to end. `pace = 15`. The provider waits 75 s for the availability call before raising.

## Not verified

Adults > 1 (the provider reads `priceForOne`), Jetstar fare families (`ACEECOJQ…` exist in the rules table; the
code falls back to the `ECO/PRM/BUS/FIR` stem), error messages for invalid airports or out-of-range dates,
sites other than en-au (AUD).
