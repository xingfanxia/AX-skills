# Delta SkyMiles (delta.com)

Verified 2026-10-13. No sign-in needed.

- The "Shop with Miles" results page posts one GraphQL query, `gqlSearchOffers`, to
  `https://offer-api-prd.delta.com/prd/rm-offer-gql`. The query text is kept verbatim in
  `providers/delta_offers.graphql`; re-capture it with `sniff.py` if Delta changes the schema.
- Guest headers the page sends: `authorization: GUEST`, `applicationid: DC`, `channelid: DCOM`,
  `airline: DL`, `x-app-type: dcom-shop`, `x-app-route: search`, `transactionid: <uuid>_<epoch ms>`.
  The provider replays the call with `fetch` from inside a delta.com page (after `book-a-flight` has
  loaded and run Akamai's script), which is cross-origin but allowed.
- Variables: `offersCriteria.pricingCriteria.priceableIn = ["MILES"]`, one `searchOriginDestination`
  with `departureLocalTs`, `resultsPageNum: 1`. The provider asks for 50 results per request; pagination
  beyond that is not implemented.
- The deep link `…/flightsearch/search?action=findFlights&awardTravel=true&…` fires a ±3-day calendar
  variant (`calenderDateRequest`, `resultsPageNum: 4`) that answered `ROF4002` / ITA 404 for both markets
  tried, then drops back to the prefilled form. Clicking Find Flights there sends the exact-date query used here.
- Response: `gqlOffersSets[]`, each with `trips[0].flightSegment[]` and `offers[]`. Miles, cash and seats
  are under `offerItems[0].retailItems[0].retailItemMetaData.fareInformation[0]` (`farePrice[0].totalFarePrice`,
  `availableSeatCnt`); `brandByFlightLegs[].brandId` gives the brand per leg.
- Brands seen: `BMAIN` Main Basic, `CMAIN` Main Classic, `CDCP` Comfort (mapped to economy), `CDPS`
  Premium Select, `CD1` Delta One, `CFIRST` domestic First on a connecting leg. Partner-operated brands
  were not observed; `cabin_of` guesses them by stem.
- A market Delta does not sell (SEA→NRT) answers `ROF4002` with a 404 in `moreInfo`; the provider
  returns no itineraries for that.
- Taxes come in the departure country's currency (USD from SEA, JPY from HND).
- Checked on SEA→JFK with one and two adults: miles and taxes come back per passenger (identical in both
  runs), and domestic First (`CFIRST`) maps to `first`.
