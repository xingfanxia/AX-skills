"""ANA Mileage Club: international award search on aswbe-i.ana.co.jp, signed in as the user.

Unlike the other providers this one needs the member's own session: sign-in cookies are copied from
the user's Chrome profile and ANA's password re-confirmation is answered from the environment or
1Password. One search covers one cabin, and ANA rate-limits searches hard (see reference/ana.md).
"""
import hashlib, os, re, shutil, sqlite3, subprocess, tempfile
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PwTimeout
from ._base import Provider, ProviderError, fare

ENTRY = ("https://aswbe-i.ana.co.jp/international_asw/pages/award/search/roundtrip/"
         "award_search_roundtrip_input.xhtml?CONNECTION_KIND=JPN&LANG=en")
# Per-user settings come from the environment so this file carries no account details.
CHROME_COOKIES = os.path.expanduser("~/Library/Application Support/Google/Chrome/%s/Cookies"
                                    % os.environ.get("ANA_CHROME_PROFILE", "Default"))
OP_ITEM, OP_VAULT = os.environ.get("ANA_OP_ITEM", "ANA"), os.environ.get("ANA_OP_VAULT")
CABIN_CODES = {"economy": "CFF1", "premium": "CFF4", "business": "CFF2", "first": "CFF3"}
# fare-family code -> award chart (economy 1400/1200, business 800/600; other cabins show the raw code)
AWARD_TYPES = {"1400": "ANA award", "800": "ANA award", "1200": "Star Alliance award", "600": "Star Alliance award"}
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
RATE_LIMITED = ("ANA did not answer within 60s: searches are being rate-limited (the result page hangs). "
                "Wait 30+ min and use a larger --pace; do not retry in a loop.")


def chrome_cookies():
    """Decrypt the member's ana.co.jp cookies from the Chrome profile (macOS; one Keychain read)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    pw = subprocess.run(["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
                        capture_output=True, text=True, timeout=90, check=True).stdout.strip()
    key = hashlib.pbkdf2_hmac("sha1", pw.encode(), b"saltysalt", 1003, 16)
    tmp = tempfile.mkdtemp()
    try:
        db = os.path.join(tmp, "c.db")
        shutil.copy(CHROME_COOKIES, db)
        con = sqlite3.connect(db)
        ver = int(con.execute("select value from meta where key='version'").fetchone()[0])
        jar = []
        for host, name, path, enc in con.execute(
                "select host_key,name,path,encrypted_value from cookies where host_key like '%ana.co.jp'"):
            if name == "JSESSIONID" or name == "_abck" or name.startswith(("bm_", "ak_bmsc")):
                continue  # backend session and Akamai state belong to the other browser; ours mints its own
            d = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).decryptor()
            raw = d.update(enc[3:]) + d.finalize()
            raw = raw[:-raw[-1]]
            if ver >= 24:
                raw = raw[32:]  # sha256(host_key) prefix
            jar.append({"domain": host, "name": name, "path": path, "value": raw.decode(), "secure": True})
        return jar
    finally:
        shutil.rmtree(tmp)


def password():
    """AMC password for the step-up: ANA_PASSWORD if set, otherwise the 1Password item named by ANA_OP_ITEM."""
    if os.environ.get("ANA_PASSWORD"):
        return os.environ["ANA_PASSWORD"]
    cmd = ["op", "item", "get", OP_ITEM, "--fields", "password", "--reveal"] + (["--vault", OP_VAULT] if OP_VAULT else [])
    pw = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if pw.returncode != 0:
        raise ProviderError("1Password read failed: " + pw.stderr.strip()[:200])
    return pw.stdout.strip()


def parse_bound(div):
    """Itineraries of one direction, keyed by ANA's flight id (the radio button's data-value)."""
    flights = {}
    for td in div.select("td.selectItineraryCheck"):
        row = td.find_parent("tr")
        segs = []
        for fs in row.select("div.flightSchedule"):
            info = fs.find_next_sibling("div", class_="detailWrap")
            spans = info.select("div.detailInformation > span") if info else []
            txt = [re.sub(r"\s+", " ", s.get_text(" ", strip=True)) for s in spans]
            get = lambda c: (fs.select_one(c).get_text(" ", strip=True) if fs.select_one(c) else None)
            segs.append({
                "flight": re.sub(r"^([A-Z0-9]{2})(\d+)$", r"\1 \2", txt[0]) if txt else None,
                "from": get(".airportDeparture"), "to": get(".airportArrival"),
                "dep": get(".timeDeparture"), "arr": get(".timeArrival"),
                "aircraft": next((s.get("aria-label") for s in spans if s.get("aria-label")), None),
                "operated_by": next((t.replace("Operated by ", "") for t in txt if t.startswith("Operated by")), "ANA"),
            })
        dur = re.search(r"(\d+)h(\d+)min", row.select_one("td.timeRequired").get_text() if row.select_one("td.timeRequired") else "")
        flights[int(td.find("i", attrs={"data-value": True})["data-value"])] = {
            "segments": segs, "duration_min": int(dur.group(1)) * 60 + int(dur.group(2)) if dur else None}
    return flights


def parse_recommendations(html):
    """addRecommendation(...) positional args per asw-RecommendationList.js: 1 outFlightId, 3 fare family,
    7 total cash in JPY, 11 miles, 14/15 seats out/in (negative = not bookable), 19/20 waitlist flags."""
    recs = []
    for call in re.findall(r"addRecommendation\((.*?),\[\{segmentInfoList", html, re.S):
        a = [x.strip().strip("'") for x in call.split(",")]
        recs.append({"out": int(a[1]), "in": int(a[2]), "family": a[3], "miles": int(float(a[11])),
                     "tax": float(a[7]) if a[7] not in ("null", "") else 0.0,
                     "out_seats": int(a[14]), "in_seats": int(a[15]), "waitlist": bool(a[19] or a[20])})
    return recs


class Ana(Provider):
    name, program, alliance = "ana", "ANA Mileage Club", "Star Alliance"
    pace, all_cabins = 150, False

    def start(self):
        self.browser.context.add_cookies(chrome_cookies())
        self.page = self.browser.page

    def _nav(self, action):
        try:
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                action()
        except PwTimeout:
            raise ProviderError(RATE_LIMITED)
        self.html = self.page.content()
        self.soup = BeautifulSoup(self.html, "html.parser")

    def _where(self):
        return re.sub(r".*/pages/", "", self.page.url.split("?")[0])

    def _errors(self):
        seen = []
        for e in self.soup.select(".errorMessage, .errorArea, .modalError, [class*=rror]"):
            t = re.sub(r"\s+", " ", e.get_text(" ", strip=True))
            if t and not any(t in s or s in t for s in seen):
                seen.append(t)
        return seen

    def _open_search(self):
        self._nav(lambda: self.page.goto(ENTRY, wait_until="domcontentloaded"))
        if "login" in self._where():
            if not self.soup.select_one(".userName"):
                raise ProviderError("Chrome's ana.co.jp cookies are not signed in; sign in at ana.co.jp in Chrome first")
            self.page.fill("input[name=password]", password())
            self._nav(lambda: self.page.click("input[type=submit][value=Login]"))
            if "login" in self._where():  # never retry: repeated bad passwords lock the account
                raise ProviderError(f"password step-up rejected: {self._errors()}")
        if "award_search_roundtrip_input" not in self._where():
            raise ProviderError(f"unexpected page {self._where()}: {self._errors()}")

    def search(self, origin, dest, date, adults=1, cabin="economy"):
        self._open_search()
        self._nav(lambda: self.page.click("#conditionInput a[id$=toOneway]"))
        self.page.evaluate("""(v) => { for (const [k, x] of Object.entries(v)) {
            const e = document.getElementsByName(k)[0];
            if (x === null) e.disabled = true; else e.value = x; } }""", {
            "departureAirportCode:field": origin, "departureAirportCode:field_pctext": origin,
            "arrivalAirportCode:field": dest, "arrivalAirportCode:field_pctext": dest,
            "awardDepartureDate:field": date.strftime("%Y%m%d"),
            "awardDepartureDate:field_pctext": f"{date:%m/%d/%Y} ({WEEKDAYS[date.weekday()]})",
            "awardReturnDate:field": None, "awardReturnDate:field_pctext": None,  # the browser disables these one-way
            "boardingClass": CABIN_CODES[cabin], "adult:count": str(adults),
        })
        self._nav(lambda: self.page.click("#conditionInput input[type=submit][value=Search]"))
        bound = self.soup.select_one(".selectItineraryOutbound")
        if "result" not in self._where() or not bound:
            errs = self._errors()
            if any("E_A01P01_0007" in e for e in errs):
                return []  # ANA: this cabin has no award setting or inventory on the route and date
            raise ProviderError("; ".join(errs) or f"no results (page {self._where()})")
        flights = parse_bound(bound)
        for rec in parse_recommendations(self.html):
            if rec["out"] in flights and rec["out_seats"] >= 0:
                # 0 seats: the page's own script treats only counts above 0 as bookable, so 0 is read as waitlist
                waitlist = rec["waitlist"] or rec["out_seats"] == 0
                brand = AWARD_TYPES.get(rec["family"], rec["family"]) + (" (waitlist)" if waitlist else "")
                flights[rec["out"]].setdefault("fares", []).append(
                    fare(cabin, rec["miles"], rec["tax"], "JPY", rec["out_seats"], False, brand))
        out = []
        for f in flights.values():
            for s in f["segments"]:
                s["dep"] = f"{date.isoformat()}T{s['dep']}" if s is f["segments"][0] and s["dep"] else s["dep"]
            f.setdefault("fares", [])
            out.append(f)
        return out


PROVIDER = Ana
