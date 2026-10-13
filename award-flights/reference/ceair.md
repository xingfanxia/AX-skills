# China Eastern Eastern Miles (`providers/ceair.py`)

Checked 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.
Miles were compared with the page on three routes; taxes could not be compared with the page (see "Not verified").

## Flow

1. Navigate straight to the results deep link (no home-page warm-up needed; cold loads worked):
   `https://www.ceair.com/en/usd/shopping/oneway/PVG-NRT/2026-12-01?eyJwYXlXYXkiOiJKRiJ9encoded`
   - Path: `/<language>/<currency>/shopping/oneway/<ORG>-<DST>/<YYYY-MM-DD>`. `usd` is the currency of the taxes.
   - Query: base64 of a compact JSON object, then the literal `encoded`. `{"payWay":"JF"}` = price in points
     (JF, 积分). Other keys read by the site's script: `passengerNum` (`"adults,children,infants"`, default
     `"1,0,0"`), `cabinClass`. The provider adds `passengerNum` only when adults is not 1.
2. The page POSTs `https://www.ceair.com/portal/v3/shopping/briefInfo`, about 3-6 s after `goto`:
   `{"adultCount":1,"arrCityCode":"TYO","arrCode":"NRT","arrStationCode":"","arrDate":"","childCount":0,"depCityCode":"SHA","depCode":"PVG","depStationCode":"","depDate":"2026-12-01","infantCount":0,"routeType":"OW","onlyPlaneFlag":true,"jfType":"ALL","cabinLevel":"","verifyUrl":"/portal/v3/shopping/briefInfo?SHATYO2026-12-01"}`
   The page fills in the city codes from its own airport list, which is why the provider navigates and
   catches the answer (`page.expect_response`) rather than building the body itself.
3. The page then sends follow-up `briefInfo` calls that the provider ignores:
   - the same body again (identical answer, seen on PVG-NRT) or with `"productCode":"GJJFZJ"` (always
     answered `resultCode 000500520`, no data);
   - `"jfType":"mcab"` (always answered `232009` "No flight information found" in every test).
   The provider takes the first POST whose body has `jfType: "ALL"` and no `productCode`.

## Airport and city codes

Plain IATA airport codes work in the URL: `PVG-NRT` sends `depCode: "PVG"` and returned only PVG flights.
The site's own search form writes Shanghai as `SHA,PVG` (both airports in one search, `depCode: "SHA,PVG"`);
the provider does not use that form, the caller searches each airport. A code the site does not know (tried
`ZZZ`) is searched with a blank `arrCode`; the provider returns `[]` for that. The provider raises if the
request the page sent does not carry the origin, destination, date and adult count it was asked for.

## Response → output

Top level: `resultCode` (`S200` = results), `currencyCode` (`JF` for points; anything else raises),
`taxCurrency` (`USD`), `data.flightItems[]` one per itinerary, `data.productInfos[]`.

| Output | Source |
|---|---|
| segment `flight` | `flightInfos[0].flightSegments[].airlineCode` + `flightNo` (marketing) |
| `from` / `to` | segment `orgCode` / `destCode` |
| `dep` / `arr` | `fltDate` + `orgTime` / `arriDate` + `destTime` (local) |
| `aircraft` | `icaoType` (`Airbus359(Wide)`, sometimes just the code `326`), else `planeType` |
| `operated_by` | `carrierCodeName` (`carrierCode`/`carrierNo` are the operating flight; `codesharefg` true on MU 8596 operated by FM 812) |
| `duration_min` | `flightInfos[0].duration` (minutes) |
| fare `cabin` | `cabinInfoDescs[].muCabinLevel`: Y economy, W premium, J and U business, F first |
| `miles` | `fareInfoDescList[]` with `paxType: "ADT"`: `lprice` (equals `totalPrice`); per adult, same value with 2 adults |
| `tax` / `currency` | same entry's `taxPrice` / top-level `taxCurrency` |
| `brand` | `data.productInfos[].cabinLabelInfo[0].labelName` for the fare's `productCode` (`COMMON_JFI` "International Standard Points Redemption", `COMMON_JF` "Domestic Standard Points Redemption") |
| `seats` | not published: always `None` |
| `mixed` | always `False` (only single-segment itineraries seen) |

Each itinerary carries at most one points fare per cabin. A cabin with no award space is simply missing
(the page shows `— —`). The page's column is "Business/First Class"; the provider reports J/U as business.

Empty results: `resultCode` `231012` / `232009` "No flight information found…" and `231009` "No relevant
flight information found…" return `[]`. Any other code raises with `resultMsg`.

## Observed on 2026-12-01

| Route | Result |
|---|---|
| PVG→NRT | 3 nonstops (MU 523/521/271), economy 25,000 + USD 68.5; business 38,000 on MU 271 only |
| HKG→PVG | 8 nonstops incl. FM 812 and its codeshare MU 8596; economy 20,000 + USD 58.4, business 30,000 + USD 67.3 |
| SZX→PVG | 3 nonstops; economy 16,000, business 20,000, both + USD 20.9 |
| PVG→LAX | `231012`, no flights |
| SZX→NRT | `231009`, no flights |

Only nonstop MU/FM flights appeared. No connecting itinerary and no other SkyTeam carrier was ever returned
(SZX→NRT, which would connect in Shanghai, was empty), so multi-segment parsing is written but untested.

## Blocks and limits

- The site's firewall answers **HTTP 200 with an HTML page** `Try again later! Your IP: …, Event-ID: …`
  (script from `blocksrc.haplat.net`) instead of JSON. The provider raises `ProviderError` on it.
- `POST /portal/v3/shopping/fareDetail` (sent when a fare cell is clicked) got that page on both attempts,
  while `briefInfo` on the same page loads worked.
- `briefInfo` itself got that page on about the 12th page load within roughly 20 minutes (loads 12 s or more
  apart, two of them including the blocked `fareDetail` click). Testing stopped there; how long the block
  lasts and the real threshold are unknown. `pace` is set to 20 as a guess, not a measured safe value.
- A "Safe Travel" notice overlays the results page ("Got it") and a cookie bar ("Accept"); neither affects
  the API call.

## Not verified

- **Taxes against the page.** The results list shows points only ("Points 25,000"); taxes appear after a
  fare is selected, which needs `fareDetail`, blocked here. `taxPrice` is reported as the API gives it.
  The "Incl.Tax" radio is not a tax view: it re-runs the search as a cash fare search.
- Connecting, partner-airline, premium-economy and first-class results; the `mcab` answer when it has data.
- Whether a signed-in member sees more award space or other products than the signed-out search.
- `passengerNum` with 2 adults produced `adultCount: 2` and the same per-adult points; not compared on the page.
