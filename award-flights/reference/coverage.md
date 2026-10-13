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
| `qantas` | Qantas Frequent Flyer | oneworld | no | SYD→LAX, SYD→NRT | Returns Classic Reward and dynamic Classic Plus; tell them apart with `--brands`. 35–60 s per search. |
| `sas` | SAS EuroBonus | SkyTeam | no | CPH→EWR, ARN→EWR | `BONUS` brands are award seats; `FLEX` brands are cash fares converted to points (hundreds of thousands). Cloudflare stalled 5 of 13 result loads; rest a few minutes between runs. |
| `etihad` | Etihad Guest | none | no | AUH→JFK, AUH→LHR | Brands with a `G` (`YGVALUE`) are GuestSeat awards; the rest are cash fares converted to miles. |
| `ana` | ANA Mileage Club | Star Alliance | **yes** | see note | Shows Star Alliance partners. One cabin per search, 150 s pace, hard rate limit. The checked searches (SZX/HKG/CSX⇄TYO, round trip) ran through the standalone `ana-award` tool this provider was ported from; the provider's own one-way path has not completed a live search yet. |

Alliance reach through partner awards: Star Alliance via `ana`, oneworld via `alaska` and `qantas`, SkyTeam
via `delta`. That shows the partner's seats at that program's price; another program may price the same
seat differently or not see it.

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
| LATAM Pass | none | redemption results redirect to LATAM login | survey only |
| Emirates Skywards | none | "Log in to book Classic Rewards" | `emirates.md` |

## Blocks headless Chrome

| Program | Alliance | What happened | Notes |
|---|---|---|---|
| American AAdvantage | oneworld | "I'm not a robot" CAPTCHA before any search; the search API answers error 309 | `american.md` |
| Aeromexico Rewards | SkyTeam | points search is open to guests, but its API answered 429 with an Akamai challenge three times out of three | `aeromexico.md` |
| Copa ConnectMiles | Star Alliance | guest search exists and showed results once during the survey; three later attempts got a DataDome slider CAPTCHA. `providers/copa.py` parses the one captured response but never completed a live search, so it is not registered | `copa.md` |
| Turkish Miles&Smiles | Star Alliance | "Press & Hold to confirm you are a human" on the home page | survey only |

These are not worked around. They might behave differently in the user's own Chrome; that was not tried.

## Not determined

Air New Zealand Airpoints: the home page offered no points search; nothing further was tried.

Survey evidence (screenshots, page text, traffic logs) is machine-local under
`~/.agents/scratch/data/award-flights/survey-a` and `survey-b` and is not part of the skill.
