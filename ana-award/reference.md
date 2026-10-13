# ANA `international_asw` protocol notes

Verified 2026-10-13 against the English site. Read this when extending or repairing `ana_award.py`.

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

Fare family `1400` is the ANA award chart, `1200` the Star Alliance chart. A recommendation is unbookable
when either seat count is negative. To continue to booking, `searchContentsForm` takes
`hiddenRecommendationId`, `hiddenDepartureFlightId`, `hiddenReturnFlightId`, `hiddenOutboundFfCode`,
`hiddenInboundFfCode`, `selectAward` and the two `…RadioGroup:radioGroup` fields; the page's own script
(`award-search-owd-pc.js`) fills them on click. That step and everything after it are unverified.

## Session and bot protection

- SSO cookies `personal` / `real` on `.ana.co.jp` identify the member; the booking app still demands the
  password for each new `JSESSIONID`. Backend idle timeout is 590 s (`asw-session-keeper.js`).
- Akamai cookies (`_abck`, `bm_sz`, `ak_bmsc`, `bm_sv`) come along from Chrome. `_abck` was unvalidated
  (`~-1~`) throughout and searches still worked, until volume triggered the tarpit described in SKILL.md.
  If throttling becomes the norm, the next step is minting a sensor-validated `_abck` in a real browser
  session and handing it to this client, not a faster retry.
