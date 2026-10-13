#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Developer tool: open a URL in the providers' headless Chrome and record its JSON API traffic.

Usage: sniff.py URL OUT_DIR [--wait SECONDS]
Writes OUT_DIR/NN.json (response bodies), OUT_DIR/NN.req (full POST bodies), OUT_DIR/index.txt (method, status, size, url, post data head), OUT_DIR/page.png.
Use it to find or re-find the search endpoint when adding or repairing a provider.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from providers._browser import Browser

url, out = sys.argv[1], sys.argv[2]
wait = float(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 25
os.makedirs(out, exist_ok=True)
rows = []


def on_response(r):
    ct = r.headers.get("content-type", "")
    if "json" not in ct and "graphql" not in r.url:
        return
    try:
        body = r.body()
    except Exception:
        return
    n = len(rows)
    open(os.path.join(out, f"{n:02d}.json"), "wb").write(body)
    try:
        post = r.request.post_data or ""
    except UnicodeDecodeError:  # binary body (bot-protection telemetry)
        post = ""
    if post:
        open(os.path.join(out, f"{n:02d}.req"), "w").write(post)
    post = post[:300].replace("\n", " ")
    rows.append(f"{n:02d} {r.request.method} {r.status} {len(body):>8} {r.url} | {post}")


with Browser() as b:
    b.page.on("response", on_response)
    try:
        resp = b.page.goto(url, wait_until="domcontentloaded")
        print("document:", resp.status if resp else None, b.page.url[:140])
    except Exception as e:
        print("navigation failed:", type(e).__name__, str(e)[:200])
    b.page.wait_for_timeout(wait * 1000)  # keeps dispatching response events, unlike time.sleep
    print("title:", b.page.title()[:80])
    try:
        b.page.screenshot(path=os.path.join(out, "page.png"), timeout=15000)
    except Exception:
        pass
    open(os.path.join(out, "page.txt"), "w").write(b.page.inner_text("body")[:6000])
    open(os.path.join(out, "page.html"), "w").write(b.page.content())  # some sites inline their data
open(os.path.join(out, "index.txt"), "w").write("\n".join(rows))
print("\n".join(rows))
