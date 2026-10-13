---
name: ana-award
description: Search ANA Mileage Club international award flights (miles, taxes, seats per itinerary) from the command line with the user's own logged-in account, instead of ANA's website. Use for ANA / Star Alliance award availability or price questions.
---

# ANA award search

`ana_award.py` (next to this file) drives ANA's international award booking site
(`aswbe-i.ana.co.jp/international_asw`) in a throwaway headless Chrome as the user's own ANA Mileage Club
account and prints the bookable itineraries with miles, cash taxes and seats. It needs macOS, Google
Chrome, and `uv`. No window opens and the user's own Chrome profile is only read, never driven.

```bash
./ana_award.py SZX,HKG TYO 2026-12-01 2026-12-15 --cabin Y,J
./ana_award.py HND SFO 2027-03-02 --cabin J --json     # one-way, full data
```

Origins and cabins are comma-separated and searched one after another; the destination is a single
IATA airport or city code (`TYO`, `OSA`, `SEL` cover all airports of the city). Cabins: `Y`, `PY`,
`J`, `F`. Omit the return date for one-way. The markdown table lists the cheapest `--limit` outbound ×
return combinations; `--json` returns every flight and combination.

## Reading the output

- **Miles** is the total for the whole itinerary per adult; **Tax** is the cash part in JPY.
- **Award** is the chart the itinerary prices on: `ANA` (ANA-operated only, waitlist allowed) or
  `Star Alliance` (any partner segment; no waitlist). An all-ANA itinerary usually appears under both.
- **Seats** is ANA's own counter per direction, capped at 9. `WL` marks a combination with a direction at
  0 seats, read as waitlist-only (ANA awards allow waitlisting; that reading is inferred from the page script).
- "No award space returned … E_A01P01_0007" means the cabin does not exist or has no award inventory on
  that route and date. It is ANA's answer, not a tool failure, and it still counts as a search. Premium Economy only exists on long-haul.
- ANA releases award seats 355 days out; the site accepts dates up to 356 days ahead.

## Login

No credentials go on the command line. The tool copies the member's `ana.co.jp` sign-in cookies from the
user's Chrome profile (one Keychain read of "Chrome Safe Storage"; `ANA_CHROME_PROFILE` selects a profile
other than `Default`), so the user must already be signed in to ana.co.jp in Chrome. ANA's booking app
then asks for the password again for every new session; the tool supplies it from `ANA_PASSWORD`, or from
the 1Password item named by `ANA_OP_ITEM` (default `ANA`, optional `ANA_OP_VAULT`) via `op`. Nothing is
cached: each run signs in once and performs all its searches in that one session.

The password step is attempted exactly once per run. Never wrap the tool in a retry loop: repeated bad
passwords lock the mileage account.

## Rate limit: the constraint that shapes every query

ANA (through Akamai) limits how often one client may search. When the limit trips, nothing is refused:
the result page simply never loads, for about 30 minutes, and for every client on the same network
(plain HTTP and real Chrome alike). Observed triggers: five or six searches in four minutes, and three
searches in four minutes. The tool therefore waits `--pace` seconds (default 150) between searches,
gives up after 60 s of silence with "searches are being rate-limited", and still prints the results it
already collected.

- Count searches before running: origins × cabins. Six searches take about 15 minutes at the default pace.
- After a rate-limit exit, wait at least 30 minutes. An immediate retry fails and may extend the block.
- Do not scan a month day by day. Ask the user which dates matter.
- 150 s is the one pace known to work (six searches in a row after a 30-minute rest). The real threshold
  is unknown; if it trips, raise the pace.

This is a personal convenience for one's own account at human volume, not a scraper.

## Booking

The tool stops at search. Redeeming miles is irreversible spending on the user's account: do it only on
their explicit request for a specific itinerary, and confirm flights, passengers, miles and taxes with
them before the final submit. The remaining steps (select flights → passenger information → payment) are
not implemented; the form protocol they would extend is in [reference.md](reference.md).
