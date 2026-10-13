#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright", "beautifulsoup4", "cryptography"]
# ///
"""ANA international award search (JSF app `international_asw` behind Akamai), driven through headless Chrome.

Flow: copy the member's SSO cookies from Chrome -> open the award search page in a throwaway headless
Chrome -> password step-up -> submit the search form -> parse flights from the DOM and miles/tax/seats
from the inline addRecommendation() calls. The site rate-limits searches hard; see SKILL.md.
"""
import argparse, datetime, hashlib, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PwTimeout, sync_playwright

ENTRY = ("https://aswbe-i.ana.co.jp/international_asw/pages/award/search/roundtrip/"
         "award_search_roundtrip_input.xhtml?CONNECTION_KIND=JPN&LANG=en")
# Per-user settings come from the environment so the script itself carries no account details.
CHROME_COOKIES = os.path.expanduser("~/Library/Application Support/Google/Chrome/%s/Cookies"
                                    % os.environ.get("ANA_CHROME_PROFILE", "Default"))
OP_ITEM, OP_VAULT = os.environ.get("ANA_OP_ITEM", "ANA"), os.environ.get("ANA_OP_VAULT")
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TARPIT = ("the site did not answer within 60s: searches are being rate-limited (the result page hangs). "
          "Stop, wait 30+ min, then rerun with a larger --pace; do not retry in a loop.")
CABINS = {"Y": "CFF1", "PY": "CFF4", "J": "CFF2", "F": "CFF3"}
# fare-family code -> award chart (economy 1400/1200, business 800/600; other cabins show the raw code)
AWARD_TYPES = {"1400": "ANA", "800": "ANA", "1200": "Star Alliance", "600": "Star Alliance"}
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


class AnaError(Exception):
    pass


def chrome_cookies():
    """Decrypt ana.co.jp cookies from the Chrome profile (macOS; reads the Keychain item once)."""
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
            jar.append({"domain": host, "name": name, "path": path, "value": raw.decode()})
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
        raise AnaError("1Password read failed: " + pw.stderr.strip()[:200])
    return pw.stdout.strip()


class Ana:
    """One headless Chrome session (temporary profile, no window) logged in as the Chrome user."""

    def __init__(self):
        ver = subprocess.run([CHROME_BIN, "--version"], capture_output=True, text=True).stdout
        major = re.search(r"(\d+)\.", ver).group(1)
        # Chrome's headless UA says "HeadlessChrome", which Akamai tarpits on the booking host
        ua = (f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
              f"Chrome/{major}.0.0.0 Safari/537.36")
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(channel="chrome", headless=True, args=[
            "--disable-blink-features=AutomationControlled", "--user-agent=" + ua])
        ctx = self._browser.new_context(locale="en-US", viewport={"width": 1440, "height": 900})
        ctx.add_cookies([{**c, "secure": True} for c in chrome_cookies()])
        self.page = ctx.new_page()
        self.page.set_default_timeout(60000)
        self.soup, self.html = None, ""

    def close(self):
        self._browser.close()
        self._pw.stop()

    def _nav(self, action):
        try:
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                action()
        except PwTimeout:
            self._stuck()
        self._read()

    def _stuck(self):
        raise AnaError(f"{TARPIT} (stuck after {self.where()})")

    def _read(self):
        self.html = self.page.content()
        self.soup = BeautifulSoup(self.html, "html.parser")

    def where(self):
        return re.sub(r".*/pages/", "", self.page.url.split("?")[0])

    def errors(self):
        seen = []
        for e in self.soup.select(".errorMessage, .errorArea, .modalError, [class*=rror]"):
            t = re.sub(r"\s+", " ", e.get_text(" ", strip=True))
            if t and not any(t in s or s in t for s in seen):
                seen.append(t)
        return seen

    def open_search(self):
        """Land on the award search input page, doing the password step-up when the site asks."""
        try:
            self.page.goto(ENTRY, wait_until="domcontentloaded")
        except PwTimeout:
            self._stuck()
        self._read()
        if "login" in self.where():
            if not self.soup.select_one(".userName"):
                raise AnaError("Chrome's ana.co.jp cookies are not logged in; sign in at ana.co.jp in Chrome first")
            self.page.fill("input[name=password]", password())
            self._nav(lambda: self.page.click("input[type=submit][value=Login]"))
            if "login" in self.where():  # never retry: repeated bad passwords lock the account
                raise AnaError(f"password step-up rejected: {self.errors()}")
        if "award_search_roundtrip_input" not in self.where():
            raise AnaError(f"unexpected page {self.where()}: {self.errors()}")

    def search(self, origin, dest, depart, ret, cabin, adults):
        self.open_search()
        if not ret:
            self._nav(lambda: self.page.click("#conditionInput a[id$=toOneway]"))

        def date(d):
            return (d.strftime("%Y%m%d"), f"{d:%m/%d/%Y} ({WEEKDAYS[d.weekday()]})") if d else (None, None)
        (d1, d1t), (d2, d2t) = date(depart), date(ret)
        self.page.evaluate("""(v) => { for (const [k, x] of Object.entries(v)) {
            const e = document.getElementsByName(k)[0];
            if (x === null) e.disabled = true; else e.value = x; } }""", {
            "departureAirportCode:field": origin, "departureAirportCode:field_pctext": origin,
            "arrivalAirportCode:field": dest, "arrivalAirportCode:field_pctext": dest,
            "awardDepartureDate:field": d1, "awardDepartureDate:field_pctext": d1t,
            "awardReturnDate:field": d2, "awardReturnDate:field_pctext": d2t,  # disabled in one-way mode
            "boardingClass": CABINS[cabin], "adult:count": str(adults),
        })
        self._nav(lambda: self.page.click("#conditionInput input[type=submit][value=Search]"))
        out = {"origin": origin, "dest": dest, "depart": str(depart), "return": str(ret) if ret else None,
               "cabin": cabin, "adults": adults}
        m = re.search(r"Mileage Balance\s*([\d,]+)", self.soup.get_text(" "))
        out["mileage_balance"] = int(m.group(1).replace(",", "")) if m else None
        if "result" not in self.where() or not self.soup.select_one(".selectItineraryOutbound"):
            out["error"] = self.errors() or [f"no results (page {self.where()})"]
            return out
        out.update(parse_results(self.soup, self.html))
        return out


def _bound(div):
    flights = {}
    for td in div.select("td.selectItineraryCheck"):
        radio = td.find("i", attrs={"data-value": True})
        row = td.find_parent("tr")
        segs = []
        for fs in row.select("div.flightSchedule"):
            info = fs.find_next_sibling("div", class_="detailWrap")
            spans = info.select("div.detailInformation > span") if info else []
            txt = [re.sub(r"\s+", " ", s.get_text(" ", strip=True)) for s in spans]
            ac = next((s.get("aria-label") for s in spans if s.get("aria-label")), None)
            get = lambda c: (fs.select_one(c).get_text(" ", strip=True) if fs.select_one(c) else None)
            segs.append({
                "flight": txt[0] if txt else None, "from": get(".airportDeparture"), "dep": get(".timeDeparture"),
                "to": get(".airportArrival"), "arr": get(".timeArrival"), "aircraft": ac,
                "operated_by": next((t.replace("Operated by ", "") for t in txt if t.startswith("Operated by")), "ANA"),
                "cabin": next((t for t in txt if t.endswith("Class")), None),
            })
        dur = row.select_one("td.timeRequired")
        types = [AWARD_TYPES.get(li["id"].rsplit("_", 1)[-1], li["id"].rsplit("_", 1)[-1])
                 for li in row.select("li[id^=fareTypeNumber_]")]
        flights[int(radio["data-value"])] = {
            "segments": segs, "award_types": types,
            "duration": dur.get_text(" ", strip=True).replace("Total travel time ", "") if dur else None,
            "note": "airport change" if "Self-arranged transfer" in row.get_text() else None,
        }
    return flights


def parse_results(soup, html):
    out = {"outbound": _bound(soup.select_one(".selectItineraryOutbound"))}
    inb = soup.select_one(".selectItineraryInbound")
    out["inbound"] = _bound(inb) if inb else {}
    recs = []
    for call in re.findall(r"addRecommendation\((.*?),\[\{segmentInfoList", html, re.S):
        # positional args per asw-RecommendationList.js: 1 outFlightId, 2 inFlightId, 3/4 fare family,
        # 7 total cash (JPY taxes), 11 miles, 14/15 seats (negative = not bookable), 19/20 waitlist
        a = [x.strip().strip("'") for x in call.split(",")]
        num = lambda x: None if x in ("null", "") else float(x)
        recs.append({
            "out": int(a[1]), "in": int(a[2]) if out["inbound"] else None,
            "award": AWARD_TYPES.get(a[3], a[3]), "miles": int(float(a[11])), "tax_jpy": int(num(a[7]) or 0),
            "out_seats": int(a[14]), "in_seats": int(a[15]),
            "waitlist": bool(a[19] or a[20]),
        })
    out["options"] = sorted(recs, key=lambda r: (r["miles"], r["tax_jpy"]))
    return out


def _fl(f):
    s = f["segments"]
    legs = " → ".join([s[0]["from"]] + [x["to"] for x in s])
    extra = [f["duration"]] + ([f["note"]] if f["note"] else [])
    return f"{'+'.join(x['flight'] for x in s)} {s[0]['dep']}–{s[-1]['arr']} {legs} ({', '.join(e for e in extra if e)})"


def render(r, limit):
    head = f"## {r['origin']} → {r['dest']} {r['cabin']} · {r['depart']}" + (f" / {r['return']}" if r["return"] else "")
    if "error" in r:
        return f"{head}\n\nNo award space returned: {' | '.join(r['error'])}\n"
    lines = [head, "", "| Miles | Tax (JPY) | Award | Seats out/in | Outbound | Return |", "|---|---|---|---|---|---|"]
    for o in r["options"][:limit]:
        # 0 seats: the page's own script treats only counts above 0 as bookable, so 0 is read as waitlist
        seats = f"{o['out_seats']}/{o['in_seats']}" + (" WL" if o["waitlist"] or 0 in (o["out_seats"], o["in_seats"]) else "")
        ret = _fl(r["inbound"][o["in"]]) if o["in"] is not None else "—"
        lines.append(f"| {o['miles']:,} | {o['tax_jpy']:,} | {o['award']} | {seats} | {_fl(r['outbound'][o['out']])} | {ret} |")
    if len(r["options"]) > limit:
        lines.append(f"\n({len(r['options']) - limit} more combinations; use --json or --limit)")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("origin", help="IATA airport/city code(s), comma-separated, e.g. SZX,HKG")
    p.add_argument("dest", help="IATA airport/city code, e.g. TYO")
    p.add_argument("depart", type=datetime.date.fromisoformat, help="YYYY-MM-DD")
    p.add_argument("ret", nargs="?", type=datetime.date.fromisoformat, help="return YYYY-MM-DD; omit for one-way")
    p.add_argument("--cabin", default="Y", help="comma-separated: Y, PY, J, F")
    p.add_argument("--adults", type=int, default=1)
    p.add_argument("--limit", type=int, default=15, help="rows per table")
    p.add_argument("--pace", type=float, default=150, help="seconds to wait between searches (rate limit)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    ana, results, failure = Ana(), [], None
    try:
        for o in a.origin.upper().split(","):
            for c in a.cabin.upper().split(","):
                if results:
                    time.sleep(a.pace)  # three searches inside four minutes got the client blocked for ~30 min
                results.append(ana.search(o, a.dest.upper(), a.depart, a.ret, c, a.adults))
                if not a.json:
                    print(render(results[-1], a.limit), flush=True)
    except AnaError as e:
        failure = e  # still hand over what was collected before the failure
    finally:
        ana.close()
    if a.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=1)
    elif results and results[-1].get("mileage_balance") is not None:
        print(f"Mileage balance: {results[-1]['mileage_balance']:,}")
    if failure:
        raise failure


if __name__ == "__main__":
    try:
        main()
    except AnaError as e:
        sys.exit(f"ana-award: {e}")
