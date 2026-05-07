# Output Bundle Format

Every successful run produces a bundle in `<output>/<timestamp>/`:

```
jewelry_bundle/20260506-082000/
├── analysis.json      # ProductAnalysis JSON (see schema below)
├── copy.md            # 6-style copywriting bundle, formatted as markdown
├── summary.json       # Run metadata: pipeline, success/fail counts, paths
├── marketing/         # OR design/ — picked by analysis.input_type
│   ├── 01_hero.jpg
│   ├── 02_wristNeck.jpg
│   └── ...
```

## analysis.json schema

```jsonc
{
  "input_type": "finished_product | raw_material",
  "material_type": "gemstone | raw_stone | other | null",
  "input_type_confidence": "high | medium | low",
  "category": "项链 | 戒指 | 耳环 | ...",
  "subcategory": "钻石项链 | 翡翠手镯 | 古法金戒指 | ...",
  "domain": "珠宝首饰",
  "brand": "周大福 | HEFANG | 未知 | ...",
  "design_concept": "2句话的设计概念",

  "materials": [
    { "part": "链身", "material": "18K白金", "detail": "Au750 含金 75%", "confidence": "high" }
  ],
  "gemstones": [
    {
      "name": "钻石(Diamond)",
      "cut": "圆形明亮式 Round Brilliant",
      "color": "G色",
      "count": "1颗主石",
      "setting": "爪镶 Prong",
      "special_effect": "无"
    }
  ],
  "craftsmanship": [
    { "technique": "古法錾刻", "location": "戒臂", "description": "手工花卉纹样" }
  ],
  "structure": [...],
  "colors": [
    { "name": "玫瑰金", "hex": "#B76E79", "area": "金属主色" }
  ],
  "care_tips": ["...", "..."],
  "guide_steps": ["...", "...", "...", "..."],
  "size_estimate": "戒指内径17mm，主石直径6mm",
  "target_audience": "25-35岁都市女性，追求轻奢...",
  "suggested_scenes": ["日常通勤", "约会晚宴", "节日送礼"],
  "product_story": "2-3句产品故事",

  "copy_bundles": [
    {
      "style": "闺蜜种草",
      "hooks": ["...", "...", "...", "...", "..."],
      "selling_points": ["...", "...", "...", "...", "..."],
      "post": "完整正文 300-500字",
      "tags": ["...", "...", "...", "...", "..."]
    },
    // 5 more bundles: 专业测评, 情绪叙事, 穿搭攻略, 文化叙事, 送礼仪式感
  ]
}
```

## summary.json schema

```jsonc
{
  "input_image": "/abs/path/to/input.jpg",
  "input_type": "finished_product",
  "category": "项链",
  "subcategory": "钻石项链",
  "pipeline": "marketing",
  "results": {
    "success": [
      { "template": "hero", "path": "/.../marketing/01_hero.jpg" }
    ],
    "failed": [
      { "template": "wristNeck", "error": "openai 429 rate limited" }
    ],
    "elapsed_seconds": 187.3
  },
  "generated_at": "2026-05-06T08:20:00.123456"
}
```

## How merchants use the bundle

| File | Usage |
|---|---|
| `marketing/01_hero.jpg` | 上传到淘宝/小红书商品详情页主图位 |
| `marketing/02_wristNeck.jpg` | XHS 笔记 cover 图（爆款封面）|
| `marketing/07_wearStyleGrid.jpg` | XHS 收藏率高的 cover（"4 种穿法"）|
| `marketing/08_giftScene.jpg` | 节日营销时段使用（七夕、母亲节）|
| `marketing/09_priceAnchor.jpg` | 大促/直播专用 cover |
| `copy.md` | 复制 6 篇正文 + 标题去 XHS / 抖音 / 微博 一键发布 |
| `analysis.json` | 详情页文字内容、产品参数表、SEO 关键词 |
| `design/01_sketch.jpg` | 给原石买家看"设计提案"（设计师级手绘）|
| `design/08_cad3d.jpg` | 给打版师傅看技术图（含尺寸+宝石数量表）|

## Re-run / partial regeneration

If a few templates failed (rate limit / network), just re-run with `--templates`:

```bash
generate.py jewelry.jpg --output ./jewelry_bundle/20260506-082000 \
  --templates wristNeck,priceAnchor
```

The same output dir gets the missing files patched in. analysis.json + copy.md
won't be regenerated unless you delete them first.

## Cost estimate

Per full marketing bundle (12 images):
- Analysis: ~$0.005 (Gemini Flash 3, < 5K tokens)
- Image gen: 12 × ~$0.04 (gpt-image-2 medium) = ~$0.48
- Total: ~$0.48 / bundle

Per full design bundle (8 images):
- Analysis: ~$0.005
- Image gen: 8 × ~$0.04 = ~$0.32
- Total: ~$0.33 / bundle

Wall time:
- Marketing (concurrency=4): ~3-5 min
- Design (concurrency=4 for phase 2 only): ~5-7 min (sketch is sequential first)
