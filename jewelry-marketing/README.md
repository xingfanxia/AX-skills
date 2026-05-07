# jewelry-marketing

> 一张商品照片输入 → 完整 XHS 营销 bundle 输出（12 张营销图 + 6 风格文案 + 商品分析 JSON）。
> 专为珠宝电商商家打造，覆盖钻石/翡翠/珍珠/古法金/月光石/坦桑石等品类。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple)](https://docs.claude.com/en/docs/claude-code)

## 它做什么

把一张珠宝照片喂给它，它自动判断这是「成品」还是「散石」，然后跑对应 pipeline：

```
成品照（项链/戒指/耳环/手镯/吊坠/胸针）
  → marketing pipeline
    → 12 张 XHS 营销图（棚拍/上手/微距/场景/海报）
    + 6 风格文案（闺蜜种草/专业测评/情绪叙事/穿搭攻略/文化叙事/送礼仪式感）
    + analysis.json（材质/宝石/工艺/色彩/目标人群/场景）
```

```
散石/原石照
  → design pipeline
    → 8 张设计图（手绘稿/工程蓝图/3D 渲染/佩戴效果/材质拆解/灵感板/色彩 DNA/CAD 技术图）
    + analysis.json
```

## 安装

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
mkdir -p ~/.claude/skills
ln -sf ~/AX-skills/jewelry-marketing ~/.claude/skills/jewelry-marketing
```

## 凭证

只需 2 个 key（放 env 或 `~/.config/gpt-image/credentials`）：

```bash
export GEMINI_API_KEY="..."   # 商品分析（Gemini Flash 3，免费 tier 够）
export OPENAI_API_KEY="..."   # 生图（gpt-image-2 via OpenAI direct）
```

## 调用

```bash
# 完整 marketing bundle — 成品珠宝
~/.claude/skills/jewelry-marketing/generate.py ./pearl_necklace.jpg

# 散石设计套图
~/.claude/skills/jewelry-marketing/generate.py ./loose_stone.jpg --jewelry-type ring

# 只生成几个模板
~/.claude/skills/jewelry-marketing/generate.py ./ring.jpg --templates hero,wristNeck,priceAnchor

# 只要文案+分析（不生图）
~/.claude/skills/jewelry-marketing/generate.py ./ring.jpg --copy-only
```

PEP 723 uv script — 第一次跑 `uv` 自动装依赖。

## 输出 bundle

```
jewelry_bundle/<timestamp>/
├── analysis.json
├── copy.md                # 6 风格小红书文案
├── marketing/             # 或 design/，按 input_type 自动选
│   ├── 01_hero.jpg
│   ├── 02_wristNeck.jpg            # 上手图（爆款封面）
│   ├── 03_gemCutDetail.jpg         # 宝石微距
│   ├── 04_sceneStyleWear.jpg       # 场景化佩戴
│   ├── 05_flatLayEditorial.jpg     # 单品平铺
│   ├── 06_moodboard.jpg            # 品牌情绪板
│   ├── 07_wearStyleGrid.jpg        # 一饰多搭四宫格
│   ├── 08_giftScene.jpg            # 送礼场景海报
│   ├── 09_priceAnchor.jpg          # 价格锚点合集
│   ├── 10_meaningCraftPoster.jpg   # 寓意工艺大字报
│   ├── 11_knowhowAvoid.jpg         # 选购避坑指南
│   └── 12_starTestimonial.jpg      # 明星同款/玄学种草
```

## 关键能力

- **材质感知光照**：钻石高对比、珍珠单光、翡翠均匀透光、黄金 3000K 暖光自动注入
- **场景智能路由**：古法金→新中式古建、钻石→晚宴餐厅、珍珠→咖啡馆白墙
- **佩戴位识别**：项链→颈部锁骨、戒指→手部、耳环→侧脸
- **细分品类专属文案**：翡翠/钻石/珍珠/古法金 各有独立的价格锚点话术、避坑话题、送礼场景
- **占位符纪律**：所有价格留 `¥___`、销量留 `[X]+`，不写死虚假数字

## 模板列表

详见 [`references/JEWELRY_TEMPLATES.md`](./references/JEWELRY_TEMPLATES.md)（20 个模板的视觉/适用场景对照）和 [`references/COPY_STYLES.md`](./references/COPY_STYLES.md)（6 种 XHS 文案风格规则）。

## 为什么直接用，而不是自己写 prompt

12 个营销 prompt 内置千瓜 2024 / 数英 / fxbaogao / 我是产品经理 等多份珠宝电商爆文研究，案例参考：周大福 / HEFANG / 樱桃 / 阑珊珠宝 / 翡翠平安环 / 莫桑钻 / Akoya / 古法金。每个 prompt 都对应一个验证过的爆款公式。

## 单笔成本

| 项 | 成本 |
|---|---|
| 商品分析（Gemini Flash 3） | ~$0.005 |
| 12 张营销图（gpt-image-2 medium） | 12 × ~$0.04 = ~$0.48 |
| **总计** | **~$0.48 / 完整 bundle** |
| 时效（concurrency=4） | 3-5 分钟 |

对比外包：摄影 ¥300-800 + 文案 ¥100-300 + 设计 ¥200-500 = ¥600-1600 / SKU，周期 3-7 天。

## 不适用场景

- 非珠宝品类（服饰 / 美妆 / 食品） — 用通用工具
- 批量超数十件（OpenAI tier RPM 限制）
- 必须像 Tiffany / Bulgari 品牌一致性的高奢场景

## 来源

精炼自 [shichuan (识川)](https://github.com/xingfanxia/shichuan) 生产系统的核心营销模块。
