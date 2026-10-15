# Program coverage

State on 2026-10-13, from headless Chrome on a residential US connection, signed out unless noted.
"Checked" means a real search whose miles and taxes were compared with what the airline's page displayed.

## Working

| Provider | Program | Alliance | Account | Checked on | Notes |
|---|---|---|---|---|---|
| `delta` | Delta SkyMiles | SkyTeam | no | SEA⇄HND, HKG→NRT/HND | Shows partner flights (China Eastern seen). Dynamic pricing. |
| `alaska` | Alaska Atmos Rewards | oneworld | no | SEA⇄NRT, HKG→NRT | Shows partner flights (JAL, Cathay, Starlux, American seen). |
| `jetblue` | JetBlue TrueBlue | none | no | JFK→LAX, JFK→LHR | Own flights only observed. Mint is business. |
| `southwest` | Southwest Rapid Rewards | none | no | DAL→LAX, BWI→HNL | Single cabin. Site terms forbid automated fare collection; keep it personal and slow. |
| `frontier` | Frontier Miles | none | no | DEN→LAS, DEN→MCO | Single cabin; reports the Basic fare. Bundles add miles on top. |
| `qantas` | Qantas Frequent Flyer | oneworld | no | SYD→LAX, SYD→NRT | Returns Classic Reward and dynamic Classic Plus; tell them apart with `--brands`. 35–60 s per search. |
| `velocity` | Virgin Australia Velocity | none | no | SYD→MEL, SYD→PER, SYD→DOH, SYD→LAX | Shows partner flights (Qatar, United seen). "(any seat)" brands are cash fares converted to points. |
| `sas` | SAS EuroBonus | SkyTeam | no | CPH→EWR, ARN→EWR | `BONUS` brands are award seats; `FLEX` brands are cash fares converted to points (hundreds of thousands). Cloudflare stalled 5 of 13 result loads; rest a few minutes between runs. |
| `smiles` | GOL Smiles | none | no | GRU→MIA, GRU→LIS | Shows GOL plus partners (Avianca, TAP, Copa, American, Air France seen). Taxes in BRL; about a minute per search. `miles` is the regular member price; the Clube Smiles price is in the brand. |
| `azul` | Azul Fidelidade | none | no | VCP→FLL, VCP→LIS | Taxes in BRL including the redemption fee. Seats are not published. The site limited the address after about 15 loads in 30 minutes during development: use sparingly. |
| `ceair` | China Eastern Eastern Miles | SkyTeam | no | PVG→NRT, HKG→PVG, SZX→PVG | Miles matched the page; taxes are the API's value and were not checked against the page. Only MU/FM nonstops seen. The site's firewall cut in after about 12 loads in 20 minutes: use sparingly. |
| `ethiopian` | Ethiopian ShebaMiles | Star Alliance | no | ADD→IAD, ADD→FRA | Miles matched the page. Taxes are not quoted at search time. Only Ethiopian nonstops in economy seen. |
| `etihad` | Etihad Guest | none | no | AUH→JFK, AUH→LHR | Brands with a `G` (`YGVALUE`) are GuestSeat awards; the rest are cash fares converted to miles. |
| `ana` | ANA Mileage Club | Star Alliance | **yes** | see note | Shows Star Alliance partners. One cabin per search, 150 s pace, hard rate limit. The checked searches (SZX/HKG/CSX⇄TYO, round trip) ran through the standalone `ana-award` tool this provider was ported from; the provider's own one-way path has not completed a live search yet. |

## Which airline's seats show up where

A loyalty program sells seats on its partners, so an airline whose own program is behind a sign-in wall can
still be searched through a program that works. Each airline below appeared with a priced award fare in a
real search on 2026-10-13 (2026-12-01 or -02 departures); the route is the one it was seen on. Absence
from the list means "not seen in the searches run", not "not available".

| Alliance | Airline | Seen through | On |
|---|---|---|---|
| Star Alliance | United (UA) | `velocity` | SYD→NRT, SYD→LAX |
| Star Alliance | Singapore Airlines (SQ) | `velocity` | SYD→SIN, SEA→MEL |
| Star Alliance | Air Canada (AC), Turkish (TK), TAP (TP), Avianca (AV) | `smiles` | GRU→DXB |
| Star Alliance | Copa (CM) | `smiles` | GRU→MIA |
| Star Alliance | Ethiopian (ET) | `ethiopian` | ADD→IAD, ADD→FRA |
| Star Alliance | ANA (NH), Air China (CA), Shenzhen (ZH), Juneyao (HO) | `ana` (account) | SZX/HKG/CSX⇄TYO |
| oneworld | American (AA), British Airways (BA), Finnair (AY) | `alaska` | LHR→JFK, HEL→JFK |
| oneworld | Qatar (QR), Royal Air Maroc (AT) | `alaska` | DOH→JFK |
| oneworld | Japan Airlines (JL), Cathay Pacific (CX) | `alaska` | SEA→NRT, HKG→NRT |
| oneworld | Qantas (QF) | `alaska`, `qantas` | SYD→MEL |
| oneworld | SriLankan (UL), Oman Air (WY) | `alaska` | KUL→NRT, KUL→LHR |
| oneworld | Malaysia Airlines (MH) | `alaska`, `qantas` | KUL→LHR, KUL→SYD, SYD→KUL |
| SkyTeam | Delta (DL), Air France (AF), KLM (KL), Virgin Atlantic (VS) | `delta` | CDG/AMS/LHR→JFK |
| SkyTeam | China Eastern (MU) | `delta`, `ceair` | HKG→NRT, PVG→NRT |
| SkyTeam | China Airlines (CI) | `delta` | TPE→JFK |
| SkyTeam | Korean Air (KE) | `alaska` | PEK→SEA |
| SkyTeam | SAS (SK) | `sas` | CPH→EWR |
| none | Emirates (EK), ITA Airways (AZ) | `smiles` | GRU→DXB, GRU→CDG |
| none | Etihad (EY) | `etihad` | AUH→LHR |
| none | Aer Lingus (EI), Icelandair (FI), Starlux (JX), Hainan (HU) | `alaska` | LHR→JFK, HEL→JFK, HKG→NRT, PEK→SEA |
| none | LATAM (LA) | `delta` | SCL→MIA, GRU→MIA |
| none | JetBlue (B6), Southwest (WN), Frontier (F9), Virgin Australia (VA), GOL (G3), Azul (AD) | own program | — |

Not seen through any working program: Lufthansa group (LH, LX, OS), EVA (BR), Asiana (OZ), Thai (TG),
Iberia (IB, absent from `alaska` on MAD→JFK, MIA, BOG and MEX and from `qantas` on SYD→MAD), China Southern
(CZ, which has no partnership with any working program). `ethiopian` returned only Ethiopian's own flights, including on partner-only markets (FRA→JFK,
ICN→NRT, BKK→NRT, TPE→NRT came back empty), so it does not reach Star Alliance partners. `ana` is the
remaining route to the Star Alliance ones. `delta` showed no Korean Air on ICN→LAX or ICN→NRT.

The price is the searching program's price: another program may charge differently for the same seat, or
not have access to it. Partner space also differs by program, so a seat seen through `smiles` is not
proof that United or Aeroplan miles can book it.

## Needs the user's account

The airline's own site shows miles results only to signed-in members. None of these is implemented; each
would follow the `ana` pattern (copy the member's sign-in cookies from Chrome, drive the same headless
Chrome) and needs an account to build and verify against.

| Program | Alliance | What the site said | Notes |
|---|---|---|---|
| United MileagePlus | Star Alliance | "You must be signed-in to see flight results with miles." | `united.md` |
| Air Canada Aeroplan | Star Alliance | "Please sign in to book with Aeroplan points."; results URL also 403s headless Chrome | `aeroplan.md` |
| Singapore KrisFlyer | Star Alliance | "REDEEM FLIGHTS" opens the KrisFlyer login dialog | survey only |
| Lufthansa Miles & More | Star Alliance | award form submits to the login page | survey only |
| EVA Infinity MileageLands | Star Alliance | availability link is a member login with password and image CAPTCHA | survey only |
| Avianca LifeMiles | Star Alliance | date field redirects to LifeMiles SSO | survey only |
| TAP Miles&Go | Star Alliance | "Pay with miles" opens a login panel behind a Cloudflare human check | survey only |
| British Airways Executive Club | oneworld | redemption page redirects to BA login | survey only |
| Iberia Plus | oneworld | "Fly with Avios" redirects to Iberia login | survey only |
| Finnair Plus | oneworld | "You will need a Finnair Plus account" | survey only |
| Cathay Asia Miles | oneworld | submit button reads "Sign in to redeem" | survey only |
| Qatar Privilege Club | oneworld | "Search flights" with Avios ticked opens the Privilege Club login | `qatar.md` |
| JAL Mileage Bank | oneworld | both award entry points redirect to JMB member login | `jal.md` |
| Air France-KLM Flying Blue | SkyTeam | reward search redirects to Flying Blue login | `flyingblue.md` |
| Virgin Atlantic Flying Club | SkyTeam | "Must be logged in to a valid account." | `virgin.md`; a public day-level Reward Seat Checker exists |
| Korean Air SKYPASS | SkyTeam | "Book with miles" opens the login dialog | `korean.md` |
| China Southern Sky Pearl Club | SkyTeam | mileage form submits to "Log in … Membership Card No/Email" | survey only |
| Vietnam Airlines Lotusmiles | SkyTeam | choosing "Miles" opens "Lotusmiles Login" | survey only |
| Garuda GarudaMiles | SkyTeam | search opens "GarudaMiles Login"; home page sometimes sits behind a Cloudflare check | survey only |
| Asiana Club | Star Alliance | a signed-out "Mileage Seat Availability" calendar shows which cabins have award seats per flight (updated daily, no miles prices); booking and prices need login | survey only |
| Air China PhoenixMiles | Star Alliance | the public booking form has no miles option; the PhoenixMiles member portal shows only "Log in" signed out, with no award search form | survey only |
| Thai Royal Orchid Plus | Star Alliance | "Redeem Miles" opens "Royal Orchid Plus Member Sign In" | survey only |
| Air India Maharaja Club | Star Alliance | paying with points opens "SIGN IN TO YOUR MAHARAJA CLUB ACCOUNT" | survey only |
| Malaysia Airlines Enrich | oneworld | "Redeem Flight" search redirects to "Enrich - Log In" | survey only |
| Hainan Fortune Wings | none | award search opens "LOGIN TO FORTUNE WINGS" | survey only |
| Aer Lingus AerClub | oneworld (Avios) | "Find a Reward Flight by logging in with AerClub number." | survey only |
| Air Europa SUMA | SkyTeam | "Pay with Miles" search opens "Log in with SUMA" | survey only |
| Saudia Alfursan | SkyTeam | "Book with Miles" opens the login dialog | survey only |
| Gulf Air Falconflyer | none | "Pay with miles" opens "FalconFlyer Member Login" | survey only |
| Royal Air Maroc Safar Flyer | oneworld | "Buy with my miles" links to "Safar Flyer Login" | survey only |
| Oman Air Sindbad | oneworld | the Sindbad entry redirects to login; the public engine shows cash only | survey only |
| Aegean Miles+Bonus | Star Alliance | signed-out booking form has no miles option; the login dialog offers "Earn or redeem miles" | survey only |
| EgyptAir Plus | Star Alliance | "Award ticket" lands on an Account Number / PIN login form | survey only |
| South African Voyager | Star Alliance | "sign in with your SAA Voyager number and PIN"; signed-out results are cash only | survey only |
| Philippine Airlines Mabuhay Miles | none | "Sign in to book with miles" | survey only |
| Xiamen Airlines Egret Club | SkyTeam | award flights redirect to "Member Login" | survey only |
| Kuwait Airways Oasis Club | none | "Please login to redeem your awarded miles." | survey only |
| LATAM Pass | none | redemption results redirect to LATAM login | survey only |
| Emirates Skywards | none | "Log in to book Classic Rewards" | `emirates.md` |
| WestJet Rewards | none | "Sign in to … earn or redeem WestJet points."; results show cash only | survey only |

## Blocks headless Chrome

| Program | Alliance | What happened | Notes |
|---|---|---|---|
| American AAdvantage | oneworld | "I'm not a robot" CAPTCHA before any search; the search API answers error 309 | `american.md` |
| Aeromexico Rewards | SkyTeam | points search is open to guests, but its API answered 429 with an Akamai challenge three times out of three | `aeromexico.md` |
| Copa ConnectMiles | Star Alliance | guest search exists and showed results once during the survey; three later attempts got a DataDome slider CAPTCHA. `providers/copa.py` parses the one captured response but never completed a live search, so it is not registered | `copa.md` |
| ITA Airways Volare | SkyTeam | results page answers 403 with a Cloudflare security check; the booking form has no miles option | survey only |
| Turkish Miles&Smiles | Star Alliance | "Press & Hold to confirm you are a human" on the home page | survey only |

These are not worked around. They might behave differently in the user's own Chrome; that was not tried.

## Not determined

- Air New Zealand Airpoints: the booking form has no points option and AKL→SYD results were cash only
  (Airpoints Dollars are spent at checkout, so there may be no separate award search).
- Icelandair Saga Club and Royal Jordanian Royal Club: the public booking forms have no points option and
  results were cash only.
- LOT, Kenya Airways and Fiji Airways: no miles search on their own sites (LOT points to Miles & More,
  Kenya books awards by phone or email, Fiji's form is cash only).
- Aerolíneas Argentinas Plus: open signed out, only from the Argentine site (`/en-ar`, "Miles Search"
  toggle). EZE→MIA showed 35,000 / 45,000 miles from `GET api.aerolineas.com.ar/v1/flights/offers?…
  &awardBooking=true`, own flights only. Not built yet.
- Spirit Free Spirit: `www.spirit.com` did not resolve (NXDOMAIN) on the survey day.
- Hawaiian Airlines: its site now runs on Alaska's platform and showed AS-coded flights priced in Atmos
  points, so `alaska` covers it; no separate provider.

Survey evidence (screenshots, page text, traffic logs) is machine-local under
`~/.agents/scratch/data/award-flights/survey-a` and `survey-b` and is not part of the skill.
