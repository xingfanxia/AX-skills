# Jewelry Marketing & Design Templates Reference

20 templates total — 12 marketing (finished product) + 8 design (raw material).
Pick subsets via `--templates A,B,C` or generate all with default invocation.

## Marketing pipeline (12) — finished_product input

For sellers with a finished jewelry photo who need XHS-ready posts.

| # | ID | Genre | What it produces | Use this for |
|---|---|---|---|---|
| 01 | `hero` | Studio packshot | 单品棚拍主图，3:4，干净背景，高细节 | 商品详情页主图 / XHS 笔记 cover |
| 02 | `wristNeck` | 上手图/锁骨图 | 颈部/手腕/耳廓局部佩戴近拍（爆款封面） | XHS 转化最强的封面 — 樱桃珠宝 4.7W 粉案例 |
| 03 | `gemCutDetail` | 宝石/工艺微距 | 极近镜，宝石刻面火彩 / 古法錾刻 / 镶嵌 | 建立溢价感 — 周大福古法金核心打法 |
| 04 | `sceneStyleWear` | 场景化佩戴 | 模特半身穿搭场景图（茶馆 / 餐厅 / 古建） | XHS 高颜值穿搭场景类爆文 — EVIE 高奢风 |
| 05 | `flatLayEditorial` | 单品平铺特写 | Tiffany-Cartier 风格俯拍编辑级排版 | 品牌质感 / 详情页配图 |
| 06 | `moodboard` | 品牌情绪板 | 同色系干花+丝绒+小道具组合俯拍 | 周大福粉金系列爆款打法 |
| 07 | `wearStyleGrid` | 一饰多搭四宫格 | 一件首饰 × 4 种穿搭，大字标题压顶 | "1 条项链 × 4 种穿法" 收藏率高 |
| 08 | `giftScene` | 送礼场景海报 | 礼盒+干花+大字情感标题 | 七夕/母亲节/生日转化引流 |
| 09 | `priceAnchor` | 价格锚点合集 | 3-5 件首饰白底分格标价 + 大字标题 | 阑珊珠宝 2.2W 赞案例（"救命她家太便宜"）|
| 10 | `meaningCraftPoster` | 寓意工艺大字报 | 单品+竖排文案，传统/现代两种风格 | 工艺/文化/寓意溢价（古法金、翡翠平安环）|
| 11 | `knowhowAvoid` | 选购避坑指南 | 大问句标题+对比图+干货 4 点 | 翡翠 A/B/C 货 / 钻石 vs 莫桑钻避坑爆文 |
| 12 | `starTestimonial` | 明星同款/玄学种草 | 大字情感钩+宝石主色暗调背景 | HEFANG×刘亦菲爆款 / 蝴蝶玄学锁骨链 |

### Marketing prompts share these properties

- **Material-aware lighting** — auto-injects "diamond high-contrast", "pearl single-soft", "jade even-translucency", "gold warm-3000K" hints based on detected gemstones/materials
- **Scene routing** — 古法金 → 新中式古建筑场景; 钻石 → 暖光餐厅晚宴; 珍珠 → 简约咖啡馆白墙
- **Wear-zone detection** — 项链→颈部锁骨, 戒指→手部, 耳环→侧脸, 手镯→手腕
- **Subcategory-specific copy** — different headlines/avoid topics for 翡翠 / 钻石 / 珍珠 / 古法金
- **Merchant placeholder discipline** — prices stay as `¥___`, contact as `[联系方式]`, never bake fake numbers

## Design pipeline (8) — raw_material input

For sellers with a loose stone / 散石 / 原石 who need to show "what it could become."

`sketch` is the canonical design — its output becomes the reference image
for all 7 dependents, ensuring all images show the SAME design.

| # | ID | Genre | What it produces | Notes |
|---|---|---|---|---|
| 01 | `sketch` | 手绘设计稿 | 水彩+铅笔，Harry Winston 设计室级别 | **Canonical** — 7 others use this as ref |
| 02 | `sketchMulti` | 多角度技术图 | 6视图工程蓝图（前/侧/顶/背/3-4透视/剖面）| 纯铅笔，工程师感 |
| 03 | `rendering3d` | 3D 渲染 | 白底悬浮，KeyShot/V-Ray 级 | 成品预览 |
| 04 | `wearing` | 佩戴效果 | 手/颈/耳的真实佩戴场景 | XHS 风格 |
| 05 | `materialBreak` | 材质拆解 | 深色背景，宝石+金属+成品独立陈列 | 像博物馆陈列 |
| 06 | `moodboard` | 灵感画板 | Pinterest 风拼贴：花/形/光的灵感来源 | 设计叙事 |
| 07 | `colorDna` | 色彩基因 | 水彩色卡，左 40% 首饰右 60% swatches | 配色解读 |
| 08 | `cad3d` | CAD 技术图 | 5视图 + 宝石数量表 + 尺寸标注 | 工厂打版用 |

### Design pipeline routing

- Inferred jewelry_type by category (default `pendant`); override with `--jewelry-type ring|earring|brooch`
- `metal_choice()` picks 18K rose/yellow/white gold based on detected color names
- All non-sketch templates inject the `sketchReferencePrefix` to lock design consistency

## When to subset

```bash
# Just hero + wristNeck + priceAnchor (cheapest viral combo for XHS)
generate.py jewelry.jpg --templates hero,wristNeck,priceAnchor

# Skip the educational poster trio (knowhowAvoid 比较费 prompts/image quality)
generate.py jewelry.jpg --templates hero,wristNeck,gemCutDetail,sceneStyleWear,flatLayEditorial,moodboard,wearStyleGrid,giftScene,priceAnchor,starTestimonial

# Design-only suite minus the engineering blueprint
generate.py stone.jpg --mode design --templates sketch,rendering3d,wearing,materialBreak,moodboard,colorDna,cad3d
```
