---
name: jewelry-marketing
description: Use when a jewelry / 珠宝 / 文玩 / 翡翠 / 钻石 / 黄金 / 珍珠 e-commerce merchant needs marketing material from one product photo — produces a full XHS-ready bundle (12 marketing images + 6 copywriting styles + product analysis JSON) for finished pieces, or a design suite (8 images: hand-drawn sketch + 3D render + lifestyle + CAD sheet + ...) when the input is a raw gemstone / 原石 / 散石. Auto-detects finished-product vs raw-material. Trigger phrases: 珠宝营销素材, 生成珠宝商品图, 珠宝小红书素材, 珠宝海报, 上手图, 一饰多搭, 钻石/翡翠/珍珠/玉/古法金/月光石 marketing bundle, jewelry design from raw stone, 原石设计图, 散石变成品.
---

# /jewelry-marketing — 珠宝电商一键营销素材生成器

One photo in → full Xiaohongshu-ready marketing bundle out. Distilled from the shichuan (识川) production system, narrowed and tuned for jewelry merchants specifically.

## Two pipelines, auto-routed

| Input | Pipeline | Output |
|---|---|---|
| 成品珠宝照（项链/戒指/耳环/手镯/吊坠/胸针）| **marketing** | 12 张 XHS 营销图 + 6 风格文案 + 分析 JSON |
| 原石/散石/裸石照 | **design** | 8 张设计图（手绘稿 / 3D 渲染 / 佩戴效果 / CAD 技术图...）|

Routing happens automatically from the analysis (`input_type=finished_product` vs `raw_material`). User doesn't pick.

## Invocation

```bash
~/.claude/skills/jewelry-marketing/generate.py PRODUCT_IMAGE.jpg [options]
```

PEP 723 uv script — no venv setup, `uv` handles deps on first run.

### Options

- `--output DIR` — output directory (default `./jewelry_bundle/<timestamp>`)
- `--mode auto|marketing|design` — override auto-routing (default `auto`)
- `--templates A,B,C` — generate only these templates (default = full bundle)
- `--jewelry-type ring|pendant|earring|brooch` — design mode subject (default: inferred from analysis)
- `--copy-only` — skip image gen, write only `analysis.json` + `copy.md`
- `--analyze-only` — skip everything, just write `analysis.json`
- `--seller-description TEXT` — extra context to inject into analysis (e.g., "天然 GIA 钻 1ct")
- `--concurrency N` — parallel image gens (default 4 — bump higher if your OpenAI tier allows)

### Marketing template IDs (12)

`hero` `wristNeck` `gemCutDetail` `sceneStyleWear` `flatLayEditorial` `moodboard` `wearStyleGrid` `giftScene` `priceAnchor` `meaningCraftPoster` `knowhowAvoid` `starTestimonial`

### Design template IDs (8)

`sketch` (canonical, others reference it) `sketchMulti` `rendering3d` `wearing` `materialBreak` `moodboard` `colorDna` `cad3d`

### Examples

```bash
# Full marketing bundle — finished jewelry product
~/.claude/skills/jewelry-marketing/generate.py ./pearl_necklace.jpg
# → ./jewelry_bundle/<ts>/{analysis.json, copy.md, marketing/01_hero.jpg, ..., marketing/12_starTestimonial.jpg}

# Design suite from a raw stone
~/.claude/skills/jewelry-marketing/generate.py ./loose_stone.jpg --jewelry-type ring
# → ./jewelry_bundle/<ts>/{analysis.json, design/01_sketch.jpg, ..., design/08_cad3d.jpg}

# Just a few templates
~/.claude/skills/jewelry-marketing/generate.py ./ring.jpg --templates hero,wristNeck,priceAnchor

# Copy + analysis only (no image gen — fast/free)
~/.claude/skills/jewelry-marketing/generate.py ./ring.jpg --copy-only
```

## What's in the output bundle

```
jewelry_bundle/<timestamp>/
├── analysis.json          # Product analysis (gemstones, materials, colors, design concept, target audience, scenes, ...)
├── copy.md                # 6 XHS copy styles: 闺蜜种草 / 专业测评 / 情绪叙事 / 穿搭攻略 / 文化叙事 / 送礼仪式感
│                          # Each style: 5 hooks (titles), 5 selling points, full post (300-500字), 5 tags
├── marketing/             # finished_product pipeline
│   ├── 01_hero.jpg                    # 棚拍主图
│   ├── 02_wristNeck.jpg               # 上手图/锁骨图（爆款封面）
│   ├── 03_gemCutDetail.jpg            # 宝石工艺微距
│   ├── 04_sceneStyleWear.jpg          # 场景化佩戴
│   ├── 05_flatLayEditorial.jpg        # 单品平铺特写
│   ├── 06_moodboard.jpg               # 品牌情绪板
│   ├── 07_wearStyleGrid.jpg           # 一饰多搭四宫格
│   ├── 08_giftScene.jpg               # 送礼场景海报
│   ├── 09_priceAnchor.jpg             # 价格锚点合集
│   ├── 10_meaningCraftPoster.jpg      # 寓意工艺大字报
│   ├── 11_knowhowAvoid.jpg            # 选购避坑指南
│   └── 12_starTestimonial.jpg         # 明星同款/玄学种草
└── design/                # raw_material pipeline (alternative to marketing/)
    ├── 01_sketch.jpg                  # 水彩+铅笔手绘稿（canonical, 其他基于此）
    ├── 02_sketchMulti.jpg             # 6视图工程蓝图
    ├── 03_rendering3d.jpg             # 3D 渲染（KeyShot 级）
    ├── 04_wearing.jpg                 # 佩戴效果
    ├── 05_materialBreak.jpg           # 材质拆解（成品+裸石+金属）
    ├── 06_moodboard.jpg               # 灵感拼贴
    ├── 07_colorDna.jpg                # 水彩色卡
    └── 08_cad3d.jpg                   # CAD 技术图（5视图+宝石数量表+尺寸标注）
```

## Credentials (only 2 keys needed)

| Var | Purpose |
|---|---|
| `GEMINI_API_KEY` | Product analysis — Gemini Flash 3, free tier OK |
| `OPENAI_API_KEY` | Image generation — `gpt-image-2` via OpenAI direct |

Both can sit in env vars or `~/.config/gpt-image/credentials` (auto-loaded). Image generation calls `gpt-image-2` directly through OpenAI's `/v1/images/{generations,edits}` endpoint — best for photorealistic + on-image text rendering (price tags, Chinese headlines, mass-market XHS feel).

## Why this skill (vs writing your own prompts)

The 12 marketing prompts are research-backed (千瓜 2024 / 数英 / fxbaogao / 我是产品经理 case studies on 周大福 / HEFANG / 樱桃 / 阑珊珠宝 / 翡翠平安环 / 莫桑钻 / akoya / 古法金 etc.) — each prompt encodes:

- Material-aware lighting (diamond high-contrast, pearl single-soft, jade even-translucency, gold warm-3000K)
- Stone-aware scene routing (古法金→新中式, 钻石→晚宴, 珍珠→咖啡馆白墙)
- Wear-zone detection (项链→颈部锁骨, 戒指→手部, 耳环→侧脸)
- Subcategory-aware copy headlines (翡翠 vs 钻石 vs 珍珠 use different price anchors / gift contexts / avoid-pitfall topics)
- Reference-image dominance handling (moodboards omit ref to avoid product-anchoring)
- Merchant-fillable slots (prices stay as `¥___`, no fabricated numbers)

Don't re-derive this. Use the skill.

## Reference docs

- `references/JEWELRY_TEMPLATES.md` — what each of the 20 templates looks like, when to use, sample output description
- `references/COPY_STYLES.md` — the 6 XHS copywriting styles with tone rules and word lists
- `references/OUTPUT_BUNDLE.md` — bundle directory structure + JSON schema

## When NOT to use this skill

- Non-jewelry products (服饰 / 美妆 / 食品) — use generic image-gen + copy tools
- Bulk / batch processing dozens of products at once — wrap this skill in a loop and respect your OpenAI tier's RPM limit
- Brand-locked aesthetics — this skill targets generic XHS-style; if you need Tiffany / Bulgari brand-exact, hand-author prompts
