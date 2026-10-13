"""Provider contract and the shared itinerary shape.

A provider answers one-way award searches for one loyalty program. `search` returns itineraries:

    {"segments": [{"flight": "AS 123", "from": "SEA", "to": "NRT", "dep": "2026-12-01T11:55",
                   "arr": "2026-12-02T15:25", "aircraft": "Boeing 787-9", "operated_by": "Alaska"}],
     "duration_min": 630,
     "fares": [{"cabin": "economy", "miles": 42500, "tax": 5.6, "currency": "USD",
                "seats": 9, "mixed": False, "brand": "REFUNDABLE_MAIN"}]}

`cabin` is one of CABINS. `seats` is None when the program does not publish a count, and `tax` is None
when the site does not price the cash part at search time. `mixed` marks a
fare whose segments are not all in the named cabin (the name is then the highest cabin flown).
"""
from ._browser import Browser, ProviderError  # noqa: F401  (re-exported for providers)

CABINS = ["economy", "premium", "business", "first"]


class Provider:
    name = ""        # CLI key
    program = ""     # loyalty program, as people call it
    alliance = ""    # "Star Alliance" | "oneworld" | "SkyTeam" | "none"
    pace = 10        # seconds between searches that the site has been seen to tolerate
    all_cabins = True  # False: one search per cabin (the CLI then multiplies searches)
    cash_brand = None  # regex over fare brands that are cash fares priced in miles, not award seats

    def __init__(self):
        self.browser = Browser()
        try:
            self.start()
        except BaseException:
            self.browser.close()  # the caller never gets an object to close
            raise

    def start(self):
        """Warm-up before the first search: home page, sign-in, cookie banners."""

    def search(self, origin, dest, date, adults=1, cabin=None):
        """One-way search on `date` (datetime.date). Providers with all_cabins=False get one `cabin`."""
        raise NotImplementedError

    def close(self):
        self.browser.close()


def fare(cabin, miles, tax, currency, seats=None, mixed=False, brand=None):
    assert cabin in CABINS, cabin
    return {"cabin": cabin, "miles": int(miles), "tax": None if tax is None else round(float(tax), 2), "currency": currency,
            "seats": seats, "mixed": bool(mixed), "brand": brand}
