"""China Eastern Eastern Miles: ceair.com points search, no sign-in needed.

The results page (a deep link, no warm-up visit needed) POSTs the search to the site's `briefInfo`
endpoint and gets every itinerary with one points fare per cabin and its cash taxes. The provider
navigates there and catches that answer. Protocol notes: reference/ceair.md.
"""
import base64, json
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

# /en/usd/ sets the language and the currency the taxes are quoted in
RESULTS = "https://www.ceair.com/en/usd/shopping/oneway/{org}-{dst}/{date}?{query}encoded"
API = "/portal/v3/shopping/briefInfo"
EMPTY = {"231009", "231012", "232009"}  # "No (relevant) flight information found. Please ..."
# cabin level letter (`muCabinLevel`): U is "Premium Business Class", shown in the Business/First column
LEVELS = {"Y": "economy", "W": "premium", "J": "business", "U": "business", "F": "first"}


def is_search(request):
    """The page's main points search: the first-stage call, not its product-specific or mixed-cabin follow-ups."""
    if API not in request.url or request.method != "POST":
        return False
    try:
        body = json.loads(request.post_data or "")
    except ValueError:
        return False
    return body.get("jfType") == "ALL" and "productCode" not in body


def parse(doc):
    """Itineraries from a `briefInfo` answer with resultCode S200."""
    data = doc.get("data") or {}
    labels = {}  # product code -> name the site gives it, e.g. "International Standard Points Redemption"
    for p in data.get("productInfos") or []:
        for label in p.get("cabinLabelInfo") or []:
            if label.get("labelName"):
                labels.setdefault(p["productCode"], label["labelName"])
    out = []
    for item in data.get("flightItems") or []:
        info = item["flightInfos"][0]  # one per direction; a one-way search has one
        segs = [{
            "flight": f"{s['airlineCode']} {s['flightNo']}", "from": s["orgCode"], "to": s["destCode"],
            "dep": f"{s['fltDate']}T{s['orgTime']}", "arr": f"{s['arriDate']}T{s['destTime']}",
            "aircraft": s.get("icaoType") or s.get("planeType"),
            "operated_by": s.get("carrierCodeName") or s.get("carrierCode"),  # carrier* is the operating flight
        } for s in info["flightSegments"]]
        best = {}
        for c in item.get("cabinInfoDescs") or []:
            cab = LEVELS.get(c.get("muCabinLevel") or c.get("ctype"))
            if cab is None:
                continue
            # booking class per segment, e.g. "X" or "X/O"; more than one level's classes would be a mixed cabin,
            # but only single-segment itineraries were ever seen, so nothing is flagged
            for f in c.get("fareInfoDescList") or []:
                if f.get("paxType") != "ADT" or not f.get("lprice"):
                    continue
                one = fare(cab, float(f["lprice"]), float(f.get("taxPrice") or 0), doc.get("taxCurrency") or "USD",
                           None, False, labels.get(f.get("productCode"), f.get("productCode")))
                if cab not in best or one["miles"] < best[cab]["miles"]:
                    best[cab] = one
        if best:
            out.append({"segments": segs, "duration_min": info.get("duration"),
                        "fares": [best[c] for c in CABINS if c in best]})
    return out


class Ceair(Provider):
    name, program, alliance, pace = "ceair", "China Eastern Eastern Miles", "SkyTeam", 20  # see reference: firewall

    def search(self, origin, dest, date, adults=1, cabin=None):
        query = {"payWay": "JF"}  # JF = 积分, points
        if adults != 1:
            query["passengerNum"] = f"{adults},0,0"
        url = RESULTS.format(org=origin, dst=dest, date=date.isoformat(),
                             query=base64.b64encode(json.dumps(query, separators=(",", ":")).encode()).decode())
        page = self.browser.page
        try:
            with page.expect_response(lambda r: is_search(r.request)) as info:
                page.goto(url, wait_until="domcontentloaded")
            resp = info.value
            status, text = resp.status, resp.text()
        except PwTimeout:
            try:
                shown = " ".join(page.inner_text("body").split())[:200]
            except Exception:
                shown = ""
            raise ProviderError("ceair.com made no points search call within 60s (blocked, rate-limited, unknown "
                                f"airport code, or the site changed); page says: {shown!r}")
        asked = json.loads(resp.request.post_data)
        if "" in (asked.get("depCode"), asked.get("arrCode")):
            return []  # the site's airport list does not know the code, so it searched with a blank
        if (asked.get("depCode"), asked.get("arrCode"), asked.get("depDate"), asked.get("adultCount")) != \
                (origin, dest, date.isoformat(), adults):
            raise ProviderError("ceair.com searched something else: " + json.dumps(
                {k: asked.get(k) for k in ("depCode", "arrCode", "depDate", "adultCount")}))
        try:
            doc = json.loads(text)
        except ValueError:  # the site's firewall answers 200 with an HTML "Try again later! Your IP: ..." page
            raise ProviderError(f"ceair.com search answered {status} without JSON (blocked or rate-limited): {text[:120]!r}")
        code = doc.get("resultCode")
        if code in EMPTY:
            return []
        if status != 200 or code != "S200":
            raise ProviderError(f"ceair.com search answered {status} {code}: {doc.get('resultMsg')!r}")
        if doc.get("currencyCode") != "JF":  # the same page also sells in cash; never report those as points
            raise ProviderError(f"ceair.com priced in {doc.get('currencyCode')!r}, not points")
        return parse(doc)


PROVIDER = Ceair
