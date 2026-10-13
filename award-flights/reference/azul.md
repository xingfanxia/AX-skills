# Azul Fidelidade (`providers/azul.py`)

Investigated 2026-10-13 from one residential IP, headless installed Chrome via `_browser.Browser`, no sign-in.

**Status: partial.** Points results are visible signed out and the mapping is checked against the page, but
the provider's own end-to-end run never completed: the site rate-limited the IP (see Limits) while the form
automation was still being debugged. What ran live and what did not is listed under "Not verified".

## Flow

1. Home: `https://www.voeazul.com.br/br/pt/home`, wait 8 s.
2. First search of a browser session goes through the home form:
   - click the `Origem` field, type the IATA code, click the `[role="option"]` whose text starts with the code
     (`data-cy="autocomplete-options-item-0"`, text "VCP São Paulo - Campinas"); focus moves to `Destino`, same again;
   - the calendar opens with `input[aria-label="Data de ida"]` focused; typing `01122026` fills `01/12/2026`;
   - button "Selecionar apenas data de ida" (one-way), checkbox `[data-cy="checkbox-points"]` ("Usar pontos Azul"),
     button "Buscar passagens".
3. The browser loads the results page as a full document:
   `https://www.voeazul.com.br/br/pt/home/selecao-voo?c[0].ds=VCP&c[0].std=12/01/2026&c[0].as=FLL&p[0].t=ADT&p[0].c=1&p[0].cp=false&f.dl=3&f.dr=3&cc=PTS`
   (`std` is MM/DD/YYYY, `cc=PTS` is the points switch, `p[0].c` the adult count). The page calls
   `POST b2c-api.voeazul.com.br/authentication/api/authentication/v1/token`,
   `DELETE b2c-api.voeazul.com.br/reservationavailability/api/reservation/availability/v1/bookings`, then
   `POST https://b2c-api.voeazul.com.br/tudoAzulReservationAvailability/api/tudoazul/reservation/availability/v6/availability`
   with a body starting `{"criteria":[{"departureStation":"VCP","arrivalStation":"FLL","std":"12/01/2026","departureDate":"2026-12-01"}],"passengers":[{"type":"ADT","count":"1","companionPass":false}],"flexibleDays":{...`
   (full body and request headers were not captured). The provider catches that response (HTTP 200, 6-22 KB).
4. Later searches in the same browser open the results URL of step 3 directly.

**The results deep link fails cold.** Opened as the first page, or after only a home-page visit (3 of 3 tries),
it shows "Ops! Tivemos um problema — Infelizmente não foi possível concluir sua solicitação…": the token and
`DELETE bookings` calls run, the availability call is never made. After one form search the same kind of URL
for another route (VCP→LIS, set with `location.href`) worked, 1 of 1. The form search leaves a `VoeAzul`
cookie (`{"token": <JWT valid 24 h>}`) that the cold page does not have; whether that cookie is the cause was
not tested.

## Response → output

`data.trips[0].journeys[]`, one per itinerary:

| Output | Source |
|---|---|
| segment `flight` | `segments[].identifier.carrierCode` + `flightNumber` |
| `from` / `to` | `segments[].identifier.departureStation` / `arrivalStation` |
| `dep` / `arr` | `segments[].identifier.std` / `sta` (local, `2026-12-01T23:05:00`, cut to minutes) |
| `aircraft` | `segments[].equipment.name` ("Airbus A330-200"), else `.type` ("73H") |
| `operated_by` | `segments[].identifier.operatedBy` (`AD` → Azul; `UX` seen on Air Europa codeshares, left as code) |
| `duration_min` | `journeys[].identifier.duration` `{days, hours, minutes}` (equals the page's "8h 50m") |
| `cabin` | highest of `fares[].cabin.segmentsCabin[].type`, else `fares[].productClass.category` ("Economy", "Business") |
| `mixed` | `fares[].cabin.mixed` (false on everything seen; `cabin` is null on some nonstops) |
| `miles` | `fares[].paxPoints[].levels[]` with `paxType: "ADT"` and `fareMoney: 0` → `points.discountedAmount` |
| `tax`, `currency` | same level: `totalMoney` (= `taxesAndFees` + `convenienceFee`), `currencyCode` (`BRL`) |
| `brand` | `fares[].productClass.name` |
| `seats` | always `None` (see below) |

- **Discounted points.** The page headlines `discountedAmount` (161.020) and strikes through `amount`
  (166000), tagged "Desconto ao titular": "O desconto na tarifa e a taxa de resgate diferenciada do nível
  são validos apenas para reservas em que o titular da conta seja um dos viajantes." The provider reports the
  headline; a booking where the account holder does not travel costs `amount` (3 % more in economy, 1 % in
  business on the fares seen).
- **Points + cash is not output.** Each fare has several `paxPoints[]` entries: `amountLevel: 1` is all points
  (`fareMoney: 0`), levels 2-5 trade points for cash (level 2 for VCP→FLL: 12.901 points + R$ 2.891,77, the
  page's "ou … pontos + R$ …" line). As a fare row it would have the fewest miles and win the CLI's
  cheapest-per-cabin pick, so it is left out.
- **`convenienceFee`** (R$ 135,90, the "taxa de resgate") is cash charged on top of airport taxes; it is in `tax`.
- **Seats.** `segments[].legs[].legInfo.remainingSeats` (108, 146…) is unsold seats on the whole aircraft, not
  award seats in the fare, so it is not reported.
- **Nearby airports.** A LIS search also returns VCP→OPO journeys in the same `trips[0]` (page: "Além de Lisboa,
  veja também voos para Porto"). Journeys whose own origin/destination differ from the request are dropped.
- Journeys with `status.available: false` (`reason: "Tarifa indisponível"`, page "Indisponível"; the Air Europa
  connections via MAD) and fares with `available: false` are dropped.

## Empty results

- Airport the form does not offer: no `[role="option"]` starts with the typed code → `[]`, no search made.
  Written from the form's observed behaviour; not run against a real unsold airport.
- What the API answers for a sold pair with no flights was not observed. The provider returns `[]` for empty
  `trips`/`journeys` and raises `ProviderError` for a non-200 or a body without `data`.

## Checked against the page (2026-12-01)

Captured API bodies run through the provider's mapping (`scratch/data/award-flights/azul/offline.py`), compared
with the page text and screenshots of the same loads (`azul/live1/a7.png`, `a8.png`, `lis_page.txt`):
- VCP→FLL AD 8704 23:05–05:55+1, 8h 50m: economy 161,020, business 891,000 = the fare panel's "161.020 pontos" /
  "891.000 pontos".
- VCP→LIS AD 8750 and AD 8752, 10h 5m: economy 223,740 = page "223.740 pontos". VCP→OPO AD 8800: 134,640 = page.
- Taxes: the page shows no cash amount for the all-points price before a fare is selected (the summary stays
  "Taxas e impostos R$ 0,00"). Indirect check: its points + cash line is `fareMoney` + the same taxes and fee —
  FLL 2.489,00 + 402,77 = R$ 2.891,77; LIS 1.994,00 + 195,07 = R$ 2.189,07, both as displayed.

## Limits observed

About 15 page loads in 30 minutes. The last 8 were home-page loads in two bursts ~18 s apart (two failed test
runs that reloaded the home page per route). The next load got Azul's block page instead of the home page:
"Oops! Just a moment. We detected unusual activity from your IP. Access is temporarily limited. Please try
disabling VPN, clearing cookies, or wait a moment." (screenshot `scratch/data/award-flights/azul/ip-limit.png`,
served from `cybersecurity.voeazul.com.br` assets). Work stopped there; how long the limit lasts is unknown.
The provider recognises that page and raises `ProviderError`. No CAPTCHA was seen. The site runs Akamai Bot
Manager (`_abck`, `bm_*` cookies, `sensor_data` posts). `pace` is 12 s as a guess; nothing shows it is enough.

## Not verified

- **The provider end to end.** The form steps were each done by hand in one live session and returned results;
  `_pick`'s final version (choosing the option by its text) and the whole `_form` → `_catch` chain have not run
  since the last two fixes. First thing to do once the IP limit clears:
  one run of the brief's test command for VCP→FLL, then VCP→LIS in the same session.
- Deep link through `page.goto` in a warmed session (it was done with `location.href`), and how long a
  session stays warm.
- `adults` > 1 (the provider warms up with a 1-adult form search, then opens the deep link with `p[0].c=N`).
- Domestic routes (VCP→REC): product class names there, `cabin`/`mixed` on connections, taxes.
- Any cabin other than "Economy" and "Business"; a category outside `CLASSES` is skipped.
- The availability request's headers and full body.
