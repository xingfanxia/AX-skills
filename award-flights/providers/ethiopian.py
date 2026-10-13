"""Ethiopian Airlines ShebaMiles: award search on dxbooking.ethiopianairlines.com, no sign-in needed.

Ethiopian books through the same Sabre "DX" app as Virgin Australia, with the same `bookingAirSearch`
GraphQL answer, so this is the Velocity provider pointed at Ethiopian's host. Notes: reference/ethiopian.md.
"""
from .velocity import Velocity


class Ethiopian(Velocity):
    name, program, alliance, pace = "ethiopian", "Ethiopian ShebaMiles", "Star Alliance", 15
    cash_brand = None
    results = "https://dxbooking.ethiopianairlines.com/dx/ETDX/#/flight-selection?"

    def search(self, origin, dest, date, adults=1, cabin=None):
        out = super().search(origin, dest, date, adults, cabin)
        for it in out:
            for f in it["fares"]:
                f["tax"] = None  # the search answer carries 0; the site adds taxes after flight selection
        return out


PROVIDER = Ethiopian
