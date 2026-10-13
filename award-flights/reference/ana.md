# ANA Mileage Club (`international_asw`)

Verified 2026-10-13 against the English site. Field names below are what the browser submits; the tool
sets them on the page's own form and clicks its buttons. Read this when extending or repairing `providers/ana.py`.

## Shape of the app

A server-rendered JSF (Mojarra) application. Every step is a form POST back to the page's own URL carrying
`javax.faces.ViewState`; there is no JSON API. URLs carry a load-balancer node prefix (`/rei11f/`, `/rei12d/` …)
that the server assigns on redirect, so always follow redirects from the prefix-less entry URL and post to
the form's own `action`. Result URLs with `rand`/`rdtk` are one-shot and cannot be replayed with GET.

| Step | Page | Form | Submit |
|---|---|---|---|
| Entry | `award/search/roundtrip/award_search_roundtrip_input.xhtml?CONNECTION_KIND=JPN&LANG=en` | — | GET |
| Password step-up | `common/login_standard.xhtml` | the form containing `password` | its only submit button |
| Round-trip search | `…_roundtrip_input.xhtml` | `conditionInput` | the submit whose value is `Search` |
| Switch to one-way | same | `conditionInput` | extra field `toOneway=toOneway`, then search |
| Results | `…_roundtrip_result_owd.xhtml` | `searchContentsForm` | `nextButton` |

Search fields: `departureAirportCode:field` / `arrivalAirportCode:field` (IATA code; the `_pctext` display
twin accepts the code too), `awardDepartureDate:field` / `awardReturnDate:field` (`YYYYMMDD`, `_pctext`
`MM/DD/YYYY (TU)`), `boardingClass` (`CFF1` economy, `CFF4` premium economy, `CFF2` business, `CFF3` first),
`adult:count`, `youngAdult:count`, `child:count`, `infant:count`. In one-way mode the browser leaves both
return-date fields disabled; sending them, even empty, fails validation. `comparisonSearchType=on` switches
to the ±3-day page (`…_roundtrip_calendar.xhtml`), whose per-day status is filled in by JavaScript and was
not decoded. Component ids such as `j_idt1080` change between builds: locate buttons by value, forms by content.

## Result data

Flights are in the DOM: `.selectItineraryOutbound` / `.selectItineraryInbound`, one `td.selectItineraryCheck`
per itinerary whose `i[data-value]` is the flight id; `li#fareTypeNumber_<bound>_<id>_<fareFamily>` lists the
award types it qualifies for. Prices are inline JavaScript calls, defined in `asw-RecommendationList.js`:

`addRecommendation(recId, outFlightId, inFlightId, outFf, inFf, outAmt, inAmt, totalAmount, usePromotion,
outMile, inMile, milesCost, outLastSeat, inLastSeat, outSeats, inSeats, amountWithoutTax, tax,
rebookTotal, outWaitList, inWaitList, hasWaiver, totalBefore, boundInfoList)`

Fare families: economy `1400` ANA award chart and `1200` Star Alliance chart; business `800` ANA and `600`
Star Alliance. Premium economy and first were not observed. A recommendation is unbookable
when either seat count is negative; the page script (`isEnableRecommendationList`) treats only counts above 0
as open, so 0 is read as waitlist-only. That reading was not checked against the rendered page. To continue to booking, `searchContentsForm` takes
`hiddenRecommendationId`, `hiddenDepartureFlightId`, `hiddenReturnFlightId`, `hiddenOutboundFfCode`,
`hiddenInboundFfCode`, `selectAward` and the two `…RadioGroup:radioGroup` fields; the page's own script
(`award-search-owd-pc.js`) fills them on click. That step and everything after it are unverified.

## Session and bot protection

- SSO cookies `personal` / `real` on `.ana.co.jp` identify the member; the booking app still demands the
  password for each new `JSESSIONID`. Backend idle timeout is 590 s (`asw-session-keeper.js`).
- Search is POST → 302 (answered in ~0.2 s) → GET of the result page, which performs the actual search
  (4–5 s normally). The rate limit shows up on that GET: it hangs with no bytes.
- A plain HTTP client with Chrome's TLS fingerprint (`curl_cffi`) and Chrome's cookies completes the whole
  flow too; the first version of this tool worked that way. It was dropped for headless Chrome because the
  browser runs Akamai's own script and needs no borrowed Akamai cookies, not because it searches more:
  both transports hit the same rate limit.
- Headless Chrome announces itself as `HeadlessChrome/<ver>` in the user agent; with that string the
  booking host hangs on the very first request while `www.ana.co.jp` still answers. The tool overrides it
  with the installed Chrome's normal user agent.
- Akamai's `_abck` cookie stayed unvalidated (`~-1~`) in every working session, so its flag is not a
  useful health signal here.

## Rate limit

When the limit trips nothing is refused: the result-page GET never answers, for about 30 minutes, for every
client on the same network. Observed on 2026-10-13: five or six searches in four minutes tripped it (plain
HTTP client); three searches in four minutes tripped it (headless Chrome); six searches 150 s apart, after a
30-minute rest, all succeeded. `pace = 150` comes from that single successful run; the real threshold is
unknown. A search that returns `E_A01P01_0007` (cabin not offered) still counts.

## Round trips

The site prices a round trip as one search and returns outbound × return combinations; a round trip cost
the same miles as two one-ways in the cases compared (20,000 economy SZX⇄TYO). The provider searches
one-way only, like the other providers, so a return date means a second search. The provider's one-way path
(`toOneway`, then search) reuses the round-trip parser on a page with no return block.
