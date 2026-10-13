#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright", "beautifulsoup4", "cryptography"]
# ///
"""Search award (miles) flights across airline loyalty programs from one command."""
import argparse, datetime, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import providers
from providers._base import CABINS, ProviderError

SHORT = {"Y": "economy", "PY": "premium", "J": "business", "F": "first"}


def fmt_time(seg_list):
    dep, arr = seg_list[0]["dep"], seg_list[-1]["arr"]
    days = (datetime.date.fromisoformat(arr[:10]) - datetime.date.fromisoformat(dep[:10])).days if len(arr) >= 10 and len(dep) >= 10 else 0
    return f"{dep[-5:]}–{arr[-5:]}" + (f" +{days}" if days else "")


def render(res, cabins, limit, brands=False):
    head = f"## {res['program']} · {res['origin']} → {res['dest']} · {res['date']}"
    if res.get("error"):
        return f"{head}\n\n{res['error']}\n"
    rows = []
    for it in res["itineraries"]:
        best = {}
        for f in it["fares"]:
            if f["cabin"] in cabins and (f["cabin"] not in best or f["miles"] < best[f["cabin"]]["miles"]):
                best[f["cabin"]] = f
        if best:
            rows.append((min(f["miles"] for f in best.values()), it, best))
    if not rows:
        return f"{head}\n\nNo award space in {', '.join(cabins)}.\n"
    rows.sort(key=lambda r: (r[0], r[1].get("duration_min") or 0))
    lines = [head, "", "| Flights | Time | Route | Duration | " + " | ".join(c.title() for c in cabins) + " |",
             "|---|---|---|---|" + "---|" * len(cabins)]
    for _, it, best in rows[:limit]:
        s = it["segments"]
        dur = it.get("duration_min")
        cells = []
        for c in cabins:
            f = best.get(c)
            if not f:
                cells.append("—")
                continue
            cell = (f"{f['miles']:,} + {f['currency']} {f['tax']:,.2f}".replace(".00", "") if f["tax"] is not None
                    else f"{f['miles']:,} + taxes (not quoted)")
            cell += f" ({f['seats']} left)" if f["seats"] is not None else ""
            cell += " mixed" if f["mixed"] else ""
            cells.append(cell + (f" [{f['brand']}]" if brands and f.get("brand") else ""))
        lines.append(f"| {' + '.join(x['flight'] for x in s)} | {fmt_time(s)} | "
                     f"{'-'.join([s[0]['from']] + [x['to'] for x in s])} | "
                     f"{f'{dur // 60}h{dur % 60:02d}' if dur else ''} | " + " | ".join(cells) + " |")
    if len(rows) > limit:
        lines.append(f"\n({len(rows) - limit} more itineraries; use --limit or --json)")
    return "\n".join(lines) + "\n"


def main():
    avail = providers.available()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("programs", help="comma-separated: " + ", ".join(avail) + ", or 'all' (every program that needs no account)")
    p.add_argument("origin", help="IATA code(s), comma-separated")
    p.add_argument("dest", help="IATA code(s), comma-separated")
    p.add_argument("depart", type=datetime.date.fromisoformat, help="YYYY-MM-DD")
    p.add_argument("ret", nargs="?", type=datetime.date.fromisoformat, help="return date: also searches the reverse direction")
    p.add_argument("--cabin", default="Y,J", help="comma-separated: Y, PY, J, F (default Y,J)")
    p.add_argument("--adults", type=int, default=1)
    p.add_argument("--limit", type=int, default=12, help="rows per table")
    p.add_argument("--pace", type=float, help="seconds between searches (default: each provider's own)")
    p.add_argument("--awards-only", action="store_true",
                   help="drop cash fares that a program merely converts to miles (Qantas Classic Plus, SAS FLEX, …)")
    p.add_argument("--brands", action="store_true", help="show each fare's brand (saver vs dynamic, award chart)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    cabins = [SHORT[c] for c in a.cabin.upper().split(",")]
    # 'all' leaves out account-bound programs: they are slow, rate-limited, and touch the user's credentials
    names = [n for n, p in avail.items() if p.all_cabins] if a.programs == "all" else a.programs.lower().split(",")
    legs = [(o, d, a.depart) for o in a.origin.upper().split(",") for d in a.dest.upper().split(",")]
    if a.ret:
        legs += [(d, o, a.ret) for o, d, _ in legs]
    results = []
    for name in names:
        if name in providers.UNAVAILABLE:
            results.append({"program": name, "provider": name, "error": providers.UNAVAILABLE[name]})
            if not a.json:
                print(f"## {name}\n\nNot searchable: {providers.UNAVAILABLE[name]} (details: reference/coverage.md).\n", flush=True)
            continue
        if name not in avail:
            sys.exit(f"unknown program '{name}'; available: {', '.join(avail)}")
        prov, searched = None, 0
        try:
            prov = avail[name]()
            per_cabin = [None] if prov.all_cabins else cabins
            for o, d, date in legs:
                for cab in per_cabin:
                    if searched:
                        time.sleep(a.pace if a.pace is not None else prov.pace)
                    searched += 1
                    res = {"program": prov.program, "provider": name, "origin": o, "dest": d, "date": str(date)}
                    try:
                        res["itineraries"] = prov.search(o, d, date, a.adults, cab)
                        if a.awards_only and prov.cash_brand:
                            for it in res["itineraries"]:
                                it["fares"] = [f for f in it["fares"] if not re.search(prov.cash_brand, f.get("brand") or "")]
                    except ProviderError as e:
                        res["error"] = str(e)
                    results.append(res)
                    if not a.json:
                        print(render(res, [cab] if cab else cabins, a.limit, a.brands), flush=True)
        except ProviderError as e:  # the provider could not even start
            results.append({"program": avail[name].program, "provider": name, "error": str(e)})
            if not a.json:
                print(f"## {avail[name].program}\n\n{e}\n", flush=True)
        finally:
            if prov:
                prov.close()
    if a.json:
        json.dump(results, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
