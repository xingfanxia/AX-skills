---
name: award-flights
description: Search award (miles/points) flight space and prices across airline loyalty programs from the command line - Delta, Alaska, JetBlue, Southwest, Frontier, Qantas, Velocity, SAS, GOL Smiles, China Eastern, Ethiopian, Etihad and ANA. Use for questions about award availability, how many miles a route costs, or comparing programs for a trip.
---

# Award flights

`award.py` (next to this file) asks each airline's own website for award space and prints one table per
program, direction and date: itineraries with miles, cash taxes and seats left per cabin. It drives a
throwaway headless Chrome (installed Google Chrome, temporary profile, no window). Needs macOS, Chrome, `uv`.

```bash
./award.py delta,alaska SEA TYO,HND 2026-12-01 2026-12-08 --cabin Y,J
./award.py all JFK LHR 2026-12-01 --json          # every registered program, full data
./award.py ana SZX,HKG TYO 2026-12-01 --cabin Y,J  # signed-in program, slow on purpose
```

Arguments: programs (comma-separated, or `all`), origins, destinations, departure date, optional return
date. Every search is one-way; a return date adds the reverse direction as its own search and table,
because most programs price each direction separately. Cabins are `Y`, `PY`, `J`, `F` (default `Y,J`).
Prices are per passenger on Delta, Alaska and Etihad (checked with two adults); the other programs were
only checked with one adult. Each cell is the cheapest fare in that cabin; `mixed` means some segment is in a lower cabin. `--json`
returns every fare of every itinerary.

Several programs list cash fares converted to miles next to real award seats (Qantas Classic Plus, SAS
FLEX, Velocity "any seat", Etihad brands without a `G`); they show up as six-figure prices. `--awards-only`
drops them, `--brands` labels every price. Use one of the two before quoting a price as "the award rate".

Airport codes are passed to the airline as typed. City codes (`TYO`, `NYC`, `LON`) work only where the
airline's own site accepts them; an airline that does not fly or sell a market returns an empty table,
which is an answer, not a failure.

## Programs

See [reference/coverage.md](reference/coverage.md) for the full list: which programs work, which need the
user's account, which block automated browsers, and what was tried. Read it before telling the user a
program "is not supported", and before starting work on a new one.

Which program to search is not the same as which airline flies the route: miles of one program book
partner flights. For a trip, search the programs where the user holds miles plus the alliance partners
of the airlines that fly the route.

## Programs that use the user's account

ANA only shows award space to a signed-in member. That provider copies the member's `ana.co.jp` sign-in
cookies from the user's Chrome profile (one Keychain read of "Chrome Safe Storage"; `ANA_CHROME_PROFILE`
picks a profile other than `Default`) and answers ANA's password re-confirmation from `ANA_PASSWORD` or the
1Password item named by `ANA_OP_ITEM` (default `ANA`, optional `ANA_OP_VAULT`). The password step runs once
per run; never wrap it in a retry loop, because repeated bad passwords lock the mileage account. ANA searches
one cabin at a time and rate-limits hard: details in [reference/ana.md](reference/ana.md).

## Pace and blocks

These are airline websites with bot protection, used from one personal network address. Each provider
waits its own `pace` between searches; `--pace` overrides it. Count searches before running:
programs × origins × destinations × directions (× cabins for one-cabin-at-a-time programs).

- A table that says a program is blocked, rate-limited or needs sign-in is reporting the site's answer.
  Do not loop, and do not work around it: no CAPTCHA solving, no stealth or proxy tooling, no calling an
  API behind a sign-in wall. Wait, slow down, or tell the user.
- Do not scan a month day by day. Ask the user which dates matter.

This is a personal convenience at human volume, not a scraper.

## Booking

The tool stops at search. Redeeming miles spends the user's balance irreversibly: do it only on their
explicit request for a specific itinerary, on the airline's site, and confirm flights, passengers, miles
and taxes with them before the final submit.

## Adding or repairing a program

One module per program in `providers/`, registered in `providers/__init__.py`. The contract and the shared
itinerary shape are in `providers/_base.py`; `sniff.py URL OUT_DIR` records the JSON traffic of any page in
the same headless Chrome. Protocol notes per program live in `reference/<name>.md`; write one for every
program attempted, including the ones that did not work.
