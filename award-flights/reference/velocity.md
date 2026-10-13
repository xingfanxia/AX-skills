# Virgin Australia Velocity (`providers/velocity.py`)

Verified 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.

## Flow

1. Navigate straight to the results deep link of the booking app (Sabre "Digital Experience"; no home-page
   warm-up was needed, cold loads worked every time):
   `https://book.virginaustralia.com/dx/VADX/#/flight-selection?journeyType=one-way&activeMonth=12-01-2026&awardBooking=true&class=Economy&ADT=1&origin=SYD&destination=MEL&date=12-01-2026&promoCode=&direction=0`
   Dates are `MM-DD-YYYY`. The whole search sits in the URL fragment, so the provider goes to `about:blank`
   first: otherwise a second search in the same browser would not reload the app.
2. The page itself POSTs `https://book.virginaustralia.com/api/graphql`:
   `{"operationName":"bookingAirSearch","variables":{"airSearchInput":{"cabinClass":"Economy","awardBooking":true,"promoCodes":[""],"searchType":"BRANDED","itineraryParts":[{"from":{"useNearbyLocations":false,"code":"SYD"},"to":{"useNearbyLocations":false,"code":"MEL"},"when":{"date":"2026-12-01"}}],"passengers":{"ADT":1}}},"query":"query bookingAirSearch($airSearchInput: CustomAirSearchInput) { bookingAirSearch(airSearchInput: $airSearchInput) { originalResponse __typename } }"}`
   The provider catches the first such response during the navigation (100-480 KB).
   Other GraphQL operations on the same URL (`getSession`, `getBookingApplicableRules`, `dcmcInit`) are ignored.
3. During the same load the page fetches `…/dx/VADX/<build>/data/translations/en-GB.json`; its `aircrafts{}` and
   `airlines{}` (by IATA code) name the aircraft and operating carrier. Cached after the first search; if it is
   missed the raw codes are returned.

Replaying the GraphQL call with an in-page `fetch` was not tried (the page also posts to an obfuscated
bot-protection URL on load; navigating avoids depending on whatever that adds).

## One search covers all cabins

`class=Economy` returns Economy and Business brands for every itinerary. A `class=Business` search of SYD→DOH
gave the same 21 itineraries with the same brand set (no extra reward brands); only 3 any-seat prices and some
seat counts differed. So `all_cabins = True` and the `cabin` argument is ignored. Premium economy and First
never appeared as offers (a `RF` "First Reward" family is declared on SYD→DOH, with no offers).

## Response → output

`data.bookingAirSearch.originalResponse`. Objects are written once with `"@id"` and referred to later as
`{"@ref": "<id>"}` (itinerary parts and segments); the provider indexes every `@id` first.
`brandedResults.itineraryPartBrands[0][]` is one entry per itinerary:

| Output | Source |
|---|---|
| segment `flight` | `itineraryPart.segments[].flight.airlineCode` + `flightNumber` |
| `from` / `to` | segment `origin` / `destination` |
| `dep` / `arr` | segment `departure` / `arrival` (local, cut to minutes) |
| `aircraft` | segment `equipment` (`73H`) through translations `aircrafts` |
| `operated_by` | `flight.operatingAirlineCode` through translations `airlines` (`aircraftLeaseText`, the page's "Virgin Aust Intl for Virgin Aust" wet-lease wording, is ignored) |
| `duration_min` | entry `duration` (minutes, includes layovers) |
| `cabin` | `brandOffers[].cabinClass` (`Economy`, `Business` seen) |
| `miles` | `brandOffers[].fare.alternatives[]`: the alternative that is one `FFCURRENCY` amount |
| `tax`, `currency` | `brandOffers[].taxes.alternatives[]`: the alternative that is one cash amount (`AUD`) |
| `seats` | `brandOffers[].seatsRemaining.count` (1-9; the page prints "N left at this price" only for small counts) |
| `brand` | `fareFamilies[].brandLabel[].marketingText` for the offer's `brandId`, see below |
| `mixed` | always `False`: no per-segment cabin is published per offer |

`fare`/`taxes`/`total` each list alternative ways to pay. The page prints "from 5,900 Pts and $43.33 or 13,300
Pts": fare in points plus taxes in cash (what the provider returns), or `total`'s all-points alternative (not returned).

### Reward Seats vs points for a cash fare (`brand`)

Each itinerary carries two kinds of offers, and the provider returns up to two fares per cabin, cheapest of each kind:

- **Reward Seat**: brand `RE` "Economy Reward" / `RB` "Business Reward". Fixed award price, limited seats; the page
  badges the flight "Reward Seats". Recognised by a `fare` with **no cash alternative** (points only). `brand` is
  the site's name unchanged, so it contains "Reward".
- **Any seat** (ordinary cash fare quoted in points, about 0.6 c/pt, several times dearer): brands `LT` Lite,
  `CH` Choice, `FL` Flex, `BU` Business. Their `fare` has both a points and an AUD alternative. `brand` is the
  site's name plus the suffix **` (any seat)`**, e.g. `Lite (any seat)`.

So: no suffix = Reward Seat; `(any seat)` = dynamic points price that exists whenever the flight is on sale.
A cabin with only an any-seat fare has no reward space. The CLI table shows the cheapest fare per cabin (the
Reward Seat when there is one); use `--brands` to see which kind it is.

One brand can have a different label per fare program (`RE` was "Reward Economy" in program 188694 and
"Economy Reward" in 149146 on SYD→LAX); the provider takes the label of the itinerary's last `programIDs` entry,
which is what the page showed.

A pair/date with nothing to sell answers 200 with `brandedResults` absent and `unbundledOffers: [[]]` → `[]`
(seen SYD→GRU; page says "Flight not found"). The page then fires three more `bookingAirSearch` calls for its
calendar; only the first answer is used.

## Partners

Partner flights do appear: SYD→DOH returned Qatar-operated `VA 1` (Economy Reward 56,000 + AUD 260.07) and
QR-marketed connections; SYD→LAX returned United-operated `VA 8000`… and `UA` segments (one Economy Reward via
VA+UA+UA, 55,900 + AUD 197.52). No Business Reward was offered on either partner route that day.

## Checked against the page (2026-12-01)

Every itinerary's cheapest price per cabin (points, cash, brand name, "N left") was compared with the page text
of the same load: SYD→MEL 24 itineraries / 48 prices, SYD→PER 36 / 69, SYD→NAN 7 / 14, SYD→ZQN 4 / 8,
SYD→DOH 21 / 35, SYD→LAX 8 / 15, all equal. Examples: SYD→MEL VA 800 Economy Reward 5,900 + $43.33, Business
Reward 15,500 + $43.33 (2 left); VA 830 Business (any seat) 56,700 + $66.30 (3 left); SYD→PER VA 800+VA 681
Lite (any seat) 71,800 + $109.28 (1 left).

## Limits observed

No CAPTCHA, challenge or block in 10 result-page loads (up to 4 back to back in one browser, 15 s apart).
Higher rates were not tried. Each load is heavy (about 125 JSON requests, 2-3 MB, mostly config and trackers).
A cookie-consent dialog overlays the page; it does not stop the search and is left alone.

## Not verified

- GraphQL error bodies (bad airport code, past date, rate limit): none was seen. Anything without
  `originalResponse` raises `ProviderError` with the body's head.
- `adults` > 1, non-AUD taxes (a departure outside Australia), `soldout: true` offers, premium economy / First
  offers, mixed-cabin connections.
- Whether signing in reveals more reward space than the signed-out search.
