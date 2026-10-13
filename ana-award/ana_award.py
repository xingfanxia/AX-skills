#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["curl_cffi", "beautifulsoup4", "cryptography"]
# ///
"""ANA international award search over plain HTTP (JSF app `international_asw` behind Akamai).

Flow: Chrome cookies (SSO + Akamai) -> award search entry -> password step-up -> POST the
search form -> parse flights from the DOM and miles/tax/seats from the inline addRecommendation() calls.
"""
import argparse, datetime, hashlib, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time
from bs4 import BeautifulSoup
from curl_cffi import requests

CACHE = os.path.expanduser("~/.cache/ana-award")
STATE = os.path.join(CACHE, "session.json")
ENTRY = ("https://aswbe-i.ana.co.jp/international_asw/pages/award/search/roundtrip/"
         "award_search_roundtrip_input.xhtml?CONNECTION_KIND=JPN&LANG=en")
# Per-user settings come from the environment so the script itself carries no account details.
CHROME_COOKIES = os.path.expanduser("~/Library/Application Support/Google/Chrome/%s/Cookies"
                                    % os.environ.get("ANA_CHROME_PROFILE", "Default"))
OP_ITEM, OP_VAULT = os.environ.get("ANA_OP_ITEM", "ANA"), os.environ.get("ANA_OP_VAULT")
CABINS = {"Y": "CFF1", "PY": "CFF4", "J": "CFF2", "F": "CFF3"}
AWARD_TYPES = {"1400": "ANA", "1200": "Star Alliance"}  # fare-family code -> award chart
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
            if name == "JSESSIONID":
                continue  # the browser's backend session times out after ~10 min; always start our own
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
    def __init__(self, fresh=False):
        self.s = requests.Session(impersonate="chrome")
        self.s.headers.update({"Accept-Language": "en-US,en;q=0.9"})
        jar = chrome_cookies() if fresh or not os.path.exists(STATE) else json.load(open(STATE))
        for c in jar:
            self.s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
        self.url, self.soup, self.html = None, None, ""

    def _save(self):
        os.makedirs(CACHE, mode=0o700, exist_ok=True)
        jar = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path} for c in self.s.cookies.jar]
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, json.dumps(jar).encode())
        os.close(fd)

    def _take(self, r):
        if r.status_code != 200:
            raise AnaError(f"HTTP {r.status_code} from {r.url.split('?')[0]} (Akamai block or outage)")
        self.url, self.html, self.soup = r.url, r.text, BeautifulSoup(r.text, "html.parser")
        self._save()

    def page(self):
        return re.sub(r".*/pages/", "", self.url.split("?")[0])

    def errors(self):
        seen = []
        for e in self.soup.select(".errorMessage, .errorArea, .modalError, [class*=rror]"):
            t = re.sub(r"\s+", " ", e.get_text(" ", strip=True))
            if t and not any(t in s or s in t for s in seen):
                seen.append(t)
        return seen

    def form(self, pred):
        for f in self.soup.find_all("form"):
            if pred(f):
                return f
        raise AnaError(f"expected form missing on {self.page()}: {self.errors()}")

    def submit(self, form, extra):
        data = {}
        for i in form.find_all(["input", "select"]):
            n, t = i.get("name"), (i.get("type") or "").lower()
            if not n or t in ("submit", "button", "image"):
                continue
            if t in ("checkbox", "radio") and not i.has_attr("checked"):
                continue
            if i.name == "select":
                o = i.find("option", selected=True) or i.find("option")
                data[n] = o.get("value", "") if o else ""
            else:
                data[n] = i.get("value", "")
        data.update(extra)
        data = {k: v for k, v in data.items() if v is not None}  # None = field the browser leaves disabled
        try:
            r = self.s.post(form["action"], data=data, timeout=60,
                            headers={"Referer": self.url, "Origin": "https://aswbe-i.ana.co.jp"})
        except requests.exceptions.Timeout:
            # Akamai tarpits (accepts the POST, never answers) once it scores the client as a bot
            raise AnaError("request hung for 60s: Akamai is throttling this IP/session. Stop, wait 30+ min, "
                           "browse ana.co.jp in Chrome once, then rerun with --fresh. Do not retry in a loop.")
        self._take(r)

    def open_search(self):
        """Land on the award search input page, doing the password step-up when the site asks."""
        self._take(self.s.get(ENTRY, timeout=90))
        if "login" in self.page():
            f = self.form(lambda f: f.find("input", {"name": "password"}))
            if not f.find(class_="userName") and "userName" not in self.html:
                raise AnaError("Chrome's ana.co.jp cookies are not logged in; sign in at ana.co.jp in Chrome, then rerun with --fresh")
            btn = f.find("input", {"type": "submit"})
            self.submit(f, {"password": password(), btn["name"]: btn.get("value", "")})
            if "login" in self.page():  # never retry: repeated bad passwords lock the account
                raise AnaError(f"password step-up rejected: {self.errors()}")
        if "award_search_roundtrip_input" not in self.page():
            raise AnaError(f"unexpected page {self.page()}: {self.errors()}")

    def search(self, origin, dest, depart, ret, cabin, adults):
        self.open_search()
        f = self.form(lambda f: f.get("id") == "conditionInput")
        if not ret:
            self.submit(f, {"toOneway": "toOneway"})
            f = self.form(lambda f: f.get("id") == "conditionInput")
        btn = next(i for i in f.find_all("input", {"type": "submit"}) if i.get("value") == "Search")

        def date(d):
            return (d.strftime("%Y%m%d"), f"{d:%m/%d/%Y} ({WEEKDAYS[d.weekday()]})") if d else (None, None)
        (d1, d1t), (d2, d2t) = date(depart), date(ret)
        self.submit(f, {
            "departureAirportCode:field": origin, "departureAirportCode:field_pctext": origin,
            "arrivalAirportCode:field": dest, "arrivalAirportCode:field_pctext": dest,
            "awardDepartureDate:field": d1, "awardDepartureDate:field_pctext": d1t,
            "awardReturnDate:field": d2, "awardReturnDate:field_pctext": d2t,
            "boardingClass": CABINS[cabin], "adult:count": str(adults), btn["name"]: "Search",
        })
        out = {"origin": origin, "dest": dest, "depart": str(depart), "return": str(ret) if ret else None,
               "cabin": cabin, "adults": adults}
        m = re.search(r"Mileage Balance\s*([\d,]+)", self.soup.get_text(" "))
        out["mileage_balance"] = int(m.group(1).replace(",", "")) if m else None
        if "result" not in self.page() or not self.soup.select_one(".selectItineraryOutbound"):
            out["error"] = self.errors() or [f"no results (page {self.page()})"]
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
        seats = f"{o['out_seats']}/{o['in_seats']}" + (" WL" if o["waitlist"] else "")
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
    p.add_argument("--pace", type=float, default=20, help="seconds to wait between searches")
    p.add_argument("--json", action="store_true")
    p.add_argument("--fresh", action="store_true", help="re-read cookies from Chrome instead of the cached session")
    a = p.parse_args()
    ana, results = Ana(fresh=a.fresh), []
    for o in a.origin.upper().split(","):
        for c in a.cabin.upper().split(","):
            if results:
                time.sleep(a.pace)  # bursts of searches trip Akamai's rate scoring
            results.append(ana.search(o, a.dest.upper(), a.depart, a.ret, c, a.adults))
            if not a.json:
                print(render(results[-1], a.limit), flush=True)
    if a.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=1)
    elif results and results[-1].get("mileage_balance") is not None:
        print(f"Mileage balance: {results[-1]['mileage_balance']:,}")


if __name__ == "__main__":
    try:
        main()
    except AnaError as e:
        sys.exit(f"ana-award: {e}")
