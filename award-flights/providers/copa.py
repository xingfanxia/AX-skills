"""Copa Airlines ConnectMiles: copaair.com miles search, no sign-in needed.

After a warm-up visit to the home page, the results deep link on shopping.copaair.com makes the page POST
the search to its own booking API; the answer holds every itinerary (Copa and partner flights) with every
fare family. STATUS 2026-10-13: the booking API answered 403 + slider CAPTCHA on every provider run, so
search() has only ever raised ProviderError; parse() is checked against one captured answer.
Protocol notes: reference/copa.md.
"""
import re, time
from urllib.parse import urlencode
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

HOME = "https://www.copaair.com/en-us/"
RESULTS = "https://shopping.copaair.com/miles?"
API = "/ibe/booking/plan-redemptions"
# fare family code -> cabin. Copa sells two cabins; "Dreams" is its lie-flat business seat, not a third cabin.
FAMILIES = {"ESV": "economy", "ESD": "economy", "BSV": "business", "BSD": "business"}
CAPTCHA = "blocked: copaair.com answered with its 'Verification required' slider CAPTCHA (DataDome)"


def _minutes(iso):  # "PT03H06M"
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso or "")
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) if m else None


def parse(doc):
    """plan-redemptions answer (a list with one block per direction) -> itineraries."""
    out = []
    for od in doc[:1]:  # one-way: a single origin-destination block
        currency = (od.get("currency") or {}).get("code") or "USD"
        for sol in od.get("solutions") or []:
            segs = []
            for f in sol["flights"]:
                mk, op, dep, arr = f["marketingCarrier"], f.get("operatingCarrier") or {}, f["departure"], f["arrival"]
                segs.append({
                    "flight": f"{mk['airlineCode']} {mk['flightNumber']}",
                    "from": dep["airportCode"], "to": arr["airportCode"],
                    "dep": f"{dep['flightDate']}T{dep['flightTime']}", "arr": f"{arr['flightDate']}T{arr['flightTime']}",
                    "aircraft": f.get("aircraftName"),
                    "operated_by": op.get("airlineName") or mk.get("airlineName") or mk["airlineCode"],
                })
            best = {}
            for o in sol.get("offers") or []:
                fam = o.get("fareFamily") or {}
                cab = FAMILIES.get(fam.get("code")) or next(
                    (c for c in ("economy", "business") if (fam.get("name") or "").lower().startswith(c)), None)
                price = o.get("pricePerAdult") or {}
                if cab is None or not price.get("miles"):
                    continue
                fr = fare(cab, price["miles"], price.get("taxes") or 0, currency, None, False, fam.get("name"))
                if cab not in best or fr["miles"] < best[cab]["miles"]:
                    best[cab] = fr
            if best:
                out.append({"segments": segs, "duration_min": _minutes(sol.get("journeyTime")),
                            "fares": [best[c] for c in CABINS if c in best]})
    return out


class Copa(Provider):
    name, program, alliance, pace = "copa", "Copa ConnectMiles", "Star Alliance", 15

    def start(self):
        page = self.browser.page
        page.goto(HOME, wait_until="domcontentloaded")
        self._check_captcha()
        time.sleep(10)  # let the bot-protection script on the home page finish before the first search

    def _check_captcha(self):
        page = self.browser.page
        if page.locator("iframe[src*='captcha-delivery']").count() or "Verification required" in page.title():
            raise ProviderError(CAPTCHA)
        try:
            if "Verification required" in page.inner_text("body", timeout=5000)[:2000]:
                raise ProviderError(CAPTCHA)
        except PwTimeout:
            pass

    def search(self, origin, dest, date, adults=1, cabin=None):
        url = RESULTS + urlencode({
            "roundtrip": "false", "adults": adults, "children": 0, "infants": 0, "date1": date.isoformat(),
            "date2": "null", "promocode": "null", "area1": origin, "area2": dest,
            "advanced_air_search": "false", "flexible_dates_v2": "false", "airline_preference": "CM"})
        page = self.browser.page
        try:
            # a 403 on any booking call (the first is GET get-id) is the bot wall, shown as a slider CAPTCHA
            with page.expect_response(lambda r: (API in r.url and r.request.method == "POST")
                                      or ("/ibe/booking/" in r.url and r.status == 403), timeout=45000) as info:
                page.goto(url, wait_until="domcontentloaded")
            resp = info.value
            status, text = resp.status, resp.text()
        except PwTimeout:
            self._check_captcha()
            raise ProviderError("copaair.com made no plan-redemptions call within 45s (blocked, rate-limited, "
                                "or the site changed)")
        if status == 403:
            raise ProviderError(CAPTCHA + f": {text[:120]}")
        try:
            doc = resp.json()
        except Exception:
            raise ProviderError(f"copaair.com search answered {status} without JSON: {text[:200]!r}")
        if status != 200 or not isinstance(doc, list):
            raise ProviderError(f"copaair.com search answered {status}: {text[:200]}")
        return parse(doc)

PROVIDER = Copa
