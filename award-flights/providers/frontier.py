"""Frontier Miles: flyfrontier.com miles search, no sign-in needed.

The booking site's search deep link (works cold, no warm-up visit) redirects to the results page, whose
HTML carries every itinerary in an inline script, `FlightData = '<HTML-escaped JSON>'`. There is no
separate JSON response to catch. Protocol notes: reference/frontier.md.
"""
import datetime, html, json, re
from urllib.parse import quote
from playwright.sync_api import Error as PwError
from ._base import Provider, ProviderError, fare

SEARCH = "https://booking.flyfrontier.com/Flight/InternalSelect"
FLIGHT_DATA = re.compile(r"FlightData\s*=\s*'(.*?)';", re.S)
PAGE_ERROR = re.compile(r'_mfq\.push\(\["tag",\s*"error:\s*(.*?)"\]\)')
AIRLINES ={"F9": "Frontier"}
# Frontier has one cabin. The miles price is the "Basic Fare" column; the Economy / Premium / Business
# Bundle columns are the same seat class plus extras for more miles, so Basic is always the cheapest.
BRAND = "Basic Fare"


def utc(stamp):
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


class Frontier(Provider):
    name, program, alliance, pace = "frontier", "Frontier Miles", "none", 10

    def search(self, origin, dest, date, adults=1, cabin=None):
        page = self.browser.page
        # dd1 is "Dec 01, 2026"; month names spelled out here so the process locale cannot change them
        month = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[date.month - 1]
        url = (f"{SEARCH}?o1={quote(origin)}&d1={quote(dest)}&dd1={quote(f'{month} {date.day:02d}, {date.year}')}"
               f"&ADT={adults}&loy=true&promo=&ftype=Miles")
        try:
            resp = page.goto(url, wait_until="domcontentloaded")
            status, text = (resp.status, resp.text()) if resp else (0, "")
        except PwError as e:
            raise ProviderError(f"flyfrontier.com search page did not load: {str(e)[:200]}")
        m = FLIGHT_DATA.search(text)
        if not m:
            shown = " ".join(re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<(script|style).*?</\1>", " ", text)).split())
            raise ProviderError(f"flyfrontier.com answered {status} at {page.url[:100]} without flight data "
                                f"(blocked, rate-limited, or the site changed): {shown[:200]!r}")
        doc = json.loads(html.unescape(m.group(1)))
        if doc.get("fareTypeBy") != "Miles":  # the same page also sells in dollars; never report those as miles
            raise ProviderError(f"flyfrontier.com showed {doc.get('fareTypeBy')!r} prices, not miles")
        out = []
        journeys = doc.get("journeys") or []
        if not any(j.get("flights") for j in journeys):
            # the page reports a failed search as an error banner, echoed to its analytics tag
            err = PAGE_ERROR.search(text)
            if err and "airport code" not in err.group(1):  # "...airport code is invalid": Frontier does not fly there
                raise ProviderError("flyfrontier.com: " + html.unescape(err.group(1))[:300])
            return []
        for journey in journeys:
            if journey.get("departureStation") != origin or journey.get("arrivalStation") != dest \
                    or (journey.get("departureDate") or "")[:10] != date.isoformat():
                raise ProviderError("flyfrontier.com answered for another search: "
                                    f"{journey.get('departureStation')}-{journey.get('arrivalStation')} "
                                    f"{(journey.get('departureDate') or '')[:10]}")
            for f in journey.get("flights") or []:
                legs, miles = f.get("legs") or [], f.get("standardFare")
                if not legs or not miles or not f.get("milesFareKey"):
                    continue  # not sold for miles
                left = re.match(r"\d+", f.get("milesFareFareSeatsRemaining") or "")  # "3 Seats Left!"
                out.append({
                    "segments": [{
                        "flight": f"{s['carrierCode']} {s['flightNumber']}",
                        "from": s["departureStation"], "to": s["arrivalStation"],
                        "dep": s["departureDate"][:16], "arr": s["arrivalDate"][:16],
                        "aircraft": None,  # not published on the results page
                        "operated_by": s.get("carrierText") or AIRLINES.get(s["carrierCode"], s["carrierCode"]),
                    } for s in legs],
                    "duration_min": int((utc(legs[-1]["arrivalDateUtc"]) - utc(legs[0]["departureDateUtc"]))
                                        .total_seconds() // 60),
                    # in a miles search `standardFare` is the miles and `milesFare` the cash taxes (USD)
                    "fares": [fare("economy", miles, f.get("milesFare") or 0, "USD",
                                   int(left.group()) if left else None, False, BRAND)]})
        return out


PROVIDER = Frontier
