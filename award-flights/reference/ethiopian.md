# Ethiopian ShebaMiles (dxbooking.ethiopianairlines.com)

Verified 2026-10-13. No sign-in needed.

- Ethiopian's award booking runs on the same Sabre "DX" app as Virgin Australia: results deep link
  `https://dxbooking.ethiopianairlines.com/dx/ETDX/#/flight-selection?…&awardBooking=true…` and the same
  `POST /api/graphql` `bookingAirSearch` answer. `providers/ethiopian.py` is the Velocity provider with this
  host, so repairs to the parser belong in `providers/velocity.py` (see `velocity.md`).
- The site's own entry is `https://shebamiles.ethiopianairlines.com/miles/spend-miles` with "Book with
  miles" ticked. The deep link written by the provider (no `execution` parameter, `class=Economy`) worked cold.
- Checked: ADD→IAD 2026-12-01 returned ET 500 at 36,000 miles and ADD→FRA 2026-12-03 returned ET 706 at
  19,000 miles, both equal to the page ("36,000 Miles", "19,000 Miles"). Brand seen: `ECONOMY AWARD`.
- The search answer carries 0 ETB in taxes. The results page shows miles only and warns that taxes and
  surcharges are calculated later, so the provider reports `tax: None` ("taxes (not quoted)" in the table).
- ADD→LHR 2026-12-01 returned no itineraries while the page was still loading; whether that was an empty
  date or a slow answer was not established.
- Not seen: business awards, partner (Star Alliance) flights, connections. The site ran a bot-protection
  interrogation that the page passed on all four loads; `pace = 15` is a guess.
