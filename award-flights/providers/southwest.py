"""Southwest Rapid Rewards: southwest.com points search, no sign-in needed.

The booking form is opened prefilled from URL parameters and its "Search flights" button is clicked;
the page then POSTs the search to its own shopping API, whose answer holds every itinerary with all
four fare products. Opening the results deep link directly is rejected (HTTP 400) by the site's bot
protection, so the click is required. Protocol notes: reference/southwest.md.
"""
import json, time
from urllib.parse import urlencode
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import Provider, ProviderError, fare

HOME = "https://www.southwest.com/"
FORM = "https://www.southwest.com/air/booking/?"
API = "/api/air-booking/v1/air-booking/page/air/booking/shopping"
# Fare family -> name of the column the site shows it in. Southwest has one cabin: all are economy.
BRANDS = {"WGARED": "Basic", "PLURED": "Choice", "ANYRED": "Choice Preferred", "BUSRED": "Choice Extra"}
AIRLINES = {"WN": "Southwest"}
# shopping form-error codes that mean "nothing to sell on this pair and date", not a failure
EMPTY_CODES = {"ERROR__NO_FLIGHTS_AVAILABLE"}


class Southwest(Provider):
    name, program, alliance, pace = "southwest", "Southwest Rapid Rewards", "none", 12

    def start(self):
        self.browser.page.goto(HOME, wait_until="domcontentloaded")
        time.sleep(10)  # let the bot-protection script settle before the first search

    def _shop(self, origin, dest, date, adults=1):
        """Run one search through the form; returns (HTTP status, body text) of the shopping call,
        or (0, the form's own complaint) when the form did not submit."""
        page = self.browser.page
        page.goto(FORM + urlencode({
            "adultsCount": adults, "departureDate": date.isoformat(), "departureTimeOfDay": "ALL_DAY",
            "destinationAirportCode": dest, "fareType": "POINTS", "originationAirportCode": origin,
            "passengerType": "ADULT", "returnDate": "", "tripType": "oneway"}), wait_until="domcontentloaded")
        button = page.get_by_role("button", name="Search flights").first
        try:
            button.wait_for(state="visible", timeout=30000)
        except PwTimeout:
            raise ProviderError("southwest.com booking form did not load (blocked or the site changed)")
        time.sleep(8)  # a search fired right after load is the one the site answers with 400
        try:
            with page.expect_response(lambda r: API in r.url and r.request.method == "POST", timeout=30000) as info:
                button.click()
            resp = info.value
            return resp.status, resp.text()
        except PwTimeout:  # the form refused to submit; its message is the only answer there is
            shown = " ".join(page.inner_text("body").split())
            at = shown.find("Enter a valid")
            return 0, shown[at:at + 40] if at >= 0 else ""

    def search(self, origin, dest, date, adults=1, cabin=None):
        status, text = self._shop(origin, dest, date, adults)
        if status == 0:
            if "airport" in text:  # "Enter a valid arrival airport.": Southwest does not fly there
                return []
            raise ProviderError("southwest.com made no shopping call after the form was submitted "
                                "(blocked or the site changed)")
        try:
            doc = json.loads(text)
        except ValueError:
            raise ProviderError(f"southwest.com shopping answered {status} without JSON: {text[:200]!r}")
        if status != 200 or not doc.get("success"):
            errors = (doc.get("notifications") or {}).get("formErrors") or []
            if errors and all(e.get("code") in EMPTY_CODES for e in errors):
                return []
            raise ProviderError(f"southwest.com shopping answered {status}: {text[:300]}")
        out = []
        for product in doc["data"]["searchResults"].get("airProducts") or []:
            for d in product.get("details") or []:
                best = None
                for family, p in ((d.get("fareProducts") or {}).get("ADULT") or {}).items():
                    f = p.get("fare") or {}
                    total = f.get("totalFare") or {}
                    if p.get("availabilityStatus") != "AVAILABLE" or total.get("currencyCode") != "POINTS":
                        continue
                    tax = f.get("totalTaxesAndFees") or {}
                    seats = f.get("seatsLeft")
                    one = fare("economy", total["value"], tax.get("value") or 0, tax.get("currencyCode") or "USD",
                               int(seats) if seats is not None else None, False, BRANDS.get(family, family))
                    if best is None or one["miles"] < best["miles"]:
                        best = one
                if best is None:
                    continue
                out.append({
                    "segments": [{
                        "flight": f"{s['marketingCarrierCode']} {s['flightNumber']}",
                        "from": s["originationAirportCode"], "to": s["destinationAirportCode"],
                        "dep": s["departureDateTime"][:16], "arr": s["arrivalDateTime"][:16],
                        "aircraft": s.get("aircraftEquipmentType"),
                        "operated_by": AIRLINES.get(s.get("operatingCarrierCode"), s.get("operatingCarrierCode")),
                    } for s in d["segments"]],
                    "duration_min": d.get("totalDuration"),
                    "fares": [best]})
        return out


PROVIDER = Southwest
