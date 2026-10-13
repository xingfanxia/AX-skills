# American Airlines AAdvantage (aa.com) — protocol notes

Status 2026-10-13: **blocked**. No `providers/american.py` exists, because no real search response was
ever obtained and a parser written without one would be guesswork. Everything under "Observed" was seen
from the shared headless Chrome (`providers/_browser.py`), one residential IP, no sign-in.

## Observed

Bot protection is Akamai Bot Manager (`_abck` cookie, sensor POSTs to an obfuscated `/ylT5kMR2L/...` path,
`/_sec/verify?provider=adaptive`).

| Step | Result |
|---|---|
| `GET https://www.aa.com/homePage.do?locale=en_US` | 200, real home page. Sets `JSESSIONID`, `XSRF-TOKEN`, `_abck` (second field stayed `-1`, i.e. the sensor never validated the session, also after 20 s). |
| Results deep link, cold: `GET /booking/search?locale=en_US&pax=1&adult=1&child=0&type=OneWay&searchType=Award&cabin=&carriers=ALL&slices=[{"orig","origNearby","dest","destNearby","date"}]` (slices URL-encoded) | Document 200, title `Challenge Validation`, page shows a "Please confirm you're a human / I'm not a robot" checkbox CAPTCHA. No search request is made. |
| Same deep link after the home warm-up (15 s wait, 12 s gap) | `/booking/search` now loads the Angular app, which POSTs to `/booking/choose-flights/1?sid=<uuid>&locale=en_US`; that document is answered with the same CAPTCHA (`/challenge-assets/v7/captcha.html`). The page never reaches `/booking/api/search/itinerary`. |
| In-page `fetch` from the warmed-up home page: `POST /booking/api/search/itinerary`, JSON body, with and without `X-XSRF-TOKEN` echoed from the cookie | HTTP 200, `application/json`, 132 bytes: `{"error":"309","fareBenefits":[],"products":[],"responseMetadata":null,"slices":[],"utag":null}` |

`error: "309"` came back identically for an award search (SFO-NRT 2026-12-01, JFK-LAX 2026-11-10), a
revenue search, and an empty body `{}`. So it is decided before the body is read: a refusal, not "no
availability". Do not map it to an empty result list.

Evidence (scratch, not committed): `~/.agents/scratch/data/award-flights/american/s1/page.png` (cold
CAPTCHA), `s2/results.png` (CAPTCHA after warm-up), `s2/fetch.txt` (the 309 body), `probe*.py` (the
exact probes).

Load count for the whole investigation: 4 home loads, 2 deep-link loads, 5 API POSTs, each at least 10 s
apart. Nothing started hanging; the block was there from the first request, so it is not a rate limit.

## Not verified

- The request body of `/booking/api/search/itinerary`. The probes used a shape from the starting hints
  (`metadata{selectedProducts,tripType,udo}`, `passengers[{type,count}]`, `requestHeader{clientId:"AAcom"}`,
  `slices[{allCarriers,cabin,departureDate,destination,destinationNearbyAirports,maxStops,origin,originNearbyAirports}]`,
  `tripOptions{corporateBooking,fareType,locale,pointOfSale,searchType}`, `loyaltyInfo`, `version`,
  `queryParams{sliceIndex,sessionId,solutionSet,solutionId}`). The page's own request was never seen,
  so this shape is unconfirmed; the real one may carry the `sid` that `/booking/search` generates.
- The response shape (`slices[].pricingDetail[]` with `perPassengerAwardPoints`,
  `perPassengerTaxesAndFees`, `seatsRemaining`, `productType`) is also from the hints only. No field
  mapping, cabin naming, mixed-cabin flag, or segment time format has been checked against a real response.
- Whether award search works without sign-in (never got far enough to tell).
- Whether a headed Chrome or a different network gets past the challenge.

## To resume

Re-run `./sniff.py '<deep link>' <dir> --wait 30`. If `index.txt` shows a
`POST .../booking/api/search/itinerary` with a large body, the block is gone: take the request body and
response from that capture and write the provider as a sibling of `providers/alaska.py`, checking miles
and taxes against `page.txt`. If the title is still `Challenge Validation`, nothing has changed. The
CAPTCHA must not be solved or bypassed by the tool.
