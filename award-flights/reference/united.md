# United MileagePlus (united.com) — not implemented: miles search requires sign-in

Status as of 2026-10-13: **blocked by a sign-in requirement**. There is no `providers/united.py`.

## What was observed (headless Chrome via `providers/_browser.Browser`, no account)

Deep link tried (one-way, award):
`https://www.united.com/en/us/fsr/choose-flights?f=SFO&t=NRT&d=2026-12-01&tt=1&at=1&sc=7&px=1&taxng=1&newHP=True&clm=7&st=bestmatches&tqp=A`

- Document loads with 200; no CAPTCHA, no Akamai block page. Akamai sensor posts (`sensor_data`) answer 201.
- `GET /api/auth/anonymous-token` answers 200 with `{"data":{"token":{"hash":…,"expiresAt":…}}}` (about 30 minutes of validity).
- The results area stays on "Loading results..." and the page never requests `/api/flight/FetchFlights`.
- Cold load (no warm-up): a "Sign in for the best experience" dialog opens over the results.
- After a home-page warm-up (`https://www.united.com/en/us`, 12 s) and closing that dialog, the page shows
  "Continue shopping? We can show you flight results with money. You must be signed-in to see flight
  results with miles." with the choices "Show flights with money", "Sign In", "Go to homepage".

So the site itself declines to show miles prices to an anonymous visitor. The older behaviour (award
search without sign-in) no longer holds for this deep link.

## Not tried, on purpose

- Posting to `/api/flight/FetchFlights` directly with the anonymous bearer token. The site states that
  miles results need a signed-in user; calling the endpoint around that dialog would be working around
  the gate, so whether the API enforces it server-side is unknown.
- Signing in. The tool's rule for this provider was no account and no credentials.
- "Show flights with money" (cash search) — outside this tool's purpose, so cash search under headless
  Chrome is unverified.

## If this is picked up again

A United provider needs a decision to use a signed-in MileagePlus session (as `ana-award` does for ANA).
With one, start from the deep link above and look for `/api/flight/FetchFlights` (POST, bearer token,
possibly streamed) in `sniff.py` output; none of its request or response shape was observed here.

Evidence: `~/.agents/scratch/data/award-flights/united/s1` (cold load) and `s2` (warm-up; `page.png`
shows the dialog, `net.txt` is the request log). Total cost of the investigation: 3 page loads.
