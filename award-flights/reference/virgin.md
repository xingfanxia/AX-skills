# Virgin Atlantic Flying Club (`virgin`) — protocol notes

Status 2026-10-13: **blocked, no provider written.** Award search requires a signed-in Flying Club
account, enforced by the server. The tool's rule is no sign-in, so `providers/virgin.py` does not exist.

## What was observed (headless Chrome via `_browser.Browser`, 8 page loads, no CAPTCHA, no rate limit)

- Home `https://www.virginatlantic.com/en-US` loads normally (Akamai Bot Manager sensor posts run, no
  challenge). The booking widget has a "Search for Reward Seats" switch; turning it on shows
  "You'll need to log in to book flights with your Virgin Points" and sets `payment_type=PAY_WITH_POINTS`.
- Submitting the widget goes to
  `https://book.virginatlantic.com/flights/search/slice?origin=LHR&destination=JFK&departing=2026-12-01&passengers=a1t0c0i0&awardSearch=true`
  → 301/307 → `https://www.virginatlantic.com/en-US/flights/search/slice?awardSearch=true&origin=…&destination=…&departing=YYYY-MM-DD&passengers=a1t0c0i0`.
  That results page (Next.js + Apollo) redirects within ~3 s to
  `identity.virginatlantic.com/…/B2C_1A_VA_DIGITAL_SIGNUP_SIGNIN_CA/…authorize` (the "Log in" form).
- Before redirecting, the page POSTs to `https://www.virginatlantic.com/flights/search/api/graphql`:
  - `AccountMemberDetails` → HTTP 401 `{"error":"Unauthorized"}`
  - `SearchOffers` with `awardSearch: true` → HTTP 200,
    `{"errors":[{"message":"Unhandled exception (Must be logged in to a valid account.)","extensions":{"code":"500"}}]}`
  So the gate is server-side, not only the client redirect.

## SearchOffers request (for a future signed-in provider)

POST JSON `{"operationName":"SearchOffers","variables":{"request":{"pos":null,"parties":null,
"flightSearchRequest":{"searchOriginDestinations":[{"origin":"LHR","destination":"JFK","departureDate":"2026-12-01"}],
"bundleOffer":false,"awardSearch":true,"calendarSearch":false,"flexiDateSearch":false,"nonStopOnly":false,
"currentTripIndexId":"0","checkInBaggageAllowance":false,"carryOnBaggageAllowance":false,"refundableOnly":false},
"customerDetails":[{"custId":"ADT_0","ptc":"ADT"}]}},"query":"query SearchOffers(…)"}`; no special headers
beyond `content-type` and cookies. Full captured query text:
`~/.agents/scratch/data/award-flights/virgin/s6/gql_3_SearchOffers_req.json` (scratch; re-sniff if gone).

Expected field mapping, read from the query's selection set — **never seen in a real response**:
`searchOffers.result.slice.flightsAndFares[]` = itinerary; `flight.segments[]` → `airline.code` +
`flightNumber`, `origin.code`, `destination.code`, `departure`, `arrival`, `metal.name` (aircraft),
`operatingAirline.name`; `flight.duration` → duration; `fares[]` → `content.cabinName` / `fareFamilyType`
(cabin), `price.awardPoints` (miles), `price.tax` + `price.currency`, `availability` (seats?),
`fareSegments[].cabinName` (mixed cabin when they differ), `isSaverFare`. Units and formats unverified.

## Public alternative: Reward Seat Checker (no sign-in, day-level only)

`https://www.virginatlantic.com/reward-flight-finder/results/month?origin=LHR&destination=JFK&month=12&year=2026`
is server-rendered HTML: one `article[data-cy="availability-card"]` per day (`h2` = "Tue 1") with
`div[data-cy="economy"|"premium"|"upper-class"]` holding e.g. `34,000pts`, plus `span[data-cy="saver-tag-icon"]`
on Saver prices. It gives the lowest one-way points per cabin per day for one passenger. It has no flight
numbers, times, taxes or seat counts, and only covers Virgin-operated nonstop routes (the origin/destination
`<select>` lists on `/reward-flight-finder`; 12 months ahead). It cannot fill the shared itinerary shape.
Sample seen 2026-10-13, LHR→JFK 2026-12-01: Economy 34,000 / Premium 17,500 (Saver) / Upper Class 125,000.

## Not verified

- Whether a signed-in session gets `SearchOffers` data from headless Chrome (Akamai may treat it differently).
- Partner (SkyTeam/Delta/ANA) award space, taxes, seat counts: all behind the login.
