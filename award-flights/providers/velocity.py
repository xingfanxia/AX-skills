"""Virgin Australia Velocity Frequent Flyer: virginaustralia.com points search, no sign-in needed.

The results page (a deep link into the booking app, no warm-up visit needed) POSTs the search to the
site's GraphQL endpoint and gets every itinerary with every fare brand of every cabin. The provider
navigates there and catches that answer, plus the app's translation file for aircraft and airline names.
Protocol notes: reference/velocity.md.
"""
import time
from urllib.parse import urlencode
from ._base import CABINS, Provider, ProviderError, fare

API, OPERATION = "/api/graphql", "bookingAirSearch"
NAMES = "/data/translations/en-GB.json"  # aircrafts{} and airlines{} by IATA code
CLASSES = {"economy": "economy", "premiumeconomy": "premium", "premium": "premium", "business": "business",
           "first": "first"}
POINTS = "FFCURRENCY"
ANY_SEAT = " (any seat)"  # brand suffix of a cash fare converted to points; Reward Seats carry no suffix


def amount(price, kind):
    """`price` is {"alternatives": [[{amount, currency}, ...], ...]}: each alternative is one way to pay.
    kind "points": the amount of the all-points alternative; kind "cash": (amount, currency) of the all-cash one."""
    for alt in (price or {}).get("alternatives") or []:
        if len(alt) != 1:
            continue
        if kind == "points" and alt[0]["currency"] == POINTS:
            return alt[0]["amount"]
        if kind == "cash" and alt[0]["currency"] != POINTS:
            return alt[0]["amount"], alt[0]["currency"]
    return None


class Velocity(Provider):
    name, program, alliance, pace = "velocity", "Virgin Australia Velocity", "none", 12
    cash_brand = r"\(any seat\)"  # cash fares converted to points; Reward Seats carry no suffix
    # Sabre's "DX" booking app; other airlines on it differ only in host and site code (see ethiopian.py)
    results = "https://book.virginaustralia.com/dx/VADX/#/flight-selection?"

    def start(self):
        self._names = {}

    def _host(self):
        return self.results.split("/")[2]

    def search(self, origin, dest, date, adults=1, cabin=None):
        page = self.browser.page
        mdy = date.strftime("%m-%d-%Y")
        url = self.results + urlencode({
            "journeyType": "one-way", "activeMonth": mdy, "awardBooking": "true", "class": "Economy",
            "ADT": adults, "origin": origin, "destination": dest, "date": mdy, "promoCode": "", "direction": 0})
        got = {}

        def on_response(r):
            try:
                if NAMES in r.url and not self._names:
                    self._names = r.json()
                elif ("status" not in got and API in r.url and r.request.method == "POST"
                      and OPERATION in (r.request.post_data or "")):
                    # first one only: on an empty date the page goes on to search the calendar around it
                    got["status"], got["text"] = r.status, r.text()
                    got["doc"] = r.json()
            except Exception:
                pass

        page.on("response", on_response)
        try:
            # the search lives in the URL fragment: leave the app first, or a second search would not reload it
            page.goto("about:blank")
            page.goto(url, wait_until="domcontentloaded")
            deadline = time.time() + 60
            while "status" not in got and time.time() < deadline:
                page.wait_for_timeout(500)
            end = time.time() + 5
            while "status" in got and not self._names and time.time() < end:  # names are optional
                page.wait_for_timeout(250)
        finally:
            page.remove_listener("response", on_response)
        if "status" not in got:
            try:
                shown = " ".join(page.inner_text("body").split())[:200]
            except Exception:
                shown = ""
            raise ProviderError(f"{self._host()} made no flight search call within 60s (blocked, rate-limited, "
                                f"or the site changed); page says: {shown!r}")
        doc = got.get("doc")
        if not isinstance(doc, dict):
            raise ProviderError(f"{self._host()} search answered {got['status']} without JSON: {got['text'][:200]!r}")
        res = ((doc.get("data") or {}).get(OPERATION) or {}).get("originalResponse")
        if got["status"] != 200 or not isinstance(res, dict):
            raise ProviderError(f"{self._host()} search answered {got['status']}: {got['text'][:300]}")
        return self._parse(res)

    def _parse(self, res):
        ids = {}  # the answer is written with object references: {"@id": "7", ...} once, then {"@ref": "7"}

        def index(o):
            if isinstance(o, dict):
                if "@id" in o:
                    ids[o["@id"]] = o
                for v in o.values():
                    index(v)
            elif isinstance(o, list):
                for v in o:
                    index(v)

        index(res)
        deref = lambda o: ids[o["@ref"]] if isinstance(o, dict) and "@ref" in o else o
        planes, airlines = self._names.get("aircrafts") or {}, self._names.get("airlines") or {}
        labels = {}  # (brand id, fare program id) -> name; one brand can be named differently per program
        for f in res.get("fareFamilies") or []:
            for b in f.get("brandLabel") or []:
                if b.get("marketingText") and (b.get("languageId") or "en").startswith("en"):
                    labels[f["brandId"], b.get("programId")] = labels[f["brandId"], None] = b["marketingText"]
        out = []
        for group in (res.get("brandedResults") or {}).get("itineraryPartBrands") or []:
            for item in group:
                part = deref(item["itineraryPart"])
                segs = []
                for s in map(deref, part["segments"]):
                    fl = s["flight"]
                    op = fl.get("operatingAirlineCode") or fl["airlineCode"]
                    segs.append({
                        "flight": f"{fl['airlineCode']} {fl['flightNumber']}", "from": s["origin"], "to": s["destination"],
                        "dep": s["departure"][:16], "arr": s["arrival"][:16],
                        "aircraft": planes.get(s.get("equipment"), s.get("equipment")),
                        "operated_by": airlines.get(op, op),
                    })
                programs = [None] + (part.get("programIDs") or [])
                best = {}  # (cabin, is reward seat) -> cheapest fare
                for o in item.get("brandOffers") or []:
                    cab = CLASSES.get((o.get("cabinClass") or "").lower().replace(" ", "").replace("_", ""))
                    miles, cash = amount(o.get("fare"), "points"), amount(o.get("taxes"), "cash")
                    if o.get("soldout") or cab is None or not miles:
                        continue
                    # a Reward Seat has a points-only fare; any other brand is a cash fare also quoted in points
                    reward = amount(o.get("fare"), "cash") is None
                    label = next((labels[o["brandId"], p] for p in reversed(programs) if (o["brandId"], p) in labels),
                                 o["brandId"])
                    f = fare(cab, miles, cash[0] if cash else 0, cash[1] if cash else res.get("currency") or "AUD",
                             (o.get("seatsRemaining") or {}).get("count"), False,  # no per-segment cabin published
                             label + ("" if reward else ANY_SEAT))
                    if (cab, reward) not in best or f["miles"] < best[cab, reward]["miles"]:
                        best[cab, reward] = f
                if best:
                    out.append({"segments": segs, "duration_min": item.get("duration") or part.get("totalDuration"),
                                "fares": [best[c, r] for c in CABINS for r in (True, False) if (c, r) in best]})
        return out


PROVIDER = Velocity
