"""Etihad Guest: etihad.com "Book with Etihad Guest Miles" search, no sign-in needed.

The results page on digital.etihad.com (a deep link, no warm-up visit needed) fetches a guest token and POSTs
the search to api-des.etihad.com `search/air-bounds`. That first answer is capped; when the page offers "Show more
flights" the provider clicks it and takes the uncapped answer instead. One page load answers economy + business,
a second one answers first, so searches are per cabin and the economy/business answer is reused. Protocol notes:
reference/etihad.md.
"""
import time
from urllib.parse import urlencode
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

RESULTS = "https://digital.etihad.com/book/search?"
API = "/search/air-bounds"
# our cabin -> the page's CABIN parameter. The page sends CABIN=E as commercialFareFamilies ECONOMY+BUSINESS
# and CABIN=F as FIRST. Etihad sells no premium economy.
PAGE_CABIN = {"economy": "E", "business": "E", "first": "F"}
CABIN = {"eco": "economy", "business": "business", "first": "first"}
# Error codes air-bounds answers (HTTP 200, no "data") when the market/date/cabin simply has nothing to sell.
EMPTY_CODES = {"7959"}  # NO FLIGHTS FOUND / NO FARE FOUND FOR REQUESTED ITINERARY
SHOWN = 5  # itineraries the page lists before offering "Show more flights"
CAP = "maxFlightCombinationsPerBound"  # present only in the page's first, capped request


class Etihad(Provider):
    name, program, alliance, pace = "etihad", "Etihad Guest", "none", 10
    all_cabins = False

    def start(self):
        self._cache, self._last = {}, 0.0

    def search(self, origin, dest, date, adults=1, cabin=None):
        if cabin is None:  # direct callers: both page loads, merged per itinerary
            merged = {}
            for c in ("economy", "first"):
                for it in self._load(origin, dest, date, adults, PAGE_CABIN[c]):
                    key = tuple((s["flight"], s["dep"]) for s in it["segments"])
                    if key in merged:
                        merged[key]["fares"] += it["fares"]
                    else:
                        merged[key] = {**it, "fares": list(it["fares"])}
            return list(merged.values())
        if cabin not in PAGE_CABIN:
            return []
        out = []
        for it in self._load(origin, dest, date, adults, PAGE_CABIN[cabin]):
            fares = [f for f in it["fares"] if f["cabin"] == cabin]
            if fares:
                out.append({**it, "fares": fares})
        return out

    def _load(self, origin, dest, date, adults, page_cabin):
        key = (origin, dest, date, adults, page_cabin)
        if key not in self._cache:
            wait = self._last + self.pace - time.time()
            if self._last and wait > 0:  # a second page load inside one CLI search
                time.sleep(wait)
            try:
                self._cache[key] = self._fetch(origin, dest, date, adults, page_cabin)
            finally:
                self._last = time.time()
        return self._cache[key]

    def _fetch(self, origin, dest, date, adults, page_cabin):
        url = RESULTS + urlencode({
            "LANGUAGE": "EN", "CHANNEL": "DESKTOP", "B_LOCATION": origin, "E_LOCATION": dest, "TRIP_TYPE": "O",
            "CABIN": page_cabin, "TRAVELERS": ",".join(["ADT"] * adults), "TRIP_FLOW_TYPE": "AVAILABILITY",
            "DATE_1": date.strftime("%Y%m%d") + "0000", "WDS_ENABLE_MILES_TOGGLE": "TRUE", "FLOW": "AWARD"})
        page = self.browser.page
        day = f'"departureDateTime":"{date.isoformat()}T'  # the page also searches the next day on its own

        def wanted(r):
            return API in r.url and r.request.method == "POST" and day in (r.request.post_data or "")

        try:
            with page.expect_response(wanted) as info:
                page.goto(url, wait_until="domcontentloaded")
        except PwTimeout:
            raise ProviderError("digital.etihad.com made no air-bounds call within 60s (blocked, rate-limited, "
                                "or the site changed)")
        doc = self._body(info.value)
        if doc is None:
            return []
        if len(doc["data"].get("airBoundGroups") or []) > SHOWN:
            # The page lists SHOWN itineraries, then "Show more flights" repeats the search without the cap.
            try:
                more = page.get_by_text("Show more flights").first
                more.wait_for(state="visible", timeout=20000)
                with page.expect_response(lambda r: wanted(r) and CAP not in r.request.post_data, timeout=45000) as info:
                    more.click()
            except PwTimeout:
                return parse(doc)  # the capped answer is still what the page shows
            doc = self._body(info.value) or doc
        return parse(doc)

    @staticmethod
    def _body(resp):
        """Parsed air-bounds answer, None for an empty market."""
        status, text = resp.status, resp.text()
        try:
            doc = resp.json()
        except Exception:
            raise ProviderError(f"etihad air-bounds answered {status} without JSON: {text[:200]!r}")
        if status != 200 or "data" not in doc:
            codes = {str(e.get("code")) for e in doc.get("errors") or []}
            if codes and codes <= EMPTY_CODES:
                return None
            raise ProviderError(f"etihad air-bounds answered {status}: {text[:300]}")
        return doc


def parse(doc):
    dic = doc.get("dictionaries") or {}
    flights, families = dic.get("flight") or {}, dic.get("fareFamilyWithServices") or {}
    aircraft, airlines = dic.get("aircraft") or {}, dic.get("airline") or {}

    def label(table, code):
        return " ".join(w.capitalize() if w.isalpha() else w for w in table[code].split()) if table.get(code) else code

    out = []
    for group in (doc.get("data") or {}).get("airBoundGroups") or []:
        bound = group["boundDetails"]
        segs = []
        for ref in bound["segments"]:
            f = flights[ref["flightId"]]
            segs.append({
                "flight": f"{f['marketingAirlineCode']} {f['marketingFlightNumber']}",
                "from": f["departure"]["locationCode"], "to": f["arrival"]["locationCode"],
                "dep": f["departure"]["dateTime"][:16], "arr": f["arrival"]["dateTime"][:16],
                "aircraft": label(aircraft, f.get("aircraftCode")),
                "operated_by": label(airlines, f.get("operatingAirlineCode") or f["marketingAirlineCode"]),
            })
        best = {}
        for ab in group.get("airBounds") or []:
            if (ab.get("status") or {}).get("value") == "soldOut":
                continue
            code = ab["fareFamilyCode"]
            cab = CABIN.get((families.get(code) or {}).get("cabin"))
            prices = ab.get("prices") or {}
            unit = (prices.get("unitPrices") or [{}])[0]  # per traveller
            miles = ((unit.get("milesConversion") or {}).get("convertedMiles") or {}).get("base")
            cash = (unit.get("prices") or [{}])[0]
            if cab is None or miles is None:
                continue
            quotas = [a["quota"] for a in ab.get("availabilityDetails") or [] if a.get("quota") is not None]
            f = fare(cab, miles, cash.get("totalTaxes") or 0, cash.get("currencyCode") or "AED",
                     min(quotas) if quotas else None, ab.get("isMixedCabin"), code)
            if cab not in best or f["miles"] < best[cab]["miles"]:
                best[cab] = f
        if best:
            out.append({"segments": segs, "duration_min": (bound.get("duration") or 0) // 60 or None,
                        "fares": [best[c] for c in CABINS if c in best]})
    return out


PROVIDER = Etihad
