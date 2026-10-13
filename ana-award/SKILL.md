---
name: ana-award
description: Search ANA Mileage Club international award flights (miles, taxes, seats per itinerary) from the command line with the user's own logged-in account, instead of ANA's website. Use for ANA / Star Alliance award availability or price questions.
---

# ANA award search

`ana_award.py` (next to this file) queries ANA's international award booking site
(`aswbe-i.ana.co.jp/international_asw`) over plain HTTP as the user's own ANA Mileage Club account and
prints the bookable itineraries with miles, cash taxes and seats. It needs macOS, Chrome, and `uv`.

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
- **Seats** is ANA's own counter per direction, capped at 9. `WL` marks a waitlist-only combination.
- "No award space returned … E_A01P01_0007" means the cabin does not exist or has no award inventory on
  that route and date. It is ANA's answer, not a tool failure. Premium Economy only exists on long-haul.
- ANA releases award seats 355 days out; the site accepts dates up to 356 days ahead.

## Login

No credentials go on the command line. The tool reads `ana.co.jp` cookies from the user's Chrome profile
(one Keychain read of "Chrome Safe Storage"; `ANA_CHROME_PROFILE` selects a profile other than `Default`),
so the user must already be signed in to ana.co.jp in Chrome. ANA's booking app then asks for the
password again for every new session; the tool supplies it from `ANA_PASSWORD`, or from the 1Password
item named by `ANA_OP_ITEM` (default `ANA`, optional `ANA_OP_VAULT`) via `op`. The working session is
cached in `~/.cache/ana-award/session.json` (0600). ANA's backend session dies after about 10 idle
minutes, so re-login on each run is normal. `--fresh` re-reads Chrome's cookies; use it after "not
logged in" or a throttle.

The password step is attempted exactly once per run. Never wrap the tool in a retry loop: repeated bad
passwords lock the mileage account.

## Akamai throttling

The site sits behind Akamai Bot Manager. Chrome's TLS fingerprint (`curl_cffi`) plus Chrome's cookies get
through, but a burst of searches (observed: roughly ten logins and searches within 15 minutes) makes Akamai
tarpit the search POST: it hangs with no response. The tool then exits with "Akamai is throttling". Stop,
wait at least 30 minutes, and keep the default `--pace` between searches. Plan queries so a session stays
within a handful of searches; do not scan a month day by day. This is a personal convenience for one's
own account at human volume, not a scraper.

## Booking

The tool stops at search. Redeeming miles is irreversible spending on the user's account: do it only on
their explicit request for a specific itinerary, and confirm flights, passengers, miles and taxes with
them before the final submit. The remaining steps (select flights → passenger information → payment) are
not implemented; the form protocol they would extend is in [reference.md](reference.md).
