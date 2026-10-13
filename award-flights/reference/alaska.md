# Alaska Atmos Rewards (alaskaair.com)

Verified 2026-10-13. No sign-in needed.

- Results page: `https://www.alaskaair.com/search/results?A=<adults>&O=<org>&D=<dst>&OD=<YYYY-MM-DD>&OT=Anytime&RT=false&ShoppingMethod=onlineaward&locale=en-us`.
- It is a SvelteKit page, so the same query string on `/search/results/__data.json` returns the page's data
  as `text/sveltekit-data`: newline-separated JSON documents, the first with `nodes[]`, the rest
  `{"type":"chunk","data":[…]}` for values the page streams in. Every `data` array is a devalue-flattened
  graph (containers hold indexes into the array). The chunk that decodes to an object with `rows` is the
  flight result.
- `rows[]`: `segments[]` (`displayCarrier`, stations, ISO times with offset, `aircraft`,
  `operationalDisclosure`), `duration` in minutes, and `solutions{<fare brand>: {atmosPoints, grandTotal,
  seatsRemaining, cabins[], mixedCabin}}`. `cabins` values seen: `COACH`, `PREMIUM-COACH`, `BUSINESS`;
  `FIRST` is assumed. Brands seen: `REFUNDABLE_MAIN`, `REFUNDABLE_PARTNER_PREMIUM`, `REFUNDABLE_BUSINESS`.
- Bot protection is AWS WAF. A cold request for the results URL got an image CAPTCHA. Loading the home page
  first (its title stays "Client Challenge" in headless Chrome, yet the token cookie is set) and then
  fetching `__data.json` from inside that page worked every time. The provider waits 8 s on the home page.
- Not verified: more than one adult, saver (non-refundable) award brands, first class, the safe request rate
  (four searches about 10 s apart were fine).
