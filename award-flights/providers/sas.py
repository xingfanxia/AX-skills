"""SAS EuroBonus: flysas.com points search, no sign-in needed to see prices (booking needs one).

The results page (a deep link, after a home-page warm-up) GETs its own offers API, which returns every
itinerary with every product. Cloudflare sometimes stops the page before that call; then the search raises.
Protocol notes: reference/sas.md.
"""
import time
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import Provider, ProviderError, fare

API = "/api/offers/flights"
# Error codes of a 200 answer that mean "nothing to sell", not a failure.
# 225050: "Unfortunately, we can't offer any availability for selected cities & bookingType".
NO_FLIGHTS = {"225050"}
# Keys of a flight's `cabins` object (the page's fare columns). "Premium" is SAS premium economy.
CABIN_WORDS = [("FIRST", "first"), ("BUSINESS", "business"), ("PREMIUM", "premium"), ("PLUS", "premium"),
               ("ECONOMY", "economy"), ("GO", "economy")]


def cabin_of(key):
    return next((cab for word, cab in CABIN_WORDS if word in key.upper()), None)


def minutes(hms):
    h, m = hms.split(":")[:2]  # "27:20:00": hours run past 24
    return int(h) * 60 + int(m)


class SAS(Provider):
    name, program, alliance, pace = "sas", "SAS EuroBonus", "SkyTeam", 15
    cash_brand = r"FLEX"  # cash fares converted to points; award seats are the BONUS brands

    def start(self):
        # Without a first visit the results page's Cloudflare check fails and it never calls the API.
        self.browser.page.goto("https://www.flysas.com/en/", wait_until="domcontentloaded")
        time.sleep(12)

    def search(self, origin, dest, date, adults=1, cabin=None):
        url = (f"https://www.flysas.com/en/book/flights?search=OW_{origin}-{dest}-{date:%Y%m%d}"
               f"_a{adults}c0i0y0&view=upsell&bookingFlow=points")
        page = self.browser.page
        resp = None
        for attempt in range(2):  # the page's hidden Cloudflare check passes on some loads and not others
            try:  # not Browser.json_after: error statuses carry the "no flights" answer
                with page.expect_response(lambda r: API in r.url and r.request.method == "GET", timeout=45000) as info:
                    page.goto(url, wait_until="domcontentloaded")
                resp = info.value
                status, text = resp.status, resp.text()
                break
            except PwTimeout:
                self.attempts_failed = attempt + 1
                time.sleep(20)
        if resp is None:
            raise ProviderError("flysas.com made no offers call (two loads, 45s each): Cloudflare challenged the "
                                "page's hidden check frame /v1/airbus-boeing/... and it did not clear, or the "
                                "site changed")
        if text.lstrip().startswith("<"):
            raise ProviderError(f"flysas.com offers API answered {status} with a Cloudflare challenge page (blocked)")
        try:
            doc = resp.json()
        except Exception:
            raise ProviderError(f"flysas.com offers API answered {status} without JSON: {text[:200]!r}")
        if "outboundFlights" not in doc:
            errors = doc.get("errors") or []
            if errors and all(e.get("errorCode") in NO_FLIGHTS for e in errors):
                return []
            raise ProviderError(f"flysas.com offers API answered {status}: {text[:300]}")
        currency = (doc.get("currency") or {}).get("code")
        out = []
        for f in sorted(doc["outboundFlights"].values(), key=lambda f: f.get("ranking", 0)):
            segs = [{
                "flight": f"{s['marketingCarrier']['code']} {s['flightNumber']}",
                "from": s["departureAirport"]["code"], "to": s["arrivalAirport"]["code"],
                "dep": s["departureDateTimeInLocal"][:16], "arr": s["arrivalDateTimeInLocal"][:16],
                "aircraft": (s.get("airCraft") or {}).get("name"),
                "operated_by": (s.get("operatingCarrier") or s["marketingCarrier"])["name"],
            } for s in f["segments"]]
            fares = []
            for key, brands in (f.get("cabins") or {}).items():
                cab = cabin_of(key)
                if cab is None:
                    continue
                for brand in brands.values():
                    for p in (brand.get("products") or {}).values():
                        price, legs = p["price"], p.get("fares") or []
                        miles = price.get("pointsAfterDiscount") or price.get("points")
                        if not miles:
                            continue
                        # Cash due on top of the points is totalTax, the cart's "+ N EUR Taxes & carrier-imposed
                        # fees". totalPrice is the cash-fare equivalent; it equals totalTax only on BONUS awards.
                        cash = price["totalTax"]
                        seats = min((x["avlSeats"] for x in legs if x.get("avlSeats") is not None), default=None)
                        fares.append(fare(cab, miles, cash, price.get("currency") or currency, seats,
                                          len({x.get("cabinClass") for x in legs}) > 1, p.get("productName")))
            if fares:
                out.append({"segments": segs, "duration_min": minutes(f["connectionDuration"]), "fares": fares})
        return out


PROVIDER = SAS
