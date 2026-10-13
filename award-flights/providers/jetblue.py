"""JetBlue TrueBlue: jetblue.com points search, no sign-in needed.

The results page (a deep link, no warm-up visit needed) POSTs the search to its own flight-search API
and gets every itinerary with every fare brand. Protocol notes: reference/jetblue.md.
"""
from urllib.parse import urlencode
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

API = "/api/ecom/cb-flight-search/v1/search/NGB"
# JetBlue brand id -> (cabin, name the site shows). EvenMore is extra-legroom economy, sold as its own column.
BRANDS = {
    "DN": ("economy", "Main Base"), "AN": ("economy", "Main"), "GR": ("economy", "Main Flex"),
    "DE": ("economy", "EvenMore Base"), "EN": ("economy", "EvenMore"), "ER": ("economy", "EvenMore Flex"),  # extra-legroom economy, like Delta Comfort
    "DZ": ("first", "BlueFirst Base"), "ZN": ("first", "BlueFirst"), "ZR": ("first", "BlueFirst Flex"),
    "DM": ("business", "Mint Base"), "MN": ("business", "Mint"), "MR": ("business", "Mint Flex"),
}
# Fallback for brands not listed above (partner-airline fares), keyed by the offer's own cabinClass.
CLASSES = {"economy": "economy", "premiumeconomy": "premium", "business": "business", "first": "first"}
AIRCRAFT = {"223": "Airbus A220-300", "32Q": "Airbus A321neo", "32S": "Airbus A320/A321"}
AIRLINES = {"B6": "JetBlue"}


class JetBlue(Provider):
    name, program, alliance, pace = "jetblue", "JetBlue TrueBlue", "none", 10

    def search(self, origin, dest, date, adults=1, cabin=None):
        url = "https://www.jetblue.com/booking/flights?" + urlencode({
            "from": origin, "to": dest, "depart": date.isoformat(), "isMultiCity": "false", "noOfRoute": 1,
            "adults": adults, "children": 0, "infants": 0, "sharedMarket": "false",
            "roundTripFaresFlag": "false", "usePoints": "true"})
        page = self.browser.page
        try:  # not Browser.json_after: this API answers 201, and its error bodies are worth reading
            with page.expect_response(lambda r: API in r.url and r.request.method == "POST") as info:
                page.goto(url, wait_until="domcontentloaded")
            resp = info.value
            status, text = resp.status, resp.text()
        except PwTimeout:
            raise ProviderError("jetblue.com made no flight-search call within 60s (blocked, rate-limited, "
                                "or the site changed)")
        try:
            doc = resp.json()
        except Exception:
            raise ProviderError(f"jetblue.com search answered {status} without JSON: {text[:200]!r}")
        if status not in (200, 201) or "data" not in doc:
            raise ProviderError(f"jetblue.com search answered {status}: {text[:200]}")
        out = []
        for result in doc["data"].get("searchResults") or []:
            for po in result.get("productOffers") or []:
                od = po["originAndDestination"][0]
                segs = []
                for s in od["flightSegments"]:
                    fi = s["flightInfo"]
                    segs.append({
                        "flight": f"{fi['marketingAirlineCode']} {fi['marketingFlightNumber']}",
                        "from": s["departure"]["airport"], "to": s["arrival"]["airport"],
                        "dep": s["departure"]["date"][:16], "arr": s["arrival"]["date"][:16],
                        "aircraft": AIRCRAFT.get(s.get("aircraft"), s.get("aircraft")),
                        "operated_by": AIRLINES.get(fi["operatingAirlineCode"], fi["operatingAirlineCode"]),
                    })
                best = {}
                for o in po.get("offers") or []:
                    if o.get("soldOut"):
                        continue
                    bid = o["brand"]["brandId"]
                    flown = [CLASSES.get(i["cabinClass"].lower()) for i in o["offerSegmentInfo"]]
                    known = BRANDS.get(bid)
                    cab = known[0] if known else CLASSES.get(o["cabinClass"].lower())
                    if cab is None:
                        continue
                    miles = next((p["amount"] for p in o["price"] if p["currency"] == "FFCURRENCY"), None)
                    cash = next((p for p in o["price"] if p["currency"] != "FFCURRENCY"), None)
                    if miles is None:
                        continue
                    f = fare(cab, miles, cash["amount"] if cash else 0, cash["currency"] if cash else "USD",
                             (o.get("seatsRemaining") or {}).get("count"), len(set(flown)) > 1,
                             known[1] if known else bid)
                    if cab not in best or f["miles"] < best[cab]["miles"]:
                        best[cab] = f
                if best:
                    out.append({"segments": segs, "duration_min": od.get("totalDuration"),
                                "fares": [best[c] for c in CABINS if c in best]})
        return out


PROVIDER = JetBlue
