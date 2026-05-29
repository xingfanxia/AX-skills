#!/usr/bin/env python3
"""珠宝营销 Vogue 风格 Lookbook 渲染器

扫描 jewelry_bundle/<ts>/ 目录，把 analysis.json + copy.md + marketing|design/*.jpg
渲染成单页 index.html（米白 / 香槟金 / 墨 三色 + Cormorant Garamond + Inter）。

用法:
  python3 lookbook_renderer.py <bundle_dir> [--open]

  bundle_dir 应包含:
    analysis.json
    copy.md
    marketing/   (12 张图，finished_product pipeline)
    或 design/   (8 张图，raw_material pipeline)
"""
import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any


# ---------- 12 templates (finished_product) ----------
MARKETING_LAYOUTS = [
    # (template_id, label, span)  — span = grid column span (out of 12)
    ("hero",                "棚拍主图",      12),
    ("wristNeck",           "上手 · 锁骨",   7),
    ("gemCutDetail",        "宝石微距",      5),
    ("sceneStyleWear",      "场景佩戴",      5),
    ("flatLayEditorial",    "单品平铺",      7),
    ("moodboard",           "品牌情绪",      6),
    ("wearStyleGrid",       "一饰多搭",      6),
    ("giftScene",           "送礼场景",      12),
    ("priceAnchor",         "价格锚点",      5),
    ("meaningCraftPoster",  "寓意工艺",      7),
    ("knowhowAvoid",        "选购避坑",      7),
    ("starTestimonial",     "明星种草",      5),
]

# ---------- 8 templates (raw_material design pipeline) ----------
DESIGN_LAYOUTS = [
    ("sketch",          "水彩手绘",  12),
    ("sketchMulti",     "工程蓝图",  6),
    ("rendering3d",     "3D 渲染",   6),
    ("wearing",         "佩戴效果",  7),
    ("materialBreak",   "材质拆解",  5),
    ("moodboard",       "灵感拼贴",  6),
    ("colorDna",        "水彩色卡",  6),
    ("cad3d",           "CAD 技术图", 12),
]


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · Edit No. {issue}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@300;400;500;600&family=Noto+Serif+SC:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --paper: #faf6f0;
  --paper-warm: #f3ece0;
  --paper-edge: #e8dfce;
  --ink: #1a1a1a;
  --ink-soft: #3a3a36;
  --grey: #6b6660;
  --grey-soft: #a8a39c;
  --champagne: #c9a877;
  --champagne-deep: #a8854a;
  --rule: #d8cfbc;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
  background: var(--paper);
  color: var(--ink);
  font-family: 'Inter', 'Noto Serif SC', -apple-system, sans-serif;
  font-size: 15px;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}}

body {{ overflow-x: hidden; }}

::selection {{ background: var(--champagne); color: var(--paper); }}

/* Container */
.page {{
  max-width: 1320px;
  margin: 0 auto;
  padding: 56px 64px 120px;
}}

/* Top masthead */
.masthead {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--ink);
  margin-bottom: 96px;
}}
.masthead .left, .masthead .right {{
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.32em;
  color: var(--ink);
  text-transform: uppercase;
  font-weight: 500;
}}
.masthead .right {{ text-align: right; font-variant-numeric: tabular-nums; }}
.masthead .center {{
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 0.08em;
  font-style: italic;
}}

/* Cover */
.cover {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  margin-bottom: 140px;
  position: relative;
}}
.cover .kicker {{
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  letter-spacing: 0.4em;
  color: var(--champagne-deep);
  text-transform: uppercase;
  margin-bottom: 8px;
}}
.cover h1 {{
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-weight: 500;
  font-size: clamp(56px, 8.4vw, 120px);
  line-height: 0.95;
  letter-spacing: -0.01em;
  color: var(--ink);
  max-width: 1100px;
  text-wrap: balance;
  word-break: keep-all;
  overflow-wrap: anywhere;
}}
.cover h1 .sub {{
  display: block;
  font-style: italic;
  font-weight: 400;
  font-size: 0.4em;
  color: var(--ink-soft);
  letter-spacing: 0.01em;
  margin-top: 18px;
  line-height: 1.2;
}}
.cover .byline {{
  margin-top: 36px;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.3em;
  color: var(--grey);
  text-transform: uppercase;
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
}}
.cover .byline span {{ position: relative; }}
.cover .byline span + span::before {{
  content: '';
  position: absolute;
  left: -16px;
  top: 50%;
  width: 4px;
  height: 1px;
  background: var(--champagne);
  transform: translateY(-50%);
}}

/* Editorial intro pullquote */
.pullquote {{
  max-width: 880px;
  margin: 0 auto 140px;
  text-align: center;
  position: relative;
  padding: 64px 32px;
}}
.pullquote::before, .pullquote::after {{
  content: '';
  position: absolute;
  left: 50%;
  width: 48px;
  height: 1px;
  background: var(--champagne);
  transform: translateX(-50%);
}}
.pullquote::before {{ top: 0; }}
.pullquote::after {{ bottom: 0; }}
.pullquote q {{
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-size: clamp(22px, 2.6vw, 32px);
  font-weight: 400;
  font-style: italic;
  line-height: 1.55;
  color: var(--ink);
  display: block;
  quotes: '\201C' '\201D';
}}
.pullquote q::before, .pullquote q::after {{
  font-family: 'Cormorant Garamond', serif;
  color: var(--champagne);
  font-size: 1.4em;
  vertical-align: -0.15em;
}}
.pullquote cite {{
  display: block;
  margin-top: 24px;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.4em;
  color: var(--grey);
  text-transform: uppercase;
  font-style: normal;
}}

/* Section header */
.section-head {{
  display: grid;
  grid-template-columns: 100px 1fr auto;
  align-items: baseline;
  gap: 28px;
  margin: 0 0 56px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--rule);
}}
.section-head .num {{
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 32px;
  font-weight: 400;
  color: var(--champagne-deep);
}}
.section-head .title {{
  font-family: 'Cormorant Garamond', serif;
  font-size: 38px;
  font-weight: 500;
  letter-spacing: -0.005em;
  color: var(--ink);
}}
.section-head .meta {{
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.32em;
  color: var(--grey);
  text-transform: uppercase;
}}

/* Gallery */
.gallery {{
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 28px;
  margin-bottom: 140px;
}}
.shot {{
  position: relative;
  overflow: hidden;
}}
.shot.span-12 {{ grid-column: span 12; }}
.shot.span-8 {{ grid-column: span 8; }}
.shot.span-7 {{ grid-column: span 7; }}
.shot.span-6 {{ grid-column: span 6; }}
.shot.span-5 {{ grid-column: span 5; }}
.shot.span-4 {{ grid-column: span 4; }}

.shot a {{
  display: block;
  position: relative;
}}
.shot img {{
  display: block;
  width: 100%;
  height: auto;
  background: var(--paper-warm);
  transition: transform 800ms cubic-bezier(0.22, 1, 0.36, 1);
}}
.shot a:hover img {{ transform: scale(1.015); }}
.shot .cap {{
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
}}
.shot .cap .num {{
  font-family: 'Inter', sans-serif;
  font-size: 10px;
  letter-spacing: 0.32em;
  color: var(--champagne-deep);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}}
.shot .cap .label {{
  font-family: 'Cormorant Garamond', 'Noto Serif SC', serif;
  font-style: italic;
  font-size: 16px;
  color: var(--ink-soft);
  flex: 1;
}}

/* Copy / 文案 section */
.copy-section {{ margin-bottom: 140px; }}
.copy-tabs {{
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  margin-bottom: 56px;
}}
.copy-tab {{
  flex: 1 1 auto;
  min-width: 140px;
  padding: 18px 18px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--rule);
  font-family: 'Inter', 'Noto Serif SC', sans-serif;
  font-size: 12px;
  letter-spacing: 0.28em;
  color: var(--grey);
  cursor: pointer;
  transition: all 200ms ease;
  text-align: center;
  position: relative;
  font-weight: 500;
}}
.copy-tab:last-child {{ border-right: none; }}
.copy-tab:hover {{ color: var(--ink); background: rgba(201, 168, 119, 0.06); }}
.copy-tab.active {{
  color: var(--ink);
  background: var(--paper-warm);
}}
.copy-tab.active::after {{
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--champagne-deep);
}}

.copy-panel {{
  display: none;
  grid-template-columns: 1fr 1fr;
  gap: 56px;
}}
.copy-panel.active {{ display: grid; }}

@media (max-width: 880px) {{
  .copy-panel {{ grid-template-columns: 1fr; }}
}}

.copy-col h4 {{
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 22px;
  font-weight: 500;
  margin-bottom: 18px;
  color: var(--ink);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--rule);
}}
.copy-col ol, .copy-col ul {{
  list-style: none;
  margin-bottom: 36px;
}}
.copy-col li {{
  padding: 10px 0;
  font-family: 'Noto Serif SC', 'Inter', serif;
  font-size: 14px;
  line-height: 1.65;
  color: var(--ink-soft);
  display: flex;
  gap: 14px;
  border-bottom: 1px dotted var(--rule);
}}
.copy-col li:last-child {{ border-bottom: none; }}
.copy-col li::before {{
  content: attr(data-n);
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  color: var(--champagne-deep);
  flex-shrink: 0;
  font-size: 13px;
  letter-spacing: 0;
  min-width: 18px;
}}

.copy-post {{
  background: var(--paper-warm);
  padding: 36px 40px;
  border-left: 2px solid var(--champagne);
  position: relative;
  margin-bottom: 24px;
}}
.copy-post .post-head {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--rule);
}}
.copy-post .post-head h5 {{
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 18px;
  font-weight: 500;
  color: var(--ink);
}}
.copy-btn {{
  font-family: 'Inter', sans-serif;
  font-size: 10px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--champagne-deep);
  background: transparent;
  border: 1px solid var(--champagne);
  padding: 6px 14px;
  cursor: pointer;
  transition: all 200ms ease;
  font-weight: 500;
}}
.copy-btn:hover {{ background: var(--champagne); color: var(--paper); }}
.copy-btn.copied {{ background: var(--ink); color: var(--paper); border-color: var(--ink); }}
.copy-post .post-body {{
  font-family: 'Noto Serif SC', 'Inter', serif;
  font-size: 14px;
  line-height: 1.95;
  color: var(--ink);
  white-space: pre-wrap;
}}
.copy-tags {{
  margin-top: 18px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}
.copy-tags .tag {{
  font-family: 'Inter', 'Noto Serif SC', sans-serif;
  font-size: 11px;
  letter-spacing: 0.05em;
  color: var(--champagne-deep);
  padding: 4px 10px;
  border: 1px solid var(--champagne);
  border-radius: 999px;
  background: rgba(201, 168, 119, 0.06);
}}

/* Analysis details */
.details {{ margin-bottom: 120px; }}
.detail-card {{
  border-top: 1px solid var(--rule);
  padding: 28px 0;
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 36px;
}}
.detail-card:last-child {{ border-bottom: 1px solid var(--rule); }}
.detail-card .label {{
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.32em;
  color: var(--grey);
  text-transform: uppercase;
  align-self: start;
  padding-top: 4px;
}}
.detail-card .body {{
  font-family: 'Noto Serif SC', 'Inter', serif;
  font-size: 14px;
  line-height: 1.85;
  color: var(--ink-soft);
}}
.detail-card .body strong {{
  font-weight: 500;
  color: var(--ink);
}}
.detail-card ul {{
  list-style: none;
}}
.detail-card li {{
  padding: 6px 0;
  position: relative;
  padding-left: 22px;
}}
.detail-card li::before {{
  content: '—';
  position: absolute;
  left: 0;
  color: var(--champagne);
}}

/* Colophon */
.colophon {{
  border-top: 1px solid var(--ink);
  padding-top: 40px;
  margin-top: 80px;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 36px;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--grey);
  text-transform: uppercase;
}}
.colophon .end {{
  font-family: 'Cormorant Garamond', serif;
  font-style: italic;
  font-size: 18px;
  text-transform: none;
  letter-spacing: 0.05em;
  text-align: center;
  color: var(--ink);
}}
.colophon .right {{ text-align: right; }}

/* Mobile */
@media (max-width: 880px) {{
  .page {{ padding: 32px 22px 80px; }}
  .masthead {{ margin-bottom: 56px; }}
  .cover {{ margin-bottom: 80px; }}
  .pullquote {{ margin-bottom: 80px; padding: 40px 16px; }}
  .gallery {{ gap: 18px; margin-bottom: 80px; }}
  .shot.span-12, .shot.span-8, .shot.span-7, .shot.span-6, .shot.span-5, .shot.span-4 {{
    grid-column: span 12;
  }}
  .copy-tabs {{ flex-direction: column; }}
  .copy-tab {{ border-right: none; border-bottom: 1px solid var(--rule); padding: 14px; }}
  .copy-tab:last-child {{ border-bottom: none; }}
  .detail-card {{ grid-template-columns: 1fr; gap: 14px; }}
  .colophon {{ grid-template-columns: 1fr; gap: 18px; text-align: left; }}
  .colophon .right {{ text-align: left; }}
}}

/* Animation */
.reveal {{ opacity: 0; transform: translateY(12px); transition: opacity 800ms ease, transform 800ms ease; }}
.reveal.in {{ opacity: 1; transform: translateY(0); }}
</style>
</head>
<body>
<div class="page">

  <header class="masthead">
    <div class="left">珠宝 · Edit</div>
    <div class="center">{masthead_brand}</div>
    <div class="right">{date_long} · No. {issue}</div>
  </header>

  <section class="cover">
    <div class="kicker">{kicker}</div>
    <h1>
      {cover_title}
      <span class="sub">{cover_sub}</span>
    </h1>
    <div class="byline">
      {byline_chips}
    </div>
  </section>

  {pullquote_block}

  <section class="gallery-section">
    <div class="section-head">
      <span class="num">i.</span>
      <span class="title">The Edit</span>
      <span class="meta">{gallery_count} 帧 · {pipeline_label}</span>
    </div>
    <div class="gallery">
      {gallery_items}
    </div>
  </section>

  {copy_section}

  {details_section}

  <footer class="colophon">
    <div class="left">Generated · {date_short}</div>
    <div class="end">— fin —</div>
    <div class="right">识川 shichuan.ax0x.ai · jewelry-marketing</div>
  </footer>

</div>

<script>
// Tab switching
const tabs = document.querySelectorAll('.copy-tab');
const panels = document.querySelectorAll('.copy-panel');
tabs.forEach((tab) => {{
  tab.addEventListener('click', () => {{
    const idx = tab.dataset.idx;
    tabs.forEach(t => t.classList.toggle('active', t.dataset.idx === idx));
    panels.forEach(p => p.classList.toggle('active', p.dataset.idx === idx));
  }});
}});

// Copy buttons
document.querySelectorAll('.copy-btn').forEach((btn) => {{
  btn.addEventListener('click', async () => {{
    const target = btn.dataset.target;
    const el = document.getElementById(target);
    if (!el) return;
    try {{
      await navigator.clipboard.writeText(el.innerText.trim());
      const orig = btn.textContent;
      btn.textContent = '已复制';
      btn.classList.add('copied');
      setTimeout(() => {{
        btn.textContent = orig;
        btn.classList.remove('copied');
      }}, 1600);
    }} catch (e) {{
      console.error(e);
    }}
  }});
}});

// Reveal on scroll
const io = new IntersectionObserver((entries) => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{ e.target.classList.add('in'); io.unobserve(e.target); }}
  }});
}}, {{ threshold: 0.1, rootMargin: '0px 0px -80px 0px' }});
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
</script>
</body>
</html>
"""


# ---------- copy.md parser ----------
_STYLE_HEADER = re.compile(r"^## (\d+)\.\s*(.+?)$", re.MULTILINE)
_SUB_HEADER = re.compile(r"^### (.+?)$", re.MULTILINE)


def parse_copy_md(text: str) -> dict:
    """解析 copy.md → {product: {...}, styles: [{name, hooks, points, post, tags}, ...]}"""
    parts = text.split("# 小红书文案", 1)
    product_md = parts[0].strip()
    copy_md = "# 小红书文案" + parts[1] if len(parts) > 1 else ""

    styles: list[dict] = []
    style_blocks = re.split(r"\n## \d+\.\s*", "\n" + copy_md)[1:]  # drop the leading content before first style
    # Re-split by style headers more carefully:
    style_blocks = []
    for m in _STYLE_HEADER.finditer(copy_md):
        styles_starts = [(m.start(), m.group(1), m.group(2).strip())]
        style_blocks.append(styles_starts[0])

    starts = [m.start() for m in _STYLE_HEADER.finditer(copy_md)]
    headers = [m for m in _STYLE_HEADER.finditer(copy_md)]
    for i, hm in enumerate(headers):
        start = hm.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(copy_md)
        block = copy_md[start:end]
        style = _parse_style_block(hm.group(1), hm.group(2).strip(), block)
        styles.append(style)

    return {"product_md": product_md, "styles": styles}


def _parse_style_block(num: str, name: str, block: str) -> dict:
    """从单个 ## N. 风格 block 中抓 标题/卖点/正文/标签"""
    sections = {}
    sub_headers = list(_SUB_HEADER.finditer(block))
    for i, sm in enumerate(sub_headers):
        sec_name = sm.group(1).strip()
        body_start = sm.end()
        body_end = sub_headers[i + 1].start() if i + 1 < len(sub_headers) else len(block)
        sections[sec_name] = block[body_start:body_end].strip()

    sub_name = ""
    # Some styles include `_English · 中文_` italic line below ## header
    body_lines = block.splitlines()
    for line in body_lines[1:3]:
        s = line.strip()
        if s.startswith("_") and s.endswith("_"):
            sub_name = s.strip("_")
            break

    hooks_text = ""
    for key in ("标题（5 条候选）", "标题"):
        if key in sections:
            hooks_text = sections[key]
            break
    hooks = re.findall(r"^\d+\.\s*(.+?)$", hooks_text, re.MULTILINE)

    points_text = sections.get("卖点", "")
    points = re.findall(r"^-\s*(.+?)$", points_text, re.MULTILINE)

    post = sections.get("正文", "").strip()

    tags_text = sections.get("话题标签", "")
    tags = re.findall(r"(#[^\s#]+)", tags_text)

    return {
        "num": num,
        "name": name,
        "sub_name": sub_name,
        "hooks": hooks,
        "points": points,
        "post": post,
        "tags": tags,
    }


# ---------- HTML helpers ----------
def _esc(s: Any) -> str:
    return html.escape(str(s) if s is not None else "")


def _build_gallery(bundle_dir: pathlib.Path, pipeline: str) -> tuple[str, int, str]:
    """扫描 marketing/ or design/ 目录组装 gallery HTML。返回 (html, count, label)"""
    layouts = MARKETING_LAYOUTS if pipeline == "marketing" else DESIGN_LAYOUTS
    sub = bundle_dir / pipeline
    items: list[str] = []
    count = 0
    for i, (tid, label, span) in enumerate(layouts, 1):
        # Find file matching prefix `NN_<tid>` with any image ext
        matches = list(sub.glob(f"{i:02d}_{tid}.*"))
        if not matches:
            matches = list(sub.glob(f"{i:02d}_*"))
        if not matches:
            continue
        rel = f"{pipeline}/{matches[0].name}"
        items.append(
            f'''<figure class="shot span-{span} reveal">
  <a href="{_esc(rel)}" target="_blank" rel="noopener">
    <img src="{_esc(rel)}" alt="{_esc(label)}" loading="lazy">
  </a>
  <figcaption class="cap">
    <span class="num">{i:02d} · {_esc(tid)}</span>
    <span class="label">{_esc(label)}</span>
  </figcaption>
</figure>'''
        )
        count += 1
    pipeline_label = "Marketing Edit" if pipeline == "marketing" else "Design Suite"
    return "\n".join(items), count, pipeline_label


def _build_copy_section(parsed: dict) -> str:
    styles = parsed["styles"]
    if not styles:
        return ""

    tabs_html: list[str] = []
    panels_html: list[str] = []

    for i, st in enumerate(styles):
        active_class = " active" if i == 0 else ""
        tabs_html.append(
            f'<button class="copy-tab{active_class}" data-idx="{i}">{st["num"]}. {_esc(st["name"])}</button>'
        )

        hooks_html = "\n".join(
            f'<li data-n="{j:02d}">{_esc(h)}</li>'
            for j, h in enumerate(st["hooks"], 1)
        )
        points_html = "\n".join(
            f'<li data-n="·">{_esc(p)}</li>'
            for p in st["points"]
        )
        tags_html = "\n".join(
            f'<span class="tag">{_esc(t)}</span>'
            for t in st["tags"]
        )
        post_id = f"copy-post-{i}"

        panels_html.append(f'''<div class="copy-panel{active_class}" data-idx="{i}">
  <div class="copy-col">
    <h4>标题 · Headlines</h4>
    <ol>
      {hooks_html}
    </ol>
    <h4>卖点 · Selling Points</h4>
    <ul>
      {points_html}
    </ul>
  </div>
  <div class="copy-col">
    <h4>正文 · The Post</h4>
    <div class="copy-post">
      <div class="post-head">
        <h5>{_esc(st["sub_name"] or st["name"])}</h5>
        <button class="copy-btn" data-target="{post_id}">复制全文</button>
      </div>
      <div class="post-body" id="{post_id}">{_esc(st["post"])}</div>
    </div>
    <div class="copy-tags">
      {tags_html}
    </div>
  </div>
</div>''')

    return f'''<section class="copy-section">
  <div class="section-head">
    <span class="num">ii.</span>
    <span class="title">The Voice</span>
    <span class="meta">{len(styles)} 风格 · 文案矩阵</span>
  </div>
  <div class="copy-tabs">
    {''.join(tabs_html)}
  </div>
  <div class="copy-panels">
    {''.join(panels_html)}
  </div>
</section>'''


def _build_details_section(analysis: dict) -> str:
    cards: list[str] = []

    materials = analysis.get("materials", [])
    if materials:
        lis = "\n".join(
            f'<li><strong>{_esc(m.get("part", ""))}</strong> · {_esc(m.get("material", ""))} — {_esc(m.get("detail", ""))}</li>'
            for m in materials
        )
        cards.append(f'<div class="detail-card"><div class="label">Material</div><div class="body"><ul>{lis}</ul></div></div>')

    gems = analysis.get("gemstones", [])
    if gems:
        lis = []
        for g in gems:
            bits = []
            if g.get("cut"): bits.append(f'切割 {_esc(g["cut"])}')
            if g.get("color"): bits.append(f'色 {_esc(g["color"])}')
            if g.get("count"): bits.append(f'{_esc(g["count"])}')
            if g.get("setting"): bits.append(f'镶嵌 {_esc(g["setting"])}')
            lis.append(f'<li><strong>{_esc(g.get("name", ""))}</strong> · {" · ".join(bits)}</li>')
        cards.append(f'<div class="detail-card"><div class="label">Gemstone</div><div class="body"><ul>{"".join(lis)}</ul></div></div>')

    craft = analysis.get("craftsmanship", [])
    if craft:
        lis = "\n".join(
            f'<li><strong>{_esc(c.get("technique", ""))}</strong> <em>({_esc(c.get("location", ""))})</em> — {_esc(c.get("description", ""))}</li>'
            for c in craft
        )
        cards.append(f'<div class="detail-card"><div class="label">Craft</div><div class="body"><ul>{lis}</ul></div></div>')

    audience = analysis.get("target_audience")
    if audience:
        cards.append(f'<div class="detail-card"><div class="label">Audience</div><div class="body">{_esc(audience)}</div></div>')

    scenes = analysis.get("scenes") or analysis.get("usage_scenes")
    if scenes:
        if isinstance(scenes, list):
            scenes_str = " · ".join(_esc(s) for s in scenes)
        else:
            scenes_str = _esc(scenes)
        cards.append(f'<div class="detail-card"><div class="label">Occasion</div><div class="body">{scenes_str}</div></div>')

    story = analysis.get("product_story") or analysis.get("story")
    if story:
        cards.append(f'<div class="detail-card"><div class="label">Story</div><div class="body">{_esc(story)}</div></div>')

    care = analysis.get("care_tips") or analysis.get("care") or analysis.get("maintenance")
    if care:
        if isinstance(care, list):
            lis = "\n".join(f"<li>{_esc(c)}</li>" for c in care)
            body = f"<ul>{lis}</ul>"
        else:
            body = _esc(care)
        cards.append(f'<div class="detail-card"><div class="label">Care</div><div class="body">{body}</div></div>')

    if not cards:
        return ""
    return f'''<section class="details">
  <div class="section-head">
    <span class="num">iii.</span>
    <span class="title">The Details</span>
    <span class="meta">产品 · 工艺 · 故事</span>
  </div>
  {"".join(cards)}
</section>'''


def _build_byline_chips(analysis: dict) -> str:
    """Byline avoids duplicating the h1 — h1 already shows subcategory + category."""
    chips = []
    brand = analysis.get("brand")
    if brand and brand not in ("未知", "Unknown", "unknown", ""):
        chips.append(_esc(brand))
    gems = analysis.get("gemstones") or []
    if gems:
        gem_name = gems[0].get("name", "").split("(")[0].strip()
        if gem_name:
            chips.append(_esc(gem_name))
    materials = analysis.get("materials") or []
    if materials:
        mat = materials[0].get("material", "")
        if mat:
            chips.append(_esc(mat))
    audience = analysis.get("target_audience", "")
    if audience:
        # Pull just the age range / type hint, not the full sentence
        m = re.search(r"(\d+\s*[-—~]\s*\d+\s*岁)", audience)
        if m:
            chips.append(_esc(m.group(1)))
    return "".join(f"<span>{c}</span>" for c in chips[:4])


def render(bundle_dir: pathlib.Path) -> str:
    analysis_path = bundle_dir / "analysis.json"
    if not analysis_path.exists():
        raise FileNotFoundError(f"analysis.json 不存在: {analysis_path}")
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    copy_path = bundle_dir / "copy.md"
    parsed_copy = {"product_md": "", "styles": []}
    if copy_path.exists():
        parsed_copy = parse_copy_md(copy_path.read_text(encoding="utf-8"))

    # Auto-route pipeline
    input_type = analysis.get("input_type", "finished_product")
    pipeline = "marketing" if input_type == "finished_product" else "design"
    if not (bundle_dir / pipeline).exists():
        # fallback
        for cand in ("marketing", "design"):
            if (bundle_dir / cand).exists():
                pipeline = cand
                break

    gallery_html, gallery_count, pipeline_label = _build_gallery(bundle_dir, pipeline)
    copy_section_html = _build_copy_section(parsed_copy)
    details_section_html = _build_details_section(analysis)

    now = dt.datetime.now()
    issue = now.strftime("%y%m%d")
    date_long = now.strftime("%B %Y").upper() if hasattr(now, "strftime") else ""

    category = analysis.get("category", "Jewelry")
    subcategory = analysis.get("subcategory", "")
    design_concept = analysis.get("design_concept", "")

    cover_title = _esc(subcategory or category)
    cover_sub = _esc(category if subcategory else "Jewelry · The Edit")

    pullquote_block = ""
    if design_concept:
        pullquote_block = f'''<section class="pullquote">
  <q>{_esc(design_concept)}</q>
  <cite>— Design Concept</cite>
</section>'''

    return HTML_TEMPLATE.format(
        title=cover_title,
        issue=issue,
        date_long=_esc(date_long),
        date_short=_esc(now.strftime("%Y.%m.%d")),
        masthead_brand="THE JEWELRY EDIT",
        kicker=_esc(pipeline_label.upper()),
        cover_title=cover_title,
        cover_sub=cover_sub,
        byline_chips=_build_byline_chips(analysis),
        pullquote_block=pullquote_block,
        gallery_count=gallery_count,
        pipeline_label=_esc(pipeline_label),
        gallery_items=gallery_html,
        copy_section=copy_section_html,
        details_section=details_section_html,
    )


def main():
    parser = argparse.ArgumentParser(description="珠宝 Vogue lookbook 渲染器")
    parser.add_argument("bundle_dir", help="jewelry_bundle/<ts>/ 目录路径")
    parser.add_argument("--open", action="store_true", help="生成后自动 macOS open")
    parser.add_argument("--output", default=None, help="输出 HTML 路径（默认 <bundle>/index.html）")
    args = parser.parse_args()

    bundle = pathlib.Path(args.bundle_dir).expanduser().resolve()
    if not bundle.is_dir():
        sys.stderr.write(f"[lookbook] 目录不存在: {bundle}\n")
        sys.exit(1)

    html_out = render(bundle)
    out_path = pathlib.Path(args.output).expanduser().resolve() if args.output else bundle / "index.html"
    out_path.write_text(html_out, encoding="utf-8")
    sys.stderr.write(f"[lookbook] HTML 已生成: {out_path}\n")
    print(out_path)

    if args.open and sys.platform == "darwin":
        subprocess.run(["open", str(out_path)], check=False)


if __name__ == "__main__":
    main()
