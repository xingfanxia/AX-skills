# Aerolíneas Argentinas Plus (aerolineas.com.ar)

State on 2026-10-15: `providers/aerolineas.py` exists but has not completed a live search, so it is not
registered.

- Only the Argentine site (`https://www.aerolineas.com.ar/en-ar`) has the "Miles Search" toggle; `en-us`
  has none. A survey reached results signed out through the home page form (One Way, Miles Search, origin
  and destination autosuggest, date picker, `#search-flights`), landing on
  `/en-ar/flights-offers?adt=1&inf=0&chd=0&flexDates=false&cabinClass=Economy&flightType=ONE_WAY&awardBooking=true&leg=EZE-MIA-20261202`.
- That page fetched `GET https://api.aerolineas.com.ar/v1/flights/offers?<same query>`. Answer:
  `searchMetadata.currency: "MILES"`, `fareFamilies` (YB Millas Base, EX Economy Award Full, EZ Economy Plus
  Award, BA Business Award), `brandedOffers["0"][]` with `legs[0].segments[]` and `offers[]` carrying
  `requiredMinMiles.amount`, `seatAvailability.seats`, `brand`, and a `fare.taxes` number in no unit the
  page displays (508224 next to 35,000 miles). `alternateOffers` gives the lowest miles for ±3 days.
- The page showed four columns: "¡New! MILES+CASH Base" (YB), "Millas Turista" (EX) 35,000, "Millas
  Economy+" (EZ) 45,000 with "2 places left!", "Millas Business" (BA). The API labels the EZ offer
  `cabinClass: "Business"`; the page and brand name say Economy+, so the provider maps it to economy.
  The provider skips YB (miles plus cash) and reports taxes as not quoted.
- Opening the results URL directly answered `403 Forbidden`. An in-page route change from the home page
  was tried next, and by then the home page itself answered 403: the site's firewall had flagged the
  address after roughly ten loads across the survey and these attempts. The working path is the home page
  form; the provider would need to drive it (the survey's click sequence is the starting point) once the
  block lifts.
- Only Aerolíneas' own flights were seen (EZE→MIA); whether SkyTeam partners appear is unknown.
