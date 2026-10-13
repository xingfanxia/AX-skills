"""Qantas Frequent Flyer: qantas.com "Rewards" (use points) search, no sign-in needed.

The home-page booking widget is a plain form POST to book.qantas.com (Amadeus). The provider posts the
same fields from a qantas.com page, then catches the results page's own availability JSON, which holds
every cabin's reward price per itinerary, and its amenities JSON (aircraft types).
Protocol notes: reference/qantas.md.
"""
import datetime, time
from ._base import CABINS, Provider, ProviderError, fare

WIDGET = "https://www.qantas.com/en-au/book/flights"
ACTION = "https://book.qantas.com/qf-booking/dyn/air/tripflow.redirect"
BOOKING = "/qf-booking/dyn/air/booking/"
AVAIL, AMENITIES = "flexPricerAvailabilityActionFromLoad", "routeHappyAction"
CABIN = {"E": "economy", "P": "premium", "B": "business", "F": "first"}
STEM = {"ECO": "E", "PRM": "P", "BUS": "B", "FIR": "F"}  # fare family ACE<stem>[JQ], when the bound has no map entry
SUBMIT = """fields => {
  const form = document.createElement('form');
  form.method = 'post'; form.action = fields.__action; delete fields.__action;
  for (const [k, v] of Object.entries(fields)) {
    const i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = v; form.appendChild(i);
  }
  document.body.appendChild(form); form.submit();
}"""


def local(ms):
    """The site's timestamps are airport-local wall time written as a UTC epoch (ms)."""
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")


class Qantas(Provider):
    name, program, alliance, pace = "qantas", "Qantas Frequent Flyer", "oneworld", 15
    cash_brand = r"Classic Plus"  # dynamically priced; Classic Reward is the award seat

    def start(self):
        self._warm()

    def _warm(self):
        self.browser.page.goto(WIDGET, wait_until="domcontentloaded")
        time.sleep(6)  # let the page's bot-protection script report before the form post

    def search(self, origin, dest, date, adults=1, cabin=None):
        page = self.browser.page
        if not page.url.startswith("https://www.qantas.com/"):
            self._warm()  # the widget posts from qantas.com; go back there after a results page
        got = {}

        def on_response(r):
            if BOOKING not in r.url or r.request.method != "POST":
                return
            try:
                got[r.url.split(BOOKING)[1].split("?")[0]] = r.json()
            except Exception:
                pass

        page.on("response", on_response)
        try:
            # the exact fields the widget posts for one-way + "Rewards" (isClassicView is the Rewards switch)
            page.evaluate(SUBMIT, {
                "__action": ACTION, "depAirports": origin, "destAirports": dest,
                "travelDates": date.strftime("%Y%m%d0000"), "numberOfAdults": str(adults),
                "numberOfYoungAdults": "0", "numberOfChildren": "0", "numberOfInfants": "0",
                "travelClass": "ECO", "searchOption": "F", "QFdeviceType": "desktop",
                "PAGE_FROM": "/bookingError/v1/redirect/en-au/book/flights#fsw-form",
                "USER_LANG": "EN", "USER_LOCALE": "EN_AU",
                "int_cam": "au:bookflight:top:newfsw:en:flights", "isClassicView": "TRUE"})
            deadline = time.time() + 75
            while AVAIL not in got and time.time() < deadline:
                page.wait_for_timeout(500)
                if "/bookingError/" in page.url or self._messages(got):
                    page.wait_for_timeout(1500)
                    break
            if AVAIL in got:  # aircraft types arrive in a second call right after; optional
                end = time.time() + 15
                while AMENITIES not in got and time.time() < end:
                    page.wait_for_timeout(500)
        finally:
            page.remove_listener("response", on_response)
        if AVAIL not in got:
            return self._failed(got)
        return self._parse(got[AVAIL]["modelInput"], (got.get(AMENITIES) or {}).get("modelInput") or {})

    @staticmethod
    def _messages(got):
        out = []
        for doc in got.values():
            lm = ((doc or {}).get("modelInput") or {}).get("listMessages") or {}
            out += [str(m.get("text") or m.get("message") or m) for m in lm.get("messages") or []]
        return out

    def _failed(self, got):
        page = self.browser.page
        try:
            text = " ".join(page.inner_text("body").split())
        except Exception:
            text = ""
        low = text.lower()
        if "log in" in low and ("to continue" in low or "to search" in low or "to use points" in low):
            raise ProviderError("qantas.com asks for a Frequent Flyer login before showing reward flights")
        msgs = self._messages(got)
        if msgs:
            raise ProviderError("book.qantas.com: " + " / ".join(msgs)[:300])
        raise ProviderError(f"book.qantas.com returned no availability within 75s (blocked, rate-limited, or the "
                            f"site changed); page {page.url[:100]} says: {text[:200]!r}")

    def _parse(self, model, amen):
        avail = model.get("availability") or {}
        bounds = avail.get("bounds") or []
        if not bounds:
            return []
        bound = bounds[0]
        li = bound.get("listItineraries") or {}
        places = li.get("locations") or {}
        families = (avail.get("listFareFamily") or {}).get("fareFamilies") or {}
        rules = (avail.get("fareFamiliesMinirules") or {}).get("minirules") or {}
        ff_cabin = bound.get("ffCodeToAssociatedCabin") or {}
        currency = (avail.get("currency") or {}).get("code") or "AUD"
        planes = {k: v["displayText"] for k, v in (amen.get("amenityDictionary") or {}).items()
                  if v.get("type") == "aircraft"}
        by_flight = {}  # "SYD-LAX-QF-11-20261201" -> aircraft text (keys end in a cabin; any cabin will do)
        for key, ids in (amen.get("amenityMapping") or {}).items():
            plane = next((planes[i] for i in ids if i in planes), None)
            if plane:
                by_flight.setdefault(key.rsplit("-", 1)[0], plane)
        code = lambda c: (places.get(c) or {}).get("locationCode") or c[:3]  # "SYD1" (terminal-tagged) -> "SYD"
        out = []
        for it in li.get("itineraries") or []:
            recs = ((bound.get("flights") or {}).get(str(it["itemId"])) or {}).get("listRecommendation") or {}
            segs = []
            for s in it["segments"]:
                frm, to, dep = code(s["beginLocationCode"]), code(s["endLocationCode"]), local(s["beginDate"])
                al, num = s["airline"]["code"], s["flightNumber"]
                segs.append({
                    "flight": f"{al} {num}", "from": frm, "to": to, "dep": dep, "arr": local(s["endDate"]),
                    "aircraft": by_flight.get(f"{frm}-{to}-{al}-{num.lstrip('0')}-{dep[:10].replace('-', '')}"),
                    "operated_by": s.get("operatingCarrierNameForDisplay")
                                   or (s.get("operatingCarrier") or {}).get("capitalizedName"),
                })
            best = {}
            for ff, r in recs.items():
                cab = CABIN.get(ff_cabin.get(ff) or STEM.get(ff[3:6]))
                price = r.get("priceForOne") or {}
                miles = price.get("convertedBaseFare")
                if cab is None or not miles:
                    continue
                fam = families.get(ff) or {}
                # the same fare family carries either a Classic Reward (fixed table) or a Classic Plus (dynamic) price
                brand = (fam.get("rewardPlusName") if r.get("isRewardPlus") else fam.get("name")) \
                    or (rules.get(ff) or {}).get("fareFamilyName") or ff
                f = fare(cab, miles, price.get("tax") or 0, (price.get("currency") or {}).get("code") or currency,
                         r.get("nbLastSeatsAvailable"), bool(r.get("mixedCabins")), brand)
                if cab not in best or f["miles"] < best[cab]["miles"]:
                    best[cab] = f
            if best:
                out.append({"segments": segs, "duration_min": int(it["duration"] // 60000) if it.get("duration") else None,
                            "fares": [best[c] for c in CABINS if c in best]})
        return out


PROVIDER = Qantas
