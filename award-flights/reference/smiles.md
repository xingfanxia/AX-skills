# GOL Smiles (smiles.com.br)

Verified 2026-10-13, signed out, headless Chrome via `_browser.Browser`. Routes run: GRU→MIA, GRU→LIS,
FEN→HND, FEN→ZQN (empty), all 2026-12-01. No warm-up visit needed; no CAPTCHA or block seen.

## Results page (deep link)

`https://www.smiles.com.br/mfe/emissao-passagem/?adults=1&cabin=ALL&children=0&departureDate=<epoch ms>&infants=0&isElegible=false&isFlexibleDateChecked=false&returnDate=&searchType=g3&segments=1&tripType=2&originAirport=GRU&originCity=&originCountry=&originAirportIsAny=false&destinationAirport=MIA&destinCity=&destinCountry=&destinAirportIsAny=false&novo-resultado-voos=true`

- `departureDate`: the provider sends 15:00 UTC (noon in Brasília) of the travel day; the page turns it into
  `departureDate=YYYY-MM-DD` for the API. `tripType=2` is one-way.
- The page shows an "Acesse ou crie a sua conta" prompt that does not block results. It also calls
  `members-green.smiles.com.br/v1/members` and gets 452 "Token incorreto." signed out; harmless.

## Search API

`GET https://api-air-flightsearch-green.smiles.com.br/v1/airlines/search?cabin=ALL&originAirportCode=GRU&destinationAirportCode=MIA&departureDate=2026-12-01&memberNumber=&adults=1&children=0&infants=0&forceCongener=false&cookies=_gid%3Dundefined%3B`

Request headers the page sends: `x-api-key: <key from the page's bundle>`, `channel: WEB`, referer smiles.com.br.
The provider never stores the key: it catches the page's own call and reuses that call's `x-api-key` and
`channel` for the second one.

- Tab "GOL e Avianca" (the default, `searchType=g3`) = `forceCongener=false`. Answer `resultType: "G3"`,
  flights with `airline.code` G3 and AV.
- Tab "Outras companhias" (partner airlines) = the same URL with `forceCongener=true`. It is open signed out.
  The click does not change the page URL; the provider fetches this URL from inside the page instead of
  clicking. Seen: AA, AF, KL, TP, UX, AT, AZ, CM. Answer `resultType: "congener"`.
- Empty market: both calls answer 200 with `flightList: []` (FEN→ZQN) → the provider returns `[]`.

Answer shape: `requestedFlightSegmentList[0].flightList[]`, one entry per itinerary **and cabin/fare bucket**
(the same flights appear again for another cabin, and Avianca repeats them at a higher price). The provider
merges entries whose legs (marketing carrier, flight number, departure time) are equal and keeps the lowest
miles per cabin.

| Output | Source |
|---|---|
| segment flight / from / to / dep / arr | `legList[].marketingAirline.code` + `flightNumber`, `departure.airport.code`, `arrival.airport.code`, `departure.date`, `arrival.date` (local, `YYYY-MM-DDTHH:MM:SS`) |
| aircraft | `legList[].equipment` (IATA code, small name table in the provider) |
| operated_by | `legList[].operationAirline.name` (" (G3)" suffix cut) |
| duration_min | `duration.hours`, `duration.minutes` |
| cabin | entry `cabin`: ECONOMIC→economy, COMFORT (GOL Premium Economy, shown as "Premium")→premium, PREMIUM_ECONOMIC→premium, BUSINESS→business. FIRST→first is assumed, never seen |
| mixed | any `legList[].cabin` differs from the entry cabin (typical: economy domestic feeder) |
| miles | `fareList[]` with `type: "SMILES"` → `miles`: the price for ordinary members ("Tarifa para clientes Smiles") |
| brand | `"Smiles; Clube Smiles <n>"`, n = `fareList[type=SMILES_CLUB].miles` |
| seats | entry `availableSeats` (looks capped at 9) |
| tax (BRL) | GOL: `fareList[].g3.costTax`. Others: boarding-tax call below |

Other fare types are ignored: `SMILES_MONEY`, `SMILES_MONEY_CLUB` (miles + cash), `MONEY` (cash only).
The headline price on the results page ("A partir de N milhas") is the **Clube Smiles** price
(`SMILES_CLUB`: paid subscribers, Diamante and Magno members), not the one reported as `miles`. Opening
"Selecionar tarifa" shows both.

## Taxes

Results rows show no taxes. For GOL flights `g3.costTax` is the BRL tax: the page's cash price equals
`MONEY.money + costTax` (GRU→MIA G3 1520: 1686.34 + 341.64 = "R$ 2.027,98").

For every other carrier the page asks only after "Selecionar tarifa" → choose a fare → "Confirmar seleção":

`GET https://api-airlines-boarding-tax-green.smiles.com.br/v1/airlines/flight/boardingtax?type=SEGMENT_1&uid=<flight uid>&fareuid=<fare uid>&adults=1&children=0&infants=0`
(header `channel: WEB`, no API key; `uid`/`fareuid` come from the search answer and change on every search).

`totals.totalBoardingTax.money` is the BRL total the page shows under "Taxas da viagem" (= `boardingTaxMoney`
airport fees + `airlineTax` carrier surcharge). TP 88 GRU→LIS: 117.10 = page "R$ 117,10".

Call budget: one call per fare was ~58 calls for GRU→MIA, and at 250 ms spacing the API stopped answering at
call 35 (`TypeError: Failed to fetch`; the same URLs answered again minutes later, so a burst limit). The
provider therefore asks **once per routing**: key = (marketing carrier, from, to) of every leg + cabin +
the entry's `airlineTax`, 800 ms apart, hard cap 40 calls per search. Seen 17–20 calls per search. Two
itineraries with the same key that were both asked returned identical totals (CM 758 / CM 841 via PTY,
409.04). So a partner fare's tax is the tax of the first fare with the same routing, not its own call.

HTTP 452 with `errorCode: "113"` ("...indisponibilidade de assentos...") means that fare cannot be booked
any more. The provider drops that fare and asks the next one with the same key. Fares that share a key with
an answered one are not asked, so some of them may still be unbookable.

## Limits and unknowns

- A search takes ~25–60 s (one page load, two search calls, up to 20 tax calls). `pace = 15`.
- Only the burst limit above was seen. If boarding-tax calls fail again the provider raises `ProviderError`
  for the whole search instead of reporting fares without taxes.
- `adults > 1`: the page says prices are per traveller; not run. Taxes are always asked for one adult.
- `cabin` is always `ALL`; the provider's `cabin` argument is unused.
- GOL `costTax` was checked against the page on one flight only (GRU→MIA).
- Round trips, flexible dates and "any airport" (`originAirportIsAny`) were not explored.

- 2026-10-13, later the same day: in one run of four partner-heavy searches about 15 s apart (GRU→CDG,
  DXB, IST, JFK), the first two answered and the next two failed with the partner-airline call returning
  `TypeError: Failed to fetch`. Treat two searches in a row as the practical budget and rest before more.
