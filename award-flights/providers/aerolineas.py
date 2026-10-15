"""Aerolíneas Argentinas Plus: miles search on aerolineas.com.ar, no sign-in needed.

Only the Argentine site (`/en-ar`) offers the "Miles Search" toggle. Its results page fetches
`GET api.aerolineas.com.ar/v1/flights/offers?…&awardBooking=true`; the provider opens that page and
catches the answer. Protocol notes: reference/aerolineas.md.
"""
import time
from urllib.parse import urlencode
from ._base import Provider, ProviderError, fare

HOME = "https://www.aerolineas.com.ar/en-ar"
RESULTS = "https://www.aerolineas.com.ar/en-ar/flights-offers?"
API = "api.aerolineas.com.ar/v1/flights/offers"
# fare families: YB Millas Base (miles + cash), EX Millas Turista, EZ Millas Economy+ (extra-legroom
# economy, although the API labels its offers cabinClass "Business"), BA Millas Business
CABIN_BY_BRAND = {"YB": "economy", "EX": "economy", "EZ": "economy", "BA": "business"}


class Aerolineas(Provider):
    name, program, alliance, pace = "aerolineas", "Aerolíneas Argentinas Plus", "SkyTeam", 15

    def start(self):
        self.browser.page.goto(HOME, wait_until="domcontentloaded")
        self.browser.page.wait_for_timeout(6000)

    def search(self, origin, dest, date, adults=1, cabin=None):
        url = RESULTS + urlencode({
            "adt": adults, "inf": 0, "chd": 0, "flexDates": "false", "cabinClass": "Economy",
            "flightType": "ONE_WAY", "awardBooking": "true", "leg": f"{origin}-{dest}-{date:%Y%m%d}"})
        page = self.browser.page
        try:
            with page.expect_response(lambda r: API in r.url and "awardBooking=true" in r.url, timeout=60000) as info:
                page.goto(url, wait_until="domcontentloaded")
            resp = info.value
        except Exception:
            raise ProviderError("aerolineas.com.ar made no miles search call within 60s (blocked or the site changed)")
        try:
            doc = resp.json()
        except Exception:
            raise ProviderError(f"aerolineas.com.ar search answered {resp.status} without JSON")
        if resp.status >= 400 or not isinstance(doc, dict):
            raise ProviderError(f"aerolineas.com.ar search answered {resp.status}: {str(doc)[:200]}")
        if (doc.get("searchMetadata") or {}).get("currency") != "MILES":
            raise ProviderError("aerolineas.com.ar answered a cash search instead of a miles search")
        out = []
        for offer in (doc.get("brandedOffers") or {}).get("0") or []:
            leg = (offer.get("legs") or [{}])[0]
            segs = [{
                "flight": f"{s['airline']} {s['flightNumber']}", "from": s["origin"], "to": s["destination"],
                "dep": s["departure"][:16], "arr": s["arrival"][:16], "aircraft": s.get("equipment"),
                "operated_by": s.get("operatingAirline") or s["airline"],
            } for s in leg.get("segments") or []]
            fares = []
            for o in offer.get("offers") or []:
                brand = o.get("brand") or {}
                miles = (o.get("requiredMinMiles") or {}).get("amount") or (o.get("fare") or {}).get("baseFare")
                if not miles or brand.get("id") == "YB":  # YB is miles plus a cash part, not an all-miles fare
                    continue
                cab = CABIN_BY_BRAND.get(brand.get("id"), "economy")
                # `fare.taxes` is not in a unit the page shows anywhere; the page quotes miles only
                fares.append(fare(cab, miles, None, "ARS", (o.get("seatAvailability") or {}).get("seats"),
                                  False, brand.get("name")))
            out.append({"segments": segs, "fares": fares, "duration_min": leg.get("totalDuration")})
        return out


PROVIDER = Aerolineas
