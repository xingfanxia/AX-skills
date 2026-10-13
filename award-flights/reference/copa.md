# Copa Airlines ConnectMiles (`copa`)

Status 2026-10-13: **blocked**. The miles search needs no sign-in, but the booking API sits behind
DataDome, which answered this tool's headless Chrome with a slider CAPTCHA on 3 of 3 attempts. The
provider has never completed a live search; its mapping (`parse`) is checked only against one answer
captured by an earlier survey session.

## Flow
1. Warm-up: `https://www.copaair.com/en-us/` (loads `dd.copaair.com/js/`, the DataDome script).
2. Results deep link (no form to click):
   `https://shopping.copaair.com/miles?roundtrip=false&adults=1&children=0&infants=0&date1=YYYY-MM-DD&date2=null&promocode=null&area1=PTY&area2=MIA&advanced_air_search=false&flexible_dates_v2=false&airline_preference=CM`
3. The page calls `GET https://api.copaair.com/ibe/booking/get-id` (returns `nonce` + `dynamicParameters`)
   and then `POST https://api.copaair.com/ibe/booking/plan-redemptions` with
   `{"promoCode":null,"adults":1,"children":0,"infants":0,"departureAirport1":"PTY","arrivalAirport1":"MIA","departureDate1":"2026-12-01","departureDate2":null,"Rulecode":"","isRoundTrip":false,"isConventionCode":null,"preferredAirline":"CM"}`.
   The provider only navigates and reads that response; it does not build the call itself (the nonce
   handling was not studied).

## Response (`plan-redemptions`, ~55 KB, a list with one block per direction)
- `[0].currency.code` -> tax currency. `[0].priceCalendars` = cheapest miles for the date +-3 days (unused).
- `[0].solutions[]` = itineraries. `journeyTime` `"PT03H06M"` -> `duration_min`.
- `solutions[].flights[]`: `marketingCarrier.airlineCode/flightNumber` -> `flight`;
  `departure|arrival.airportCode`, `.flightDate` + `.flightTime` (local, 24 h) -> `dep`/`arr`;
  `aircraftName`; `operatingCarrier.airlineName` (null when same as marketing) -> `operated_by`,
  falling back to `marketingCarrier.airlineName`.
- `solutions[].offers[]`: `fareFamily.code` ESV/ESD (Economy Saver/Standard) -> economy, BSV/BSD
  (Business Saver/Standard) -> business; `pricePerAdult.miles` / `.taxes`. Cheapest offer per cabin is
  kept, `brand` = `fareFamily.name`. A cabin with no offer is what the page shows as "Sold Out".
- Not published: seats left (`seats` = None). No per-segment cabin, only booking letters in
  `classOfService` (e.g. `["P","I"]`), so `mixed` is always False even though partner connections may mix.
- Only two cabins exist (page columns "Economy" and "Business / Dreams"; `dreamsCabin` marks the lie-flat
  aircraft). No premium or first.

## Partner flights
With `airline_preference=CM` the PTY-MIA answer already contained connections on Avianca (AV), Air
Canada (AC, operated by Air Canada Rouge) and United (UA), always with a Copa first leg. Other values of
`airline_preference` and markets Copa does not fly were never tested (blocked before reaching that).

## Blocks observed (one personal IP, 2026-10-13)
- ~02:19 survey session: home page for ~8 min with form interaction, then the deep link -> 200 with data.
- ~02:3x cold deep link via `sniff.py`: no booking call succeeded, slider CAPTCHA.
- Provider run (home page, 10 s, deep link): CAPTCHA. Again after a 5-minute pause: `get-id` -> **403**,
  then `geo.captcha-delivery.com/captcha/` iframe.
- CAPTCHA page wording: "Verification required. To protect your information and prevent automated access,
  we need you to complete the following verification." / "Slide right to secure your access" / "We've
  detected unusual activity from your device or network... Automated (bot) activity on your network (IP ...)".
  Behind it the results page shows "Invalid date" and "Oops! No flights found." Do not read that as an
  empty market.
- The provider raises `ProviderError("blocked: ...")` on a 403 from any `/ibe/booking/` call or when the
  CAPTCHA iframe is present. Whether the block is per-IP reputation (several airline sniffers ran from this
  IP the same hour) or headless detection is unknown; repeat-request tolerance is unknown.

## Not verified
- Any live provider search; the second route (PTY-JFK); empty-market answer shape (assumed empty
  `solutions` or `[]`); `adults` > 1 (assumed `pricePerAdult` stays per person).
- The results page says: "Log in to your ConnectMiles account. PreferMembers will find the best award
  availability when logged in." Signed-out results may therefore be a subset.
