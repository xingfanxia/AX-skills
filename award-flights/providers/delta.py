"""Delta SkyMiles: delta.com "Shop with Miles", no sign-in needed.

The results page posts one GraphQL query (delta_offers.graphql, copied verbatim from the site) to
offer-api-prd.delta.com as a guest. The provider replays it from inside a delta.com page so the
site's own cookies and bot-protection state apply. Protocol notes: reference/delta.md.
"""
import os, time, uuid
from ._base import Provider, ProviderError, fare

QUERY = open(os.path.join(os.path.dirname(__file__), "delta_offers.graphql")).read()
API = "https://offer-api-prd.delta.com/prd/rm-offer-gql"
RANK = {"economy": 0, "premium": 1, "business": 2, "first": 2}


def cabin_of(brand):
    """Delta brand ids: BMAIN/CMAIN Main, CDCP Comfort (extra-legroom economy), CDPS Premium Select,
    CD1 Delta One, CFIRST domestic First. Partner brands follow the same stems."""
    b = (brand or "").upper()
    if "D1" in b or "BU" in b:
        return "business"
    if "FIRST" in b:
        return "first"
    if "DPS" in b or "PE" in b:
        return "premium"
    return "economy"


class Delta(Provider):
    name, program, alliance, pace = "delta", "Delta SkyMiles", "SkyTeam", 12

    def start(self):
        self.browser.page.goto("https://www.delta.com/flightsearch/book-a-flight", wait_until="domcontentloaded")
        time.sleep(8)  # let the page's bot-protection script report before the first API call

    def search(self, origin, dest, date, adults=1, cabin=None):
        variables = {"offerSearchCriteria": {
            "productGroups": [{"productCategoryCode": "FLIGHTS"}],
            "offersCriteria": {
                "resultsPageNum": 1, "resultsPerRequestNum": 50,
                "preferences": {"refundableOnly": False, "showGlobalRegionalUpgradeCertificate": True,
                                "nonStopOnly": False, "excludeBrandTypes": []},
                "pricingCriteria": {"priceableIn": ["MILES"]},
                "flightRequestCriteria": {
                    "currentTripIndexId": "0", "sortableOptionId": None, "selectedOfferId": "",
                    "searchOriginDestination": [{"departureLocalTs": f"{date.isoformat()}T00:00:00",
                                                 "destinations": [{"airportCode": dest}],
                                                 "origins": [{"airportCode": origin}]}],
                    "sortByBrandId": "MAIN", "additionalCriteriaMap": {"rollOutTag": "GBB"}}},
            "customers": [{"passengerTypeCode": "ADT", "passengerId": str(i + 1)} for i in range(adults)]}}
        headers = {"authorization": "GUEST", "applicationid": "DC", "channelid": "DCOM", "airline": "DL",
                   "x-app-type": "dcom-shop", "x-app-route": "search", "content-type": "application/json",
                   "accept": "application/json, text/plain, */*",
                   "transactionid": f"{uuid.uuid4()}_{int(time.time() * 1000)}"}
        status, doc = self.browser.page.evaluate(
            """async ([url, headers, body]) => {
                const r = await fetch(url, {method: 'POST', headers, body: JSON.stringify(body), credentials: 'include'});
                let j = null; try { j = await r.json(); } catch (e) {}
                return [r.status, j]; }""", [API, headers, {"variables": variables, "query": QUERY}])
        if status != 200 or not doc:
            raise ProviderError(f"Delta offer API answered {status} (blocked or changed)")
        result = (doc.get("data") or {}).get("gqlSearchOffers")
        if not result:
            errs = doc.get("errors") or [{}]
            info = (errs[0].get("extensions") or {}).get("errors") or {}
            if any(str(m.get("code")) == "404" for m in info.get("moreInfo") or []):
                return []  # ROF4002/404: no itineraries for this market and date
            raise ProviderError(f"Delta offer API error {info.get('code')}: {info.get('message')}")
        currency = "USD"
        for po in (result.get("offerDataList") or {}).get("pricingOptions") or []:
            currency = (po.get("pricingOptionDetail") or {}).get("currencyCode") or currency
        out = []
        for s in result.get("gqlOffersSets") or []:
            trip = s["trips"][0]
            segs = [{
                "flight": f"{f['marketingCarrier']['carrierCode']} {f['marketingCarrier']['carrierNum']}",
                "from": f["originAirportCode"], "to": f["destinationAirportCode"],
                "dep": f["scheduledDepartureLocalTs"][:16], "arr": f["scheduledArrivalLocalTs"][:16],
                "aircraft": (f.get("aircraft") or {}).get("fleetTypeCode"),
                "operated_by": (f.get("operatingCarrier") or {}).get("carrierName")
                               or (f.get("operatingCarrier") or {}).get("carrierCode"),
            } for f in trip["flightSegment"]]
            t = trip.get("totalTripTime") or {}
            fares = []
            for o in s.get("offers") or []:
                props = o.get("additionalOfferProperties") or {}
                if o.get("soldOut") or props.get("soldOut") or not props.get("offered"):
                    continue
                try:
                    info = o["offerItems"][0]["retailItems"][0]["retailItemMetaData"]["fareInformation"][0]
                    price = info["farePrice"][0]["totalFarePrice"]
                    miles = price["milesEquivalentPrice"]["mileCnt"]
                    tax = float(price["currencyEquivalentPrice"]["formattedCurrencyAmt"].replace(",", ""))
                except (KeyError, IndexError, TypeError, AttributeError):
                    continue
                if not miles:
                    continue
                brand = props.get("dominantSegmentBrandId")
                cab = cabin_of(brand)
                legs = [cabin_of(b.get("brandId")) for b in info.get("brandByFlightLegs") or []]
                fares.append(fare(cab, miles, tax, currency, info.get("availableSeatCnt"),
                                  any(RANK[c] < RANK[cab] for c in legs), brand))
            out.append({"segments": segs, "fares": fares,
                        # hourCnt is already the whole trip; dayCnt only counts calendar-day changes
                        "duration_min": (t.get("hourCnt") or 0) * 60 + (t.get("minuteCnt") or 0)})
        return out


PROVIDER = Delta
