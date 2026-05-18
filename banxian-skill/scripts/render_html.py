#!/usr/bin/env python3
"""半仙卦签 HTML 渲染器 — 朱砂烫金宣纸调

读取 stdin JSON（含 py 占卜引擎输出 + LLM 半仙解读），输出 self-contained 单页 HTML 到 ./banxian_results/

输入 schema:
{
  "py_output": { ... 完整 liuyao/liuren/meihua 输出 ... },
  "question": "用户原始问题",
  "interpretation": {
    "opening": "玄学开场 1-2 句",
    "gua_description": "卦象描述 3-5 句",
    "specific_landing": "针对用户问题的具体落点 3-5 句",
    "advice": "行动建议 / 心态提醒",
    "closing": "收尾留白 1 句"
  }
}

用法:
  echo '<json>' | python3 render_html.py [--open] [--output DIR]
"""
import argparse
import datetime as dt
import html
import json
import os
import pathlib
import subprocess
import sys


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, viewport-fit=cover">
<title>半仙卦签 · {primary_keyword} · {lunar}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=ZCOOL+XiaoWei&family=Noto+Serif+SC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-deep: #0a0807;
  --paper: #e8dfc8;
  --paper-warm: #d9cea8;
  --paper-shadow: #b8a87f;
  --ink: #1a1410;
  --ink-soft: #3a2f24;
  --vermillion: #b73a2c;
  --vermillion-deep: #8c2618;
  --gold: #c9a05c;
  --gold-soft: #a8854a;
  --grey: #6b6358;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
  background: var(--bg-deep);
  background-image:
    radial-gradient(ellipse at 18% 22%, rgba(201, 160, 92, 0.06) 0%, transparent 55%),
    radial-gradient(ellipse at 82% 78%, rgba(183, 58, 44, 0.05) 0%, transparent 60%),
    radial-gradient(ellipse at 50% 50%, rgba(20, 16, 14, 0) 0%, rgba(0, 0, 0, 0.55) 100%);
  min-height: 100vh;
  font-family: 'Noto Serif SC', 'Songti SC', 'STSong', serif;
  color: var(--ink);
  overflow-x: hidden;
}}

body::before {{
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.79  0 0 0 0 0.63  0 0 0 0 0.36  0 0 0 0.08 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  opacity: 0.18;
  pointer-events: none;
  mix-blend-mode: screen;
  z-index: 0;
}}

.candle-glow {{
  position: fixed;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(201, 160, 92, 0.12) 0%, transparent 70%);
  filter: blur(40px);
  pointer-events: none;
  z-index: 1;
  animation: candle-flicker 7s ease-in-out infinite;
}}

.candle-glow.tl {{ top: -200px; left: -150px; }}
.candle-glow.br {{ bottom: -200px; right: -150px; animation-delay: -3.5s; }}

@keyframes candle-flicker {{
  0%, 100% {{ opacity: 0.55; transform: scale(1) translate(0, 0); }}
  33% {{ opacity: 0.75; transform: scale(1.08) translate(8px, -12px); }}
  66% {{ opacity: 0.45; transform: scale(0.95) translate(-10px, 6px); }}
}}

main {{
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: center;
  padding: 64px 24px;
}}

.scroll {{
  width: 100%;
  max-width: 720px;
  background: var(--paper);
  background-image:
    radial-gradient(ellipse at 12% 8%, rgba(120, 90, 50, 0.18) 0%, transparent 30%),
    radial-gradient(ellipse at 88% 92%, rgba(120, 90, 50, 0.15) 0%, transparent 35%),
    linear-gradient(135deg, rgba(216, 200, 160, 0.5) 0%, rgba(232, 223, 200, 0) 40%, rgba(232, 223, 200, 0) 60%, rgba(184, 168, 127, 0.4) 100%);
  padding: 56px 56px 48px;
  position: relative;
  box-shadow:
    0 1px 0 rgba(255, 250, 230, 0.4) inset,
    0 -1px 0 rgba(120, 90, 50, 0.25) inset,
    0 30px 80px rgba(0, 0, 0, 0.55),
    0 0 0 1px rgba(201, 160, 92, 0.25);
  animation: scroll-unfurl 1100ms cubic-bezier(0.22, 1, 0.36, 1) both;
  transform-origin: top center;
}}

.scroll::before, .scroll::after {{
  content: '';
  position: absolute;
  left: -14px;
  right: -14px;
  height: 26px;
  background:
    radial-gradient(ellipse 100% 70% at 50% 35%, #e0c587 0%, #c9a05c 38%, #8a6d3a 92%, #5a4622 100%);
  border-radius: 18px / 50%;
  box-shadow:
    0 6px 18px rgba(0, 0, 0, 0.55),
    inset 0 1px 1px rgba(255, 240, 200, 0.45),
    inset 0 -2px 4px rgba(20, 12, 0, 0.4),
    inset 8px 0 6px -6px rgba(255, 240, 200, 0.35),
    inset -8px 0 6px -6px rgba(40, 24, 0, 0.5);
}}
.scroll::before {{ top: -14px; }}
.scroll::after {{ bottom: -14px; }}

/* End caps (knobs) on the rod */
.rod-cap {{
  position: absolute;
  width: 22px;
  height: 34px;
  background: radial-gradient(ellipse 80% 70% at 50% 30%, #d8b970, #8a6d3a 70%, #4a3818 100%);
  border-radius: 50%;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 240, 200, 0.4);
  z-index: 2;
}}
.rod-cap.tl {{ top: -20px; left: -24px; }}
.rod-cap.tr {{ top: -20px; right: -24px; }}
.rod-cap.bl {{ bottom: -20px; left: -24px; }}
.rod-cap.br {{ bottom: -20px; right: -24px; }}

@keyframes scroll-unfurl {{
  from {{ opacity: 0; transform: translateY(-30px) scaleY(0.85); }}
  to {{ opacity: 1; transform: translateY(0) scaleY(1); }}
}}

.scroll-edge {{
  position: absolute;
  top: 56px;
  bottom: 48px;
  width: 1px;
  background: linear-gradient(180deg, transparent, var(--gold) 12%, var(--gold) 88%, transparent);
}}
.scroll-edge.left {{ left: 28px; }}
.scroll-edge.right {{ right: 28px; }}

/* Header */
.header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(140, 38, 24, 0.35);
  padding-bottom: 16px;
  margin-bottom: 32px;
  position: relative;
}}

.brand {{
  font-family: 'Ma Shan Zheng', 'Noto Serif SC', serif;
  font-size: 22px;
  color: var(--vermillion-deep);
  letter-spacing: 0.18em;
}}

.brand-mark {{
  display: inline-block;
  width: 22px;
  height: 22px;
  vertical-align: -4px;
  margin-right: 10px;
}}

.meta {{
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 13px;
  color: var(--ink-soft);
  letter-spacing: 0.12em;
  text-align: right;
}}
.meta .lunar {{ display: block; }}
.meta .shichen {{ display: block; color: var(--vermillion-deep); margin-top: 2px; font-weight: 500; }}

/* Question quote */
.question {{
  font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
  font-size: 17px;
  color: var(--grey);
  line-height: 1.85;
  margin: 0 0 18px;
  padding-left: 18px;
  border-left: 2px solid var(--gold);
  position: relative;
  opacity: 0;
  animation: fade-in 800ms ease 200ms forwards;
}}
.question::before {{
  content: '所问';
  position: absolute;
  top: -14px;
  left: -2px;
  font-size: 11px;
  letter-spacing: 0.4em;
  color: var(--vermillion-deep);
  background: var(--paper);
  padding: 0 6px;
}}

/* Method tag */
.method-tag {{
  display: inline-block;
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 14px;
  letter-spacing: 0.5em;
  color: var(--vermillion-deep);
  margin-bottom: 16px;
  padding: 4px 14px 4px 20px;
  border: 1px solid var(--vermillion-deep);
  opacity: 0;
  animation: fade-in 800ms ease 400ms forwards;
}}

/* Primary keyword (giant hexagram name) */
.primary {{
  font-family: 'Ma Shan Zheng', 'Noto Serif SC', serif;
  font-size: clamp(64px, 12vw, 108px);
  line-height: 1;
  color: var(--ink);
  margin: 18px 0 8px;
  letter-spacing: 0.05em;
  text-shadow:
    0 0 1px rgba(26, 20, 16, 0.5),
    1px 1px 0 rgba(60, 40, 24, 0.18);
  opacity: 0;
  animation: ink-bleed 1100ms ease 600ms forwards;
}}

@keyframes ink-bleed {{
  from {{ opacity: 0; filter: blur(8px); letter-spacing: 0.4em; }}
  to {{ opacity: 1; filter: blur(0); letter-spacing: 0.05em; }}
}}

.primary .arrow {{
  font-size: 0.55em;
  color: var(--vermillion-deep);
  vertical-align: 0.15em;
  margin: 0 0.15em;
  font-family: 'Noto Serif SC', serif;
}}

.subinfo {{
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 13px;
  letter-spacing: 0.18em;
  color: var(--ink-soft);
  margin-bottom: 40px;
  opacity: 0;
  animation: fade-in 800ms ease 1000ms forwards;
}}
.subinfo .sep {{ color: var(--gold-soft); margin: 0 10px; font-style: normal; }}

/* ASCII chart */
.ascii {{
  font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
  font-size: 13.5px;
  line-height: 1.7;
  white-space: pre;
  background: rgba(26, 20, 16, 0.04);
  border-left: 3px solid var(--vermillion);
  padding: 30px 24px 22px;
  margin: 8px 0 32px;
  color: var(--ink);
  letter-spacing: -0.02em;
  overflow-x: auto;
  position: relative;
  opacity: 0;
  animation: fade-in 1000ms ease 1200ms forwards;
}}
.ascii::before {{
  content: '卦象';
  position: absolute;
  top: -10px;
  left: 14px;
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 11px;
  letter-spacing: 0.4em;
  color: var(--vermillion-deep);
  background: var(--paper);
  padding: 0 8px;
}}

/* Hexagram glyph (Unicode trigram) */
.glyph-row {{
  display: flex;
  gap: 28px;
  justify-content: center;
  margin: 0 0 24px;
  opacity: 0;
  animation: fade-in 800ms ease 1400ms forwards;
}}
.glyph {{
  text-align: center;
  font-family: 'Noto Serif SC', serif;
}}
.glyph .symbol {{
  font-size: 48px;
  line-height: 1;
  color: var(--ink);
  display: block;
  margin-bottom: 4px;
}}
.glyph .label {{
  font-size: 11px;
  letter-spacing: 0.3em;
  color: var(--grey);
}}

/* Classic verse */
.verse {{
  font-family: 'Ma Shan Zheng', 'Noto Serif SC', serif;
  font-size: 24px;
  color: var(--vermillion-deep);
  text-align: center;
  margin: 28px 0;
  padding: 16px 0;
  border-top: 1px solid rgba(140, 38, 24, 0.25);
  border-bottom: 1px solid rgba(140, 38, 24, 0.25);
  letter-spacing: 0.18em;
  line-height: 1.6;
  opacity: 0;
  animation: fade-in 1000ms ease 1600ms forwards;
}}

/* Interpretation sections */
.interp {{
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: 16px;
  line-height: 2;
  color: var(--ink-soft);
  margin-bottom: 28px;
}}
.interp .section {{
  margin-bottom: 26px;
  opacity: 0;
  transform: translateY(8px);
  animation: section-reveal 800ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}
.interp .section:nth-child(1) {{ animation-delay: 1700ms; }}
.interp .section:nth-child(2) {{ animation-delay: 1900ms; }}
.interp .section:nth-child(3) {{ animation-delay: 2100ms; }}
.interp .section:nth-child(4) {{ animation-delay: 2300ms; }}
.interp .section:nth-child(5) {{ animation-delay: 2500ms; }}
.interp .section + .section {{
  border-top: 1px dashed rgba(140, 38, 24, 0.18);
  padding-top: 22px;
}}
@keyframes section-reveal {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.interp .section-label {{
  display: inline-block;
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 12px;
  letter-spacing: 0.4em;
  color: var(--vermillion-deep);
  margin-bottom: 8px;
  padding: 2px 8px;
  background: rgba(183, 58, 44, 0.08);
}}
.interp p {{
  text-indent: 2em;
  margin-bottom: 8px;
}}
.interp p:last-child {{ margin-bottom: 0; }}
.interp strong {{
  color: var(--ink);
  font-weight: 700;
  background: linear-gradient(180deg, transparent 65%, rgba(201, 160, 92, 0.35) 65%);
  padding: 0 2px;
}}

/* Stamp (chop) */
.stamp-area {{
  display: flex;
  justify-content: flex-end;
  margin: 36px 0 12px;
  position: relative;
  min-height: 80px;
}}
.stamp {{
  position: relative;
  width: 84px;
  height: 84px;
  background: var(--vermillion);
  color: var(--paper);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Ma Shan Zheng', serif;
  font-size: 19px;
  line-height: 1.1;
  letter-spacing: 0;
  border-radius: 1px;
  box-shadow:
    inset 0 0 0 3px var(--paper),
    inset 0 0 0 4px var(--vermillion-deep);
  transform: rotate(-6deg) scale(0);
  opacity: 0;
  overflow: hidden;
  animation: stamp-drop 600ms cubic-bezier(0.22, 1.6, 0.42, 1) 2200ms forwards;
}}
.stamp::before {{
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='1.4' numOctaves='2'/><feColorMatrix values='0 0 0 0 0.91  0 0 0 0 0.87  0 0 0 0 0.78  0 0 0 0.6 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  mix-blend-mode: screen;
  opacity: 0.55;
  pointer-events: none;
}}
.stamp .top, .stamp .bottom {{ position: relative; z-index: 1; }}
.stamp .top {{ font-size: 16px; }}
.stamp .bottom {{ font-size: 22px; margin-top: 2px; }}

@keyframes stamp-drop {{
  0% {{ transform: rotate(18deg) scale(2.2) translateY(-80px); opacity: 0; }}
  60% {{ transform: rotate(-10deg) scale(1.06) translateY(0); opacity: 1; }}
  80% {{ transform: rotate(-4deg) scale(0.97); }}
  100% {{ transform: rotate(-6deg) scale(1); opacity: 0.96; }}
}}

/* Closing */
.closing {{
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(140, 38, 24, 0.2);
  font-family: 'ZCOOL XiaoWei', serif;
  font-size: 15px;
  letter-spacing: 0.35em;
  color: var(--grey);
  opacity: 0;
  animation: fade-in 1000ms ease 2600ms forwards;
}}
.closing .yinyang {{ color: var(--vermillion-deep); margin: 0 12px; font-size: 18px; vertical-align: -2px; }}

/* Footer note */
.footnote {{
  margin-top: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.15em;
  color: var(--paper-shadow);
  text-align: center;
  opacity: 0;
  animation: fade-in 1000ms ease 2800ms forwards;
}}

@keyframes fade-in {{
  from {{ opacity: 0; transform: translateY(4px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Bagua spinner */
.bagua {{
  position: absolute;
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  opacity: 0.5;
}}
.bagua circle {{
  fill: none;
  stroke: var(--ink);
  stroke-width: 1;
}}

/* Mobile */
@media (max-width: 640px) {{
  main {{ padding: 32px 14px; }}
  .scroll {{ padding: 40px 28px 36px; }}
  .scroll::before, .scroll::after {{ left: -4px; right: -4px; }}
  .ascii {{ font-size: 11.5px; padding: 18px 16px; }}
  .glyph .symbol {{ font-size: 38px; }}
  .verse {{ font-size: 19px; }}
  .interp {{ font-size: 15px; line-height: 1.95; }}
  .stamp {{ width: 72px; height: 72px; font-size: 17px; }}
  .stamp .bottom {{ font-size: 18px; }}
}}

@media print {{
  body {{ background: white; }}
  .candle-glow {{ display: none; }}
  body::before {{ display: none; }}
  .scroll {{ box-shadow: none; }}
}}
</style>
</head>
<body>
  <div class="candle-glow tl"></div>
  <div class="candle-glow br"></div>

  <main>
    <article class="scroll">
      <span class="rod-cap tl"></span>
      <span class="rod-cap tr"></span>
      <span class="rod-cap bl"></span>
      <span class="rod-cap br"></span>
      <span class="scroll-edge left"></span>
      <span class="scroll-edge right"></span>

      <header class="header">
        <div class="brand">
          <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="11" fill="none" stroke="#8c2618" stroke-width="1.2"/>
            <path d="M 12 1 A 5.5 5.5 0 0 1 12 12 A 5.5 5.5 0 0 0 12 23" fill="#8c2618" stroke="none"/>
            <circle cx="12" cy="6.5" r="1.3" fill="#e8dfc8"/>
            <circle cx="12" cy="17.5" r="1.3" fill="#8c2618"/>
          </svg>
          半仙卦签
        </div>
        <div class="meta">
          <span class="lunar">{lunar}</span>
          <span class="shichen">{shichen}</span>
        </div>
      </header>

      {question_block}

      <div class="method-tag">{method_label}</div>

      <h1 class="primary">{primary_display}</h1>

      <div class="subinfo">{subinfo}</div>

      {glyph_block}

      <pre class="ascii">{ascii_chart}</pre>

      {verse_block}

      <section class="interp">
        {interp_blocks}
      </section>

      <div class="stamp-area">
        <div class="stamp" title="半仙之印">
          <span class="top">半仙</span>
          <span class="bottom">之印</span>
        </div>
      </div>

      <div class="closing">
        <span class="yinyang">☯</span>天机已泄三分　余下七分由施主自悟<span class="yinyang">☯</span>
      </div>

      <div class="footnote">
        {footnote}
      </div>
    </article>
  </main>

</body>
</html>
"""


METHOD_LABELS = {
    "liuyao": "六　爻",
    "liuren": "小六壬",
    "meihua": "梅花易数",
}

# Unicode trigrams
TRIGRAM_GLYPHS = {
    "乾": "☰", "兑": "☱", "离": "☲", "震": "☳",
    "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷",
}


def build_subinfo(py_out: dict) -> str:
    """根据 method 组装副信息行（卦宫/五行/时辰等）"""
    method = py_out["method"]
    timing = py_out.get("timing", {})
    structured = py_out["result"].get("structured", {})
    shichen = timing.get("shichen", "")
    parts = []

    if method == "liuyao":
        detail = structured.get("benDetail", {})
        palace = detail.get("palace")
        wuxing = detail.get("palaceWuXing")
        if palace:
            parts.append(palace)
        if wuxing:
            parts.append(f"五行属{wuxing}")
        parts.append(shichen)
    elif method == "liuren":
        main = structured.get("mainResult", {})
        wuxing = main.get("element")
        alias = main.get("alias")
        if alias:
            parts.append(f"别名「{alias}」")
        if wuxing:
            parts.append(f"五行属{wuxing}")
        parts.append(shichen)
    elif method == "meihua":
        upper = structured.get("upperGua")
        lower = structured.get("lowerGua")
        dong = structured.get("dongYao")
        if upper and lower:
            parts.append(f"上{upper}下{lower}")
        if dong:
            parts.append(f"动在第{dong}爻")
        parts.append(shichen)

    return '<span class="sep">·</span>'.join(html.escape(p) for p in parts if p)


def build_glyph_block(py_out: dict) -> str:
    """梅花和六爻显示本卦/之卦的八卦符号"""
    method = py_out["method"]
    structured = py_out["result"].get("structured", {})

    if method == "meihua":
        upper = structured.get("upperGua", "")
        lower = structured.get("lowerGua", "")
        ben = structured.get("benGua", "")
        bian = structured.get("bianGua", "")
        u_sym = TRIGRAM_GLYPHS.get(upper, "")
        l_sym = TRIGRAM_GLYPHS.get(lower, "")
        if u_sym and l_sym:
            return f"""<div class="glyph-row">
              <div class="glyph"><span class="symbol">{u_sym}</span><span class="label">上 · {html.escape(upper)}</span></div>
              <div class="glyph"><span class="symbol">{l_sym}</span><span class="label">下 · {html.escape(lower)}</span></div>
              <div class="glyph"><span class="symbol" style="font-family:'Ma Shan Zheng',serif;font-size:38px">{html.escape(ben)}</span><span class="label">本 卦</span></div>
              <div class="glyph"><span class="symbol" style="font-family:'Ma Shan Zheng',serif;font-size:38px">{html.escape(bian)}</span><span class="label">之 卦</span></div>
            </div>"""

    if method == "liuyao":
        ben_detail = structured.get("benDetail", {})
        upper = ben_detail.get("upperGua", "")
        lower = ben_detail.get("lowerGua", "")
        u_sym = TRIGRAM_GLYPHS.get(upper, "")
        l_sym = TRIGRAM_GLYPHS.get(lower, "")
        if u_sym and l_sym:
            return f"""<div class="glyph-row">
              <div class="glyph"><span class="symbol">{u_sym}</span><span class="label">上 · {html.escape(upper)}</span></div>
              <div class="glyph"><span class="symbol">{l_sym}</span><span class="label">下 · {html.escape(lower)}</span></div>
            </div>"""

    return ""


def build_verse_block(py_out: dict) -> str:
    """卦辞 / 经典诗韵"""
    method = py_out["method"]
    structured = py_out["result"].get("structured", {})

    verse = ""
    if method == "liuyao":
        verse = structured.get("benDetail", {}).get("guaCi", "")
    elif method == "liuren":
        full_verse = structured.get("mainResult", {}).get("classicVerse", "")
        verse = full_verse.split("\n")[0] if full_verse else ""
    elif method == "meihua":
        verse = structured.get("benDetail", {}).get("guaCi", "")

    if not verse:
        return ""
    return f'<div class="verse">「{html.escape(verse).strip("，。；")}」</div>'


def build_primary_display(py_out: dict) -> str:
    method = py_out["method"]
    primary = py_out["result"]["primary_keyword"]
    structured = py_out["result"].get("structured", {})

    if method == "liuyao":
        bian = structured.get("bianGua")
        if bian and bian != primary:
            return f'{html.escape(primary)}<span class="arrow">→</span>{html.escape(bian)}'
    elif method == "meihua":
        bian = structured.get("bianGua")
        if bian and bian != primary:
            return f'{html.escape(primary)}<span class="arrow">→</span>{html.escape(bian)}'

    return html.escape(primary)


def build_question_block(question: str) -> str:
    if not question or not question.strip():
        return ""
    return f'<blockquote class="question">{html.escape(question.strip())}</blockquote>'


import re

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_QUOTE_RE = re.compile(r"「(.+?)」")


def _md_inline(text: str) -> str:
    """Escape then re-enable a tiny subset: **bold** + 「quote」 emphasis."""
    escaped = html.escape(text)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _QUOTE_RE.sub(r'<em style="font-style:normal;color:var(--vermillion-deep);font-weight:500">「\1」</em>', escaped)
    return escaped


def build_interp_blocks(interp: dict) -> str:
    """把 5 段解读渲染成带标签的 section"""
    order = [
        ("opening", "开　卦"),
        ("gua_description", "卦象之意"),
        ("specific_landing", "落于此事"),
        ("advice", "贫道之言"),
        ("closing", "余　言"),
    ]
    blocks = []
    for key, label in order:
        body = interp.get(key, "").strip()
        if not body:
            continue
        paragraphs = "".join(
            f"<p>{_md_inline(line.strip())}</p>"
            for line in body.split("\n")
            if line.strip()
        )
        blocks.append(
            f'<div class="section"><span class="section-label">{label}</span>{paragraphs}</div>'
        )
    return "\n".join(blocks)


def render(payload: dict) -> str:
    py_out = payload["py_output"]
    question = payload.get("question", "")
    interp = payload.get("interpretation", {})

    method = py_out["method"]
    timing = py_out.get("timing", {})
    result = py_out["result"]

    return HTML_TEMPLATE.format(
        primary_keyword=html.escape(result["primary_keyword"]),
        lunar=html.escape(timing.get("lunar", "")),
        shichen=html.escape(timing.get("shichen", "")),
        method_label=METHOD_LABELS.get(method, method),
        question_block=build_question_block(question),
        primary_display=build_primary_display(py_out),
        subinfo=build_subinfo(py_out),
        glyph_block=build_glyph_block(py_out),
        ascii_chart=html.escape(result.get("ascii_chart", "")),
        verse_block=build_verse_block(py_out),
        interp_blocks=build_interp_blocks(interp),
        footnote=html.escape(f"banxian-skill · 算法引擎 panpanmao.com · 生成于 {timing.get('datetime_iso', '')}"),
    )


def main():
    parser = argparse.ArgumentParser(description="半仙卦签 HTML 渲染器")
    parser.add_argument("--output", default="./banxian_results",
                        help="输出目录（默认 ./banxian_results）")
    parser.add_argument("--open", action="store_true",
                        help="生成后自动在浏览器打开（macOS `open`）")
    parser.add_argument("--stdout", action="store_true",
                        help="HTML 输出到 stdout 而非文件")
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        sys.stderr.write("[render_html] stdin 为空,需要 JSON 输入\n")
        sys.exit(1)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[render_html] JSON 解析失败: {e}\n")
        sys.exit(1)

    html_out = render(payload)

    if args.stdout:
        sys.stdout.write(html_out)
        return

    out_dir = pathlib.Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    method = payload["py_output"]["method"]
    primary = payload["py_output"]["result"]["primary_keyword"]
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"{ts}_{method}_{primary}.html"
    out_path.write_text(html_out, encoding="utf-8")

    sys.stderr.write(f"[render_html] 卦签已生成: {out_path}\n")
    print(out_path)

    if args.open and sys.platform == "darwin":
        subprocess.run(["open", str(out_path)], check=False)


if __name__ == "__main__":
    main()
