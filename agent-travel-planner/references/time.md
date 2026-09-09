# Time without invented precision

The schema offers three explicit representations:

- `unknown`: a reason, without fabricated calendar fields.
- `date`: a local YYYY-MM-DD plus named IANA time_zone; no implied midnight.
- `exact`: local YYYY-MM-DDTHH:MM, named IANA time_zone and UTC instant
  YYYY-MM-DDTHH:MM:SSZ. The instant must round-trip to the stated local minute.

Each endpoint has its own zone. Compare exact endpoints as UTC instants to
calculate duration; display both local dates and zones. An arrival's local date
can be earlier than departure when crossing the date line, despite a positive
duration. For date-only endpoints in different zones, do not claim a precise
duration or chronological contradiction from calendar labels alone.

An approximate season/month belongs in trip.window; keep start_date/end_date
null until the actual days are known. A known local day with an unknown hour is
`date`, not `exact` at 00:00. Unknown duration is not zero.

Derive an instant only after the zone and offset are supported by evidence.
During a daylight-saving overlap, the local clock occurs twice: use the
supplier's offset/instant or clarify; do not pick a fold silently. A clock time
inside a daylight-saving gap does not exist. The validator rejects an exact
instant that does not map back correctly, including nonexistent local times.
It cannot prove that the chosen one of two valid overlap instants is evidenced.

Python's zoneinfo reads the machine's IANA database. If a zone is unavailable,
report the missing prerequisite; install/configure a current zone database
through the environment's normal process before relying on exact conversion.
