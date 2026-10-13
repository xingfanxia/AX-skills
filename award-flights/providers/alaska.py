"""Alaska Airlines Atmos Rewards (formerly Mileage Plan): alaskaair.com award search, no sign-in needed.

The results page is SvelteKit; its `__data.json` twin returns the same search as structured data
(devalue-flattened, with streamed chunks). Protocol notes: reference/alaska.md.
"""
import json, time
from urllib.parse import urlencode
from ._base import Provider, ProviderError, fare

RANK = {"COACH": 0, "PREMIUM-COACH": 1, "BUSINESS": 2, "FIRST": 3}
NAMES = ["economy", "premium", "business", "first"]


def unflatten(values, root=0):
    """Decode devalue's flattened graph: every container holds indexes into `values`; negatives are holes."""
    memo = {}

    def hydrate(i):
        if i < 0:
            return None
        if i in memo:
            return memo[i]
        v = values[i]
        if isinstance(v, dict):
            memo[i] = out = {}
            for k, j in v.items():
                out[k] = hydrate(j)
        elif isinstance(v, list):
            if v and isinstance(v[0], str):  # tagged value such as ["Date", "..."] or ["Promise", id]
                memo[i] = out = None
            else:
                memo[i] = out = []
                out.extend(hydrate(j) for j in v)
        else:
            memo[i] = out = v
        return out
    return hydrate(root)


class Alaska(Provider):
    name, program, alliance, pace = "alaska", "Alaska Atmos Rewards", "oneworld", 10

    def start(self):
        # The first document request gets an AWS WAF challenge page; the site's own script clears it
        # and sets the token that the data endpoint then accepts.
        self.browser.page.goto("https://www.alaskaair.com/", wait_until="domcontentloaded")
        time.sleep(8)

    def search(self, origin, dest, date, adults=1, cabin=None):
        qs = urlencode({"A": adults, "O": origin, "D": dest, "OD": date.isoformat(), "OT": "Anytime",
                        "RT": "false", "ShoppingMethod": "onlineaward", "locale": "en-us"})
        status, text = self.browser.page.evaluate(
            """async (qs) => { const r = await fetch('/search/results/__data.json?' + qs);
                               return [r.status, await r.text()]; }""", qs)
        if status != 200 or not text.lstrip().startswith("{"):
            raise ProviderError(f"alaskaair.com answered {status} without data (WAF challenge not cleared?)")
        results = None
        for line in text.splitlines():
            if not line.strip():
                continue
            doc = json.loads(line)
            flats = [n["data"] for n in doc.get("nodes", []) if n and n.get("type") == "data"] or [doc.get("data")]
            for flat in flats:
                obj = unflatten(flat) if flat else None
                if isinstance(obj, dict) and "rows" in obj:
                    results = obj
        if results is None:
            raise ProviderError("no flightResults chunk in the response (site changed)")
        out = []
        for row in results["rows"] or []:
            segs = [{
                "flight": f"{s['displayCarrier']['carrierCode']} {s['displayCarrier']['flightNumber']}",
                "from": s["departureStation"], "to": s["arrivalStation"],
                "dep": s["departureTime"][:16], "arr": s["arrivalTime"][:16], "aircraft": s.get("aircraft"),
                "operated_by": (s.get("operationalDisclosure") or "").replace("Operated by ", "")
                               or s["displayCarrier"]["carrierFullName"],
            } for s in row["segments"]]
            fares = []
            for brand, sol in row["solutions"].items():
                top = max(RANK.get(c, 0) for c in sol["cabins"])
                fares.append(fare(NAMES[top], sol["atmosPoints"], sol["grandTotal"], "USD",
                                  sol.get("seatsRemaining"), sol.get("mixedCabin"), brand))
            out.append({"segments": segs, "duration_min": row.get("duration"), "fares": fares})
        return out


PROVIDER = Alaska
