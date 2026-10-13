# Flying Blue (Air France / KLM) — protocol notes

Status 2026-10-13: **no provider shipped. Award search needs a signed-in Flying Blue account.**
`providers/flyingblue.py` does not exist; nothing below about reward responses is verified.

## What was observed (headless Chrome via `_browser.Browser`, anonymous, US IP)

Site: Angular SPA on `www.klm.com` and `wwws.airfrance.us` (same stack), GraphQL at `/gql/v1`
with persisted queries, Akamai Bot Manager in front (`sensor_data` posts).

Deep-link form (date is `YYYYMMDD`, one-way = one connection):

    https://www.klm.com/search/offers?pax=1:0:0:0:0:0:0:0&cabinClass=ECONOMY&activeConnection=0
        &connections=AMS:A:20261201%3EJFK:A&bookingFlow=REWARD        (LEISURE = cash)

- `bookingFlow=REWARD`, KLM and Air France alike: the SPA goes `/search/offers` → `/search/landing`
  → `/endpoint/v1/oauth/login?ref=…/search/landing/login-result/<uuid>` → `/endpoint/v1/oauth/redirect`
  (302) → `api.airfranceklm.com/travel/cid/authorize` (302) → `https://identity.airfranceklm.com/login/otp`
  ("Log in — Flying Blue number or e-mail address"). It never sends an offers query while logged out.
  Accepting the cookie banner first does not change this.
- `/search/advanced?…&bookingFlow=REWARD` and `/search/open-dates/0?…&bookingFlow=REWARD` only render
  the empty search form; no fare or calendar query is sent.
- `bookingFlow=LEISURE` (cash) works anonymously, but only after a home-page visit **and clicking
  "Accept" on the cookie dialog**; without consent the search button spins forever and no query is sent.
  The page then POSTs `/gql/v1?bookingFlow=LEISURE&operationName=SearchResultAvailableOffersQuery`:

      variables: {activeConnectionIndex: 0, bookingFlow, searchStateUuid,
                  availableOfferRequestBody: {commercialCabins: ["ECONOMY"], passengers: [{id: 1, type: "ADT"}],
                    requestedConnections: [{origin: {code, type: "AIRPORT"}, destination: {…}, departureDate: "YYYY-MM-DD"}],
                    bookingFlow, withUpsellCabins: true}}
      extensions: {persistedQuery: {version: 1, sha256Hash: "2fefa196…5795"},
                   hashcash: {version: 2, timestamp, hash: "<sha256 hex>-<nonce>"}}

  `hashcash` is a proof-of-work the page's own JavaScript computes per request. Sibling call:
  `SharedSearchLowestFareOffersForSearchQuery` (±3-day strip).
- A hand-made `fetch('/gql/v1?…SearchResultAvailableOffersQuery')` from inside the warmed-up page, with
  the REWARD body and no `hashcash`, got **HTTP 403 "Access Denied" from Akamai** (edgesuite reference
  page), i.e. the Alaska-style in-page fetch is not available here; the request has to come from the SPA.

## Cash response shape (for orientation; the reward shape is expected to be the same query)

`data.availableOffers.offerItineraries[]`:
- `activeConnection.segments[]`: `marketingFlight.carrier.code` + `.number` (zero-padded, "0641"),
  `marketingFlight.operatingFlight.carrier`, `origin.code`, `destination.code`,
  `departureDateTime` / `arrivalDateTime` (local, `YYYY-MM-DDTHH:MM:SS`), `equipmentName`, `duration` (min).
- `activeConnection.duration` = total minutes.
- `upsellCabinProducts[].connections[0]`: `cabinClass` (ECONOMY / PREMIUM / BUSINESS / FIRST family),
  `numberOfSeatsAvailable`, `price`, `tax` (null in cash flow), `fareFamily`.
Where miles and the cash tax sit in a REWARD response was **not observed**.

## Limits seen

~10 page loads spaced ≥10 s: no CAPTCHA, no throttling. The only hard answers were the login redirect
and the Akamai 403 on the hand-made fetch.

## To make this provider work

It needs a Flying Blue session in the headless profile (sign-in is e-mail OTP or password on
identity.airfranceklm.com, itself behind Akamai). Then: warm up home page, accept cookies, `goto` the
REWARD deep link and catch `SearchResultAvailableOffersQuery` with `Browser.json_after`
(`all_cabins` is probably True since `withUpsellCabins` returns every cabin). Scratch evidence:
`~/.agents/scratch/data/award-flights/flyingblue/` (`x1` cash run, `x2` login redirect trace, `s3/page.png`).
