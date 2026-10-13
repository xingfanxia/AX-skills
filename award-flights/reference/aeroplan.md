# Aeroplan (aircanada.com) — protocol notes

Status 2026-10-13: **blocked**. No itinerary was ever retrieved; `providers/aeroplan.py` only
reproduces the attempt and raises `ProviderError`. Nothing below about the search API was observed.

## Observed (headless installed Chrome via `_browser.Browser`, one residential IP, US west coast)

| Step | Result |
|---|---|
| `GET https://www.aircanada.com/ca/en/aco/home.html` | 200, renders normally (redirects client-side to `/home/ca/en/aco/flights`) |
| Home form, tick "Book with Aeroplan points" (`#bkmg-desktop_searchTypeToggle`) while signed out | Form shows "Please sign in to book with Aeroplan points." |
| `GET https://www.aircanada.com/aeroplan/redeem/availability/outbound?org0=YVR&dest0=NRT&departureDate0=2026-12-01&ADT=1&YTH=0&CHD=0&INF=0&INS=0&lang=en-CA&tripType=O&marketCode=INT` | 403, Akamai page: "Access Denied — You don't have permission to access …/aeroplan/redeem/availability/outbound? on this server", `errors.edgesuite.net` reference |

The 403 was the same in all three variants tried: cold, after a 12 s home-page warm-up (address-bar
navigation), and after warm-up via in-page `location.assign` (same-origin referer). Every attempt was denied (4 of 4, counting the provider run).

Akamai Bot Manager is active: the home page posts `sensor_data` to `/hq9A1X/…` and sets `_abck`,
`bm_sz`, `bm_s`. The `_abck` second field stayed `-1` in every session, including after clicks and
typing on the form, i.e. the sensor never marked the session as validated.

No CAPTCHA was shown at any point; the denial is a plain 403 document. The `air-bounds` request was
never issued because the results app never loaded.

## Not determined

- Whether the 403 is the bot verdict, the missing sign-in, or both. The site's own form says sign-in
  is needed for points booking; a signed-out visitor in a normal Chrome would settle it.
- Whether submitting the home form signed out leads to a sign-in page. Form automation stalled on the
  trip-type popover (the "One-way" radio label would not take a click) and was not pursued.
- Request rate limits: only 9 page loads were made, ≥10 s apart, none hung.

## Unverified starting hints (from before this block; not seen in this investigation)

- Search API: `POST https://akamai-gw.dbaas.aircanada.com/loyalty/dapidynamic/1ASIUDALAC/v2/search/air-bounds`
- Response: `data.airBoundGroups[]` (`boundDetails` + `airBounds[]` with prices in miles and cash,
  `availabilityDetails` with cabin and quota) and `dictionaries` (flight, aircraft, location).

If the page ever loads, `./sniff.py '<deep link>' OUT --wait 40` after a home visit will show the
real request and response; write the mapping from that, not from the hints above.

## Evidence

Under `~/.agents/scratch/data/award-flights/aeroplan/`: `s1/page.png` + `page.txt` (cold 403),
`s2/` (warm-up then 403, `index.txt` shows the sensor posts), `s3/` (in-page navigation, 403,
`controls.txt` lists the form's element ids), `s4/2-points.png` (sign-in message on the form).
