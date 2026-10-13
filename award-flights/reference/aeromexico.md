# Aeromexico Rewards (aeromexico.com) — not implemented: points search is behind an Akamai bot challenge

Status as of 2026-10-13: **blocked**. There is no `providers/aeromexico.py`.
It is not a sign-in wall: the anonymous points form is fully usable, and the block is on the search API.

## What the site does (headless Chrome via `providers/_browser.Browser`, no account)

- Form: `https://www.aeromexico.com/es-mx/reserva?amrpoints=true` (the US storefront sends points users
  here: "Continue on our Mexico site"). The "Usar mis Puntos Aeroméxico Rewards" toggle is on, no sign-in asked.
- "Buscar vuelo" navigates (full page load) to the results deep link:
  `https://www.aeromexico.com/bf/es-mx/reserva/opciones?amrpoints=true&itinerary=MEX_JFK_2026-12-01&leg=1&travelers=A1_C0_I0_PH0_PC0`
  (document answers 200, 81 KB React app).
- That page calls, on `amx-c-mtpsbk-pd.aeromexico.com`: `GET /tc/od/origin`, `GET /tc/pcc/getPccInfo`,
  `GET /tc/region/regionByRoute` (loyalty zones, e.g. MEX=Z01, JFK=Z05), `POST /tc/cabin/names/byRouteRegion` — all 200.
- The search itself: `POST https://amx-c-bkngbk-pd.aeromexico.com/bc/ow/search/flight/points`
  - body: `{"accountNumber":"","arrivalAirportLoyaltyZone":"Z05","arrivalAirportRegion":"USA","cobrandCard":"",
    "departureAirportLoyaltyZone":"Z01","departureAirportRegion":"LOC","planMultiplica":"","promoCode":"","tier":""}`
  - the search parameters travel as headers: `itinerary: MEX_JFK_2026-12-01`, `travelers: A1_C0_I0_PH0_PC0`,
    `legregion: USA`, `store: mx`, `currency: MXN`, `language: ES`, `locale: MZ`, `citycode: D5GE`, `channel: web`,
    `isnewbf: true`, `access_type: client_credentials`, `authorization: Atmosphere realm=…atmosphere_app_id=WorkAndCoApp…`
    (guest token from `POST /api/oauth2/token?grant_type=client_credentials`), `x-transactionid`.
  - empty `accountNumber`/`tier` and a guest token: the page itself issues this call signed out.

## The block

- The points call answers **429** with body `{"cpr_chlge":"true","t":"287910558"}` — Akamai Bot Manager's
  crypto (proof-of-work) challenge for API calls. Response headers are Akamai's (`grn`, `edgescape`, new
  `ak_bmsc`/`bm_s` cookies). The success shape of this endpoint was never seen.
- The app treats the 429 as a failed search and within ~0.2 s redirects to `/es-mx` → `/new/es-mx` (home).
  No results, no error text, no sign-in prompt. That is the "search returns to the home page" symptom.
- In the survey run the home page then fetched `/_sec/cpr/params` (returns the challenge script URL) and
  posted to it (202); results were still not shown.
- Seen 3 times out of 3: survey (US home → Mexico form → click), run1 (es-mx home 12 s → form, typed at
  140 ms/key, real clicks → click), run2 (home 18 s with mouse movement → deep link).
- In run2 the warm-up itself degraded: the home document reloaded into Akamai "Access Denied"
  (403, `Reference #18.f172cd17.1791884038.37528045`), and `_abck` stayed `~-1~`. In run1 `_abck` was `~0~`
  (sensor accepted) and the points call was challenged anyway, so a clean sensor cookie does not avoid it.
- Cash calendar calls from the same form (`GET /api/v4/calendar/detailed/search?cityPairDateCodes=MEX_JFK_2026-11-28
  &travelersCode=A1_C0_I0_PH0_PC0&searchType=ONE_WAY&store=MX`) answered 200 in the survey run; they carry MXN
  fares only, no points.

## Not tried, on purpose

- Computing or replaying the proof-of-work, calling the points API outside the page's own flow, stealth
  libraries, proxies, a headed or signed-in browser. The tool's rule is to stop at a challenge.
- MEX→MAD: same endpoint, not searched once MEX→JFK was challenged three times.
- Whether a signed-in session or an ordinary desktop browser gets the challenge too is unknown.

## If this is picked up again

Start from the results deep link above with `sniff.py` and look at the status of `/bc/ow/search/flight/points`.
If it answers 200, the jetblue pattern fits (navigate to the deep link, catch the page's own response); the
response mapping still has to be worked out from a real body. Cabin names for a route come from
`/tc/cabin/names/byRouteRegion`.

Evidence: `~/.agents/scratch/data/award-flights/aeromexico/run1` (form flow: `net.txt`, `s035.png` filled form,
`s037.png` home after the click) and `run2` (`n014.body`/`n014.meta` = the 429 and its request, `n004.body` and
`home.png` = Access Denied, `net.txt`); earlier survey in `survey-b/aeromexico/load3`. Cost: 8 page loads here
plus about 5 in the survey.
