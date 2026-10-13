"""Azul Fidelidade (ex-TudoAzul): voeazul.com.br points search, no sign-in needed.

The results page POSTs the search to Azul's availability API and gets every itinerary with every cabin.
Opened cold, the results deep link shows "Ops! Tivemos um problema" and never calls the API, so the first
search of a session goes through the home-page form ("Usar pontos Azul" + "Buscar passagens"); after that
one form search the deep link works in the same browser. Protocol notes: reference/azul.md.
"""
import json
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import CABINS, Provider, ProviderError, fare

HOME = "https://www.voeazul.com.br/br/pt/home"
RESULTS = ("https://www.voeazul.com.br/br/pt/home/selecao-voo?c[0].ds={o}&c[0].std={d:%m/%d/%Y}&c[0].as={a}"
           "&p[0].t=ADT&p[0].c={n}&p[0].cp=false&f.dl=3&f.dr=3&cc=PTS")
API = "/tudoazul/reservation/availability/"  # .../v6/availability
CLASSES = {"economy": "economy", "premiumeconomy": "premium", "business": "business", "first": "first"}
AIRLINES = {"AD": "Azul"}


class Azul(Provider):
    name, program, alliance, pace = "azul", "Azul Fidelidade", "none", 12

    def start(self):
        self._warm = False  # True once a form search has run in this browser
        self._at_home()

    def _at_home(self):
        self.browser.page.goto(HOME, wait_until="domcontentloaded")
        self.browser.page.wait_for_timeout(8000)  # the form and its airport list load after the document
        self._home = True

    def _catch(self, action):
        """Run `action` (click or navigation) and return the availability call's (status, body text)."""
        page = self.browser.page
        try:
            with page.expect_response(lambda r: API in r.url and r.url.endswith("/availability")
                                      and r.request.method == "POST", timeout=60000) as info:
                action()
            resp = info.value
            return resp.status, resp.text()
        except PwTimeout:
            raise ProviderError("voeazul.com.br made no availability call within 60s (blocked, rate-limited, or "
                                f"the site changed); page {page.url[:60]} says: {self._shown()!r}")

    def _shown(self):
        """What the page says when a step failed; raises at once on the site's IP rate-limit page."""
        try:
            shown = " ".join(self.browser.page.inner_text("body").split())
        except Exception:
            return ""
        if "unusual activity from your IP" in shown:
            raise ProviderError("voeazul.com.br limited this IP: 'We detected unusual activity from your IP. "
                                "Access is temporarily limited.' Wait before searching Azul again.")
        at = shown.find("Ops!")
        return shown[at:at + 120] if at >= 0 else shown[:120]

    def _pick(self, label, code):
        """Fill one airport field of the home form. False: the site offers no such airport."""
        page = self.browser.page
        field = page.locator(f'label:has-text("{label}")').first
        try:
            field.wait_for(state="visible", timeout=30000)
        except PwTimeout:
            raise ProviderError(f"voeazul.com.br home form has no '{label}' field (blocked or the site changed); "
                                f"page says: {self._shown()!r}")
        box = field.bounding_box()  # the label sits under the input's wrapper; a locator click is intercepted
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.wait_for_timeout(1500)  # the form expands and re-renders its inputs on the first click
        entry = page.locator(f'input[aria-label="{label}"]')
        if not entry.evaluate("e => e === document.activeElement"):
            entry.focus()
        page.keyboard.type(code, delay=80)
        options = page.locator('[role="option"]')  # each reads "VCP São Paulo - Campinas"
        try:
            options.first.wait_for(state="visible", timeout=10000)
            page.wait_for_timeout(1500)  # let the list narrow to what was typed
            texts = options.all_inner_texts()
        except PwTimeout:
            texts = []
        hit = next((i for i, t in enumerate(texts) if t.split()[:1] == [code]), None)
        if hit is None:
            if entry.input_value() != code:
                raise ProviderError(f"voeazul.com.br home form did not take '{code}' in '{label}' (the site changed)")
            return False
        options.nth(hit).click()
        page.wait_for_timeout(1000)
        return True

    def _form(self, origin, dest, date):
        """One 1-adult points search through the home form; (status, text), or None for an unsold airport."""
        page = self.browser.page
        if not self._home:
            self._at_home()
        self._home = False
        if not self._pick("Origem", origin) or not self._pick("Destino", dest):
            return None  # the half-filled form is dropped: the next search reloads the home page
        day = page.locator('input[aria-label="Data de ida"]')
        try:
            day.focus(timeout=15000)  # the calendar opens by itself after the destination; typing fills it
            page.keyboard.type(date.strftime("%d%m%Y"), delay=80)
            if day.input_value() != date.strftime("%d/%m/%Y"):
                raise ProviderError(f"voeazul.com.br date field shows {day.input_value()!r} after typing {date}")
            page.get_by_role("button", name="Selecionar apenas data de ida").click(timeout=15000)
            page.locator('[data-cy="checkbox-points"]').check(timeout=15000)
            button = page.get_by_role("button", name="Buscar passagens")
            button.wait_for(state="visible", timeout=15000)
        except PwTimeout:
            raise ProviderError("voeazul.com.br home form changed (date, 'Usar pontos Azul' or search button missing)")
        got = self._catch(button.click)
        self._warm = True
        return got

    def search(self, origin, dest, date, adults=1, cabin=None):
        got = None
        if not self._warm:
            got = self._form(origin, dest, date)
            if got is None:
                return []
            if adults != 1:  # the form search was the warm-up; ask again with the passenger count
                self.browser.page.wait_for_timeout(self.pace * 1000)
                got = None
        if got is None:
            url = RESULTS.format(o=origin, a=dest, d=date, n=adults)
            self._home = False
            got = self._catch(lambda: self.browser.page.goto(url, wait_until="domcontentloaded"))
        status, text = got
        try:
            doc = json.loads(text)
        except ValueError:
            raise ProviderError(f"voeazul.com.br availability answered {status} without JSON: {text[:200]!r}")
        if status != 200 or not isinstance(doc.get("data"), dict):
            raise ProviderError(f"voeazul.com.br availability answered {status}: {text[:300]}")
        out = []
        for trip in doc["data"].get("trips") or []:
            for j in trip.get("journeys") or []:
                ident = j["identifier"]
                # a city search also lists nearby airports (LIS brings OPO flights): keep the pair asked for
                if (ident["departureStation"], ident["arrivalStation"]) != (origin, dest):
                    continue
                if not (j.get("status") or {}).get("available", True):
                    continue
                best = {}
                for f in j.get("fares") or []:
                    if not f.get("available"):
                        continue
                    pc = f.get("productClass") or {}
                    flown = [CLASSES.get((s.get("type") or "").replace(" ", "").lower())
                             for s in (f.get("cabin") or {}).get("segmentsCabin") or []]
                    flown = [c for c in flown if c]
                    cab = max(flown, key=CABINS.index) if flown else CLASSES.get((pc.get("category") or "").replace(" ", "").lower())
                    if cab is None:
                        continue
                    # paxPoints holds the all-points price (fareMoney 0) and points + cash splits; only the first is a fare here
                    full = [lv for pp in f.get("paxPoints") or [] for lv in pp.get("levels") or []
                            if lv.get("paxType") == "ADT" and not lv.get("fareMoney")]
                    if not full:
                        continue
                    lv = min(full, key=lambda x: x["points"]["discountedAmount"])
                    one = fare(cab, lv["points"]["discountedAmount"], lv.get("totalMoney") or 0,
                               lv.get("currencyCode") or trip.get("currencyCode") or "BRL", None,
                               len(set(flown)) > 1 or bool((f.get("cabin") or {}).get("mixed")), pc.get("name"))
                    if cab not in best or one["miles"] < best[cab]["miles"]:
                        best[cab] = one
                if not best:
                    continue
                segs = []
                for s in j["segments"]:
                    si, eq = s["identifier"], s.get("equipment") or {}
                    op = si.get("operatedBy") or si["carrierCode"]
                    segs.append({
                        "flight": f"{si['carrierCode']} {si['flightNumber']}",
                        "from": si["departureStation"], "to": si["arrivalStation"],
                        "dep": si["std"][:16], "arr": si["sta"][:16],
                        "aircraft": eq.get("name") or eq.get("type") or None,
                        "operated_by": AIRLINES.get(op, op),
                    })
                d = ident.get("duration") or {}
                out.append({"segments": segs,
                            "duration_min": d.get("days", 0) * 1440 + d.get("hours", 0) * 60 + d.get("minutes", 0) if d else None,
                            "fares": [best[c] for c in CABINS if c in best]})
        return out


PROVIDER = Azul
