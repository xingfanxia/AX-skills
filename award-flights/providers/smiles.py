"""GOL Smiles: smiles.com.br miles search, no sign-in needed.

The results page (a deep link, no warm-up visit needed) GETs its own flight-search API for the
"GOL e Avianca" tab. The provider catches that answer, then repeats the same call from inside the page
with forceCongener=true, which is what the "Outras companhias" (partner airlines) tab does. GOL fares
carry their taxes in the search answer; other fares get theirs from the boarding-tax call the page makes
when a fare is confirmed, asked once per routing. Protocol notes: reference/smiles.md.
"""
import datetime, json
from urllib.parse import urlencode
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

PAGE = "https://www.smiles.com.br/mfe/emissao-passagem/?"
SEARCH = "/v1/airlines/search"
TAX = "https://api-airlines-boarding-tax-green.smiles.com.br/v1/airlines/flight/boardingtax?"
# COMFORT is GOL's Premium Economy (the page labels it "Premium"). FIRST was never seen in a response.
CABIN = {"ECONOMIC": "economy", "COMFORT": "premium", "PREMIUM_ECONOMIC": "premium", "BUSINESS": "business",
         "FIRST": "first"}
AIRCRAFT = {"738": "Boeing 737-800", "7M8": "Boeing 737 MAX 8", "319": "Airbus A319", "320": "Airbus A320",
            "32N": "Airbus A320neo", "321": "Airbus A321", "332": "Airbus A330-200", "339": "Airbus A330-900neo",
            "788": "Boeing 787-8", "789": "Boeing 787-9", "77W": "Boeing 777-300ER", "359": "Airbus A350-900"}
MAX_TAX_CALLS = 40
# Runs in the page: GET each URL in turn with the given headers, stop at the first answer that is not 200.
FETCH = """async ([urls, headers, pause]) => {
  const out = [];
  for (const u of urls) {
    try {
      const r = await fetch(u, {headers});
      out.push([r.status, await r.text()]);
      if (r.status !== 200) break;
    } catch (e) { out.push([0, String(e)]); break; }
    await new Promise(done => setTimeout(done, pause));
  }
  return out;
}"""


class Smiles(Provider):
    name, program, alliance, pace = "smiles", "GOL Smiles", "none", 15

    def search(self, origin, dest, date, adults=1, cabin=None):
        page = self.browser.page
        noon = datetime.datetime(date.year, date.month, date.day, 15, tzinfo=datetime.timezone.utc)  # 12:00 in Brasília
        url = PAGE + urlencode({
            "adults": adults, "cabin": "ALL", "children": 0, "departureDate": int(noon.timestamp() * 1000),
            "infants": 0, "isElegible": "false", "isFlexibleDateChecked": "false", "returnDate": "",
            "searchType": "g3", "segments": 1, "tripType": 2, "originAirport": origin, "originCity": "",
            "originCountry": "", "originAirportIsAny": "false", "destinationAirport": dest, "destinCity": "",
            "destinCountry": "", "destinAirportIsAny": "false", "novo-resultado-voos": "true"})
        try:
            with page.expect_response(lambda r: SEARCH in r.url and r.request.method == "GET") as info:
                page.goto(url, wait_until="domcontentloaded")
            resp = info.value
            status, text = resp.status, resp.text()
        except PwTimeout:
            raise ProviderError("smiles.com.br made no flight-search call within 60s (blocked, rate-limited, "
                                "or the site changed)")
        own = self._flights(status, text, "GOL/Avianca")
        sent = resp.request.headers
        headers = {k: sent[k] for k in ("x-api-key", "channel") if k in sent}
        if "forceCongener=false" not in resp.url:
            raise ProviderError(f"smiles.com.br search URL changed shape: {resp.url[:200]}")
        page.wait_for_timeout(1500)
        (status, text), = page.evaluate(FETCH, [[resp.url.replace("forceCongener=false", "forceCongener=true")],
                                                headers, 0])
        partner = self._flights(status, text, "partner-airline")

        merged = {}  # same flights in another cabin or fare bucket arrive as separate entries
        for f in own + partner:
            cab = CABIN.get(f.get("cabin"))
            std = next((x for x in f.get("fareList") or [] if x.get("type") == "SMILES" and x.get("miles")), None)
            if cab is None or std is None or not f.get("legList"):
                continue
            key = tuple((l["marketingAirline"]["code"], l["flightNumber"], l["departure"]["date"]) for l in f["legList"])
            it = merged.setdefault(key, {"flight": f, "best": {}})
            if cab not in it["best"] or std["miles"] < it["best"][cab][1]["miles"]:
                it["best"][cab] = (f, std)

        # GOL fares state their taxes (g3.costTax); the rest are asked for, as the page does on "Confirmar
        # seleção". Taxes follow the routing, not the departure time, so one call serves every fare with the
        # same carriers, airports, cabin and carrier surcharge: ~20 calls a search instead of ~60, which the
        # tax API stopped answering part-way.
        # A fare the tax API refuses with code 113 ("indisponibilidade de assentos") cannot be booked: it is
        # dropped, and the next fare of the same routing is asked instead.
        ask = {}
        for it in merged.values():
            for cab, (f, std) in list(it["best"].items()):
                if (std.get("g3") or {}).get("costTax") is None:
                    ask.setdefault(self._tax_key(f), []).append((it, cab, f, std))
        taxes, calls = {}, 0
        for key, same in ask.items():
            for it, cab, f, std in same:
                if key in taxes:
                    break
                if calls >= MAX_TAX_CALLS:
                    raise ProviderError(f"smiles.com.br needed more than {MAX_TAX_CALLS} boarding-tax calls for one search")
                page.wait_for_timeout(800 if calls else 0)
                calls += 1
                (status, text), = page.evaluate(FETCH, [[TAX + urlencode({
                    "type": f.get("type") or "SEGMENT_1", "uid": f["uid"], "fareuid": std["uid"],
                    "adults": 1, "children": 0, "infants": 0})], {"channel": headers.get("channel", "WEB")}, 0])
                try:
                    doc = json.loads(text)
                    if str(doc.get("errorCode")) == "113":
                        del it["best"][cab]
                        continue
                    taxes[key] = doc["totals"]["totalBoardingTax"]["money"]
                except (ValueError, KeyError, TypeError, AttributeError):
                    raise ProviderError(f"smiles.com.br boarding-tax call {calls} answered {status}: {text[:200]!r} "
                                        f"(rate-limited, or the site changed)")
            if key not in taxes:  # every fare of this routing was refused
                for it, cab, f, std in same:
                    it["best"].pop(cab, None)

        out = []
        for it in merged.values():
            if not it["best"]:
                continue
            f = it["flight"]
            fares = []
            for cab in CABINS:
                if cab not in it["best"]:
                    continue
                ff, std = it["best"][cab]
                g3tax = (std.get("g3") or {}).get("costTax")
                club = next((x["miles"] for x in ff["fareList"] if x.get("type") == "SMILES_CLUB" and x.get("miles")), None)
                fares.append(fare(
                    cab, std["miles"], g3tax if g3tax is not None else taxes[self._tax_key(ff)], "BRL", ff.get("availableSeats"),
                    any(CABIN.get(l.get("cabin")) != cab for l in ff["legList"]),
                    f"Smiles; Clube Smiles {club}" if club and club != std["miles"] else "Smiles"))
            d = f.get("duration") or {}
            out.append({
                "segments": [{
                    "flight": f"{l['marketingAirline']['code']} {l['flightNumber']}",
                    "from": l["departure"]["airport"]["code"], "to": l["arrival"]["airport"]["code"],
                    "dep": l["departure"]["date"][:16], "arr": l["arrival"]["date"][:16],
                    "aircraft": AIRCRAFT.get(l.get("equipment"), l.get("equipment")),
                    "operated_by": ((l.get("operationAirline") or {}).get("name") or "").split(" (")[0] or None,
                } for l in f["legList"]],
                "duration_min": d["hours"] * 60 + d["minutes"] if d else None,
                "fares": fares})
        return out

    @staticmethod
    def _tax_key(f):
        return (tuple((l["marketingAirline"]["code"], l["departure"]["airport"]["code"],
                       l["arrival"]["airport"]["code"]) for l in f["legList"]), f.get("cabin"), f.get("airlineTax"))

    @staticmethod
    def _flights(status, text, which):
        try:
            doc = json.loads(text)
        except ValueError:
            raise ProviderError(f"smiles.com.br {which} search answered {status} without JSON: {text[:200]!r}")
        if status != 200 or "requestedFlightSegmentList" not in doc:
            raise ProviderError(f"smiles.com.br {which} search answered {status}: {text[:200]}")
        return [f for seg in doc["requestedFlightSegmentList"] or [] for f in seg.get("flightList") or []]


PROVIDER = Smiles
