"""12 jewelry-proper marketing prompts. Ported from
shichuan/src/lib/gemini/prompts/subcategory/jewelryProper/* — research-backed
templates from XHS jewelry merchant case studies (周大福 / HEFANG / 樱桃 /
阑珊珠宝 / 翡翠平安环 / 莫桑钻 / akoya).
"""
from __future__ import annotations

from typing import Any
from .helpers import (
    product_anchor,
    material_lighting_hints,
    domain_label,
)


# ─── 1. hero — 棚拍主图 ─────────────────────────────────────────
def hero_prompt(a: dict[str, Any]) -> str:
    domain_text = domain_label(a)
    lighting_hints = material_lighting_hints(a)
    return f"""Generate a professional jewelry hero product photo for Xiaohongshu 珠宝首饰 merchant.

Product: {a.get('category', '')} — {a.get('subcategory', '')}
Domain: {domain_text}

{product_anchor(a)}

COMPOSITION:
- Single jewelry piece (necklace/pendant/ring/earring/bracelet) centered
- 45-degree 3/4 angle to reveal setting craftsmanship and stone brilliance simultaneously
- Product occupies 50–60% of frame — generous negative space on all sides
- Slight elevation off surface (resting on velvet prop or angled display stand) to add depth

STYLING / SURFACE:
- Option A (dark contrast): deep-tone jewelry velvet in 墨绿/深蓝/黑 — reveals gold/diamond brilliance
- Option B (light elegance): polished white marble or frosted acrylic — suits platinum/pearl/彩色宝石
- Option C (warm luxury): raw silk or suede in 香槟米/驼色 — for 古法金/黄金 pieces
- Small surface shadow anchors the piece — no floating feeling

LIGHTING:
- Primary: directional spotlight from upper-right emphasizing gemstone faceting / metal luster
- Fill: soft ambient from lower-left to avoid harsh shadow on detail
- For pendants/necklaces: light the chain links individually to show craftsmanship
{lighting_hints}

DETAIL FIDELITY:
- Every prong setting, bead texture, and engraving must be visible
- Chain links must be individually distinguishable, not blurred into a ribbon
- Metal surface: mirror-polish vs. brushed/matte must read clearly

AESTHETIC:
- Premium XHS 珠宝 brand catalog level (HEFANG / 周大福 / 卡地亚 quality reference)
- 3:4 vertical format
- NO text overlays, NO price tags, NO watermarks
- NO props beyond minimal surface styling

DIFFERENTIATION — this is a JEWELRY HERO PACKSHOT, NOT:
- NOT wristNeck (product is NOT worn on a person's body)
- NOT gemCutDetail (shows FULL product from one angle, not extreme macro of one facet)
- NOT sceneStyleWear (no ambient scene, no person, no lifestyle context)
- NOT flatLayEditorial (hero is tighter crop with shallow DoF; flatLayEditorial is overhead with surface as co-subject)
- NOT moodboard (clean neutral background, NOT color/prop collage)"""


# ─── 2. wristNeck — 上手图/锁骨图（核心爆款） ────────────────────
def _detect_wear_zone(a: dict[str, Any]) -> str:
    cat = f"{a.get('category', '')} {a.get('subcategory', '')}".lower()
    import re

    if re.search(r"项链|pendant|吊坠|necklace|锁骨链", cat):
        return "颈部/锁骨"
    if re.search(r"耳环|耳钉|耳饰|earring|耳坠", cat):
        return "耳廓/耳垂"
    if re.search(r"手镯|手链|手串|bracelet|戒指|ring", cat):
        return "手腕/手指"
    return "颈部/锁骨"


def wrist_neck_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    wear_zone = _detect_wear_zone(a)

    if wear_zone == "手腕/手指":
        framing = """- Wrist and hand close-up: show full bracelet/ring in context of the wrist or knuckle
- Hand angle: slightly tilted or resting, natural relaxed pose (not splayed fingers)
- Nails/manicure: complement jewelry color system (pearl piece → soft nude/white; 古法金 → warm terracotta; 彩色宝石 → neutral nude)
- Include approximately 1/3 of forearm for proportion context"""
    elif wear_zone == "颈部/锁骨":
        framing = """- Neck and décolleté close-up: show necklace/pendant against collarbone
- Head cropped at chin or tilted to side — face not the focus
- Clothing: deep V-neck or off-shoulder in solid color that contrasts with jewelry metal
- Posture: slight tilt head away, chin down — exposes collarbone for necklace visibility"""
    else:  # 耳廓/耳垂
        framing = """- Ear and jaw close-up: earring must be fully visible against jawline
- Hair: swept back behind ear or single strand for earring exposure
- Face: cropped at cheekbone — no full face
- Earring position: centered in frame, not clipped by edge"""

    return f"""Generate a JEWELRY WEAR CLOSE-UP (上手图/锁骨图) — the most powerful sales-driving visual for 珠宝首饰 on Xiaohongshu.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

WEAR ZONE: {wear_zone}

BODY FRAMING:
{framing}

SKIN & STYLING:
- Skin tone: natural Asian reference (fair to medium), visible pore texture — "活人感" not overly-retouched
- Clothing color: same color family as jewelry (同色系穿搭) OR complementary neutral
- Suggested combos: 珍珠 → 奶白/粉白系; 黄金/古法金 → 驼色/卡其/深绿; 彩色宝石 → 同色系莫兰迪

LIGHTING:
- Natural window light or soft diffused studio light — avoid harsh flash that washes out skin texture
- Light direction: from the side toward the jewelry piece, creating dimension on metal/stone
{lighting_hints}

JEWELRY IN FRAME:
- Jewelry occupies 30–50% of the frame — prominent but not clipped
- Show the full piece — no cropping of pendant/clasp/earring drop
- Catch the metal/gemstone highlight at least once in frame

AESTHETIC:
- XHS 上手图 style: intimate, tactile, aspirational — feel like a friend wearing it
- 3:4 vertical format
- NO text overlays, NO price labels
- Bokeh background desirable (f/2.8 equivalent) — human element stays soft

DIFFERENTIATION — this is a WEAR CLOSE-UP, NOT:
- NOT a full-body OOTD (tight crop on the jewelry body zone only)
- NOT a hero packshot (jewelry IS on a body — not on a surface)
- NOT sceneStyleWear (no ambient environment — tight body crop, no location context)
- NOT gemCutDetail (jewelry in human context, not extreme isolated macro)"""


# ─── 3. gemCutDetail — 宝石/工艺微距 ─────────────────────────────
def gem_cut_detail_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    has_gemstones = bool(a.get("gemstones"))
    primary_block = (
        """- PRIMARY: gemstone facets — focus on the brightest cut facet, let rainbow dispersion fire across adjacent facets
  * Diamond: show table facet + bezel facets with star dispersion pattern
  * 帕拉伊巴碧玺 / Paraiba tourmaline: capture the neon cyan glow and internal fire
  * 红宝石 Ruby: saturated blood-red with subtle silk inclusion visible
  * 珍珠 Pearl: orient luster — the rainbow shimmer on the surface curve
  * 翡翠 Jadeite: translucent green glow, internal fibrous texture (翠性)"""
        if has_gemstones
        else ""
    )
    return f"""Generate a JEWELRY GEM/CRAFT MACRO DETAIL — extreme close-up revealing the craftsmanship and material quality that justify the price premium on Xiaohongshu.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

MACRO SUBJECT (choose the highest-value detail):
{primary_block}
- SECONDARY (if no gemstone or for engraved/cast metal pieces):
  * 古法金 / hand-hammered surface: individual hammer marks at 1:1 scale
  * 錾刻 (chasing/engraving): pattern depth and shadow in the incised lines
  * 镶嵌工艺 (prong/bezel/pavé setting): show how prong tips grip the stone
  * 珐琅 (cloisonné enamel): color cells and raised wire borders
  * 编织/缠绕: individual wire or bead element crisp at macro scale

MACRO PHOTOGRAPHY SPEC:
- Effective focal length: 1:1 macro equivalent (subject fills frame edge-to-edge)
- Depth of field: razor-thin — only the focal plane is sharp, everything else melts into bokeh
- Focus point: the single most visually spectacular element (peak facet / deepest engraving groove)
- Background: complete obliteration — no surface texture visible beyond 5mm from subject

LIGHTING:
- High-contrast directional spotlight from upper-left hitting the primary facet/texture
- Optional: fiber-optic point source to ignite internal fire in colored stones
- For metal texture: raking light (very low angle ≤10°) to maximize texture shadow depth
- White-balance accurate to the material — diamonds cool, gold warm (3200K)
{lighting_hints}

COLOR ACCURACY:
- Gemstone color MUST match the analysis — no over-saturation for visual pop
- 鸽血红 stays deep red, not cherry; 皇家蓝 is saturated blue-violet, not sky blue
- Metal warmth: 18K yellow gold is deeper amber-gold, not chrome-gold

AESTHETIC:
- No text, no labels — pure material experience
- 3:4 vertical format, but subject can be centered/off-center for visual tension
- Quality feel: gemological photography level, NOT product-shot level

DIFFERENTIATION — this is a GEM/CRAFT MACRO, NOT:
- NOT wristNeck (no human body context — pure material isolation)
- NOT hero (NOT showing the full jewelry piece — only the most spectacular detail)
- NOT flatLayEditorial (extreme stone macro vs full piece visible at normal scale)
- NOT sceneStyleWear (no lifestyle context, no ambient environment)"""


# ─── 4. sceneStyleWear — 场景化佩戴 ──────────────────────────────
def _suggest_scene_style(a: dict[str, Any]) -> tuple[str, str]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))}"
    ).lower()

    if re.search(r"古法|传统|国风|翡翠|青玉|汉|旗袍|錾刻", all_text):
        return (
            "新中式/古建筑",
            "雕花木门前或青砖白墙庭院，光线侧入，配汉服/旗袍/素色棉麻造型。",
        )
    if re.search(r"钻石|diamond|铂金|platinum|婚戒|engagement", all_text):
        return (
            "暖光餐厅/晚宴",
            "烛光餐桌或水晶灯吊顶，深色背景衬托钻石火彩，礼服造型。",
        )
    if re.search(r"珍珠|pearl|月光石|moonstone", all_text):
        return (
            "简约咖啡馆/白墙",
            "奶白色系或淡粉调，大理石桌面，自然窗光，轻柔文艺氛围。",
        )
    return (
        "简约咖啡馆/自然光",
        "白墙浅木桌，自然窗光，中性莫兰迪穿搭，通用型高级感场景。",
    )


def scene_style_wear_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    scene_label, scene_desc = _suggest_scene_style(a)
    return f"""Generate a SCENE-STYLE JEWELRY WEAR PHOTO — atmospheric lifestyle shot with model wearing the jewelry in a curated location. XHS 高颜值穿搭场景类.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

RECOMMENDED SCENE STYLE: {scene_label}
{scene_desc}

SCENE OPTIONS (choose based on jewelry style and material):
- 新中式/古建筑: carved wooden door, 白墙黑瓦 courtyard, blue-and-white ceramic table — for 古法金, 翡翠, 珍珠, 汉服佩饰
- 简约咖啡馆/白墙: marble table, linen textured wall, potted plant — for 设计师款, 轻奢, minimalist silver
- 暖光餐厅/晚宴: candles, crystal glassware, dark wood — for 钻石, 红宝石, 18K黄金 formal pieces
- 自然户外: dappled garden light, stone path, green foliage — for 彩色宝石, 夏日轻盈款
- 书房/文艺空间: aged books, desk lamp, ink stone — for 文人风, 印章戒指, 古典设计

MODEL FRAMING:
- 3/4 body or half body — not full body, not tight face crop
- Face: profile or slight turn — not full frontal; show jewelry in natural interaction with face/neck/hand
- Model posture: natural interaction with scene (手托茶杯 / 侧身扭头 / 低头看书 / 手扶门框)
- Jewelry visible in upper-center of frame (neck/ear/wrist at center to upper-third)

OUTFIT + COLOR COORDINATION:
- Clothing in same color family as jewelry (同色系穿搭)
- 古法金/黄金 → 深绿旗袍 / 驼色汉服 / 米白棉麻
- 珍珠/月光石 → 奶白薄纱 / 淡粉 / 素色
- 钻石/铂金 → 黑色礼服 / 深海蓝天鹅绒
- 彩色宝石 → 中性莫兰迪 tone that doesn't compete with stone color

LIGHTING:
- Scene ambient light coherent with location choice
- Jewelry must catch one directional light source to show sparkle/luster in context
- Skin: warm, healthy, natural — not flash-lit or overexposed
{lighting_hints}

TEXT ELEMENT (optional, minimal):
- Small corner tag ≤20 characters allowed: "新中式通勤" / "度假穿搭" / "约会精致感"
- Font: clean sans-serif, white or pale color, lower-left or lower-right corner only

AESTHETIC:
- XHS aspirational but attainable: feel like a real-life styled moment, not a fashion magazine
- Color grading: slightly warm, high-key for daytime; moody low-key for evening
- 3:4 vertical format
- NO large headline text, NO price overlays

DIFFERENTIATION — this is a SCENE-STYLE WEAR PHOTO, NOT:
- NOT wristNeck (full upper-body scene context, not a tight body-part crop)
- NOT hero (jewelry is ON a person in a LOCATION, not on a surface)
- NOT moodboard (real photographic scene, not a collage of props + jewelry)
- NOT wearStyleGrid (single scene/style, not a 4-cell comparison grid)"""


# ─── 5. flatLayEditorial — 单品平铺特写 ──────────────────────────
def flat_lay_editorial_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    return f"""Generate a SINGLE-PIECE JEWELRY EDITORIAL FLAT LAY — the ONE uploaded piece photographed on a premium surface, magazine-cover quality with generous breathing room.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

CRITICAL RULE — exactly ONE piece, no invented extras:
- The ONE uploaded jewelry piece is the only jewelry subject in frame
- Do NOT add matching earrings, rings, bracelets, or "collection variants" — even if the composition feels sparse
- Do NOT show "before/after" or duplicate the piece — there is exactly one
- If the frame feels empty, fill with NON-jewelry props: dried flower petals, silk ribbon, parchment paper, soft shadows, paper texture, candle wax, single perfume bottle (out-of-focus)

SURFACE OPTIONS (pick one based on product warmth/coolness):
- Option A — luxury classic: deep-tone 天鹅绒 tray (墨绿/深蓝/黑/酒红); piece centered, ample velvet around
- Option B — modern minimal: polished white marble slab; piece off-center per rule-of-thirds, lots of negative space
- Option C — editorial dramatic: matte 黑色哑光亚克力 surface; single dramatic side-light, deep shadow opposite
- Option D — soft editorial: aged cream paper or champagne silk; warm tone, painterly soft lighting
- Option E — display tray: open velvet 首饰盒 with cushion; single piece nested, lid partially open showing depth

COMPOSITION:
- ONE piece occupies ~15-25% of frame area; remaining 75%+ is surface + props + breathing room
- Magazine catalog feel — clean, intentional, never crowded
- 90° flat overhead (俯拍) preferred for editorial purity
- 30-45° angle acceptable when surface depth/tray cushioning is the visual story

LIGHTING:
- Single soft-box from above-left, gentle bounce-fill from right
- Every gem facet has a crisp catch-light, every metal edge has a clean highlight
- Shadows soft and defined — not harsh, not non-existent
- Color temperature warm (gold pieces) or cool (silver/platinum) to match metal family
{lighting_hints}

PROP CHOICES (pick at most 1-2 — keep it minimal):
- Wedding/bridal context: dried hydrangea petals, silk ribbon, paper place card
- Fine-jewelry context: marble, water droplets, single rose stem
- Gift context: wrapped ribbon, opened jewelry box, gift card edge
- Everyday-wear context: bare surface only, no props (let piece speak)

AESTHETIC:
- XHS 单品产品摄影 / Tiffany-Cartier catalog aesthetic
- 3:4 vertical format
- NO text overlays, NO price tags, NO numbering, NO watermarks
- Editorial restraint — feels like a museum or high-end magazine plate

DIFFERENTIATION — this is a SINGLE-PIECE EDITORIAL FLAT LAY, NOT:
- NOT hero (hero is tighter crop with shallow DoF; this is overhead/angled with surface as co-subject)
- NOT moodboard (this is jewelry-on-surface; moodboard is multi-prop lifestyle collage)
- NOT sceneStyleWear (no model, no person, no location scene — just product on surface)
- NOT gemCutDetail (full piece visible at normal scale, not extreme stone macro)
- NOT a collection overview (exactly ONE piece — no invented matching variants)"""


# ─── 6. moodboard — 品牌情绪板 ───────────────────────────────────
def _suggest_color_palette(a: dict[str, Any]) -> tuple[str, str]:
    import re

    all_text = (
        f"{' '.join(g.get('name', '') + ' ' + g.get('color', '') for g in a.get('gemstones', []))} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))} "
        f"{a.get('design_concept', '')}"
    ).lower()
    if re.search(r"黄金|古法金|gold|暖金", all_text):
        return ("暖金调 · 驼棕蜂蜜", "蜂蜜金、驼色、深棕构成暖调三色系。干蜡菊、驼色丝绒、暖木表面。")
    if re.search(r"珍珠|pearl|月光石|moonstone", all_text):
        return ("奶白粉调 · 纯欲氛围", "奶白、裸粉、浅灰构成柔和三色系。白色绢花芍药、粉白薄纱、浅灰大理石。")
    if re.search(r"帕拉伊巴|paraiba|蓝|海蓝|aquamarine|蓝宝", all_text):
        return ("冷蓝调 · 深海氛围", "霓虹蓝绿、冰蓝、白银构成冷调。押花蓝星花、浅蓝丝绸、白色大理石。")
    if re.search(r"钻石|diamond|铂金|platinum", all_text):
        return ("冷白调 · 纯净高奢", "纯白、冷银、极浅灰构成极简三色系。白色绣球干花、银灰丝绒、抛光白大理石。")
    return (
        "莫兰迪中性调",
        "首饰主色降饱和+白+米/浅灰作陪衬。从产品分析颜色中提取主色，配同色系干花与素色布料。",
    )


def moodboard_prompt(a: dict[str, Any]) -> str:
    palette_name, palette_desc = _suggest_color_palette(a)
    return f"""Generate a JEWELRY BRAND MOODBOARD — a color-story flat lay that places the jewelry at center of a curated same-tone prop arrangement. 色系氛围搭配图.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

COLOR PALETTE: {palette_name}
{palette_desc}

PROP SELECTION (all in the same color family as the jewelry):
- JEWELRY: the hero piece, centered or slightly off-center, occupying ~30% of frame
- FLORALS: 干花/绢花 in palette-matching tones (绢花 preferred — no moisture/wilting)
  * 珍珠/月光石 → 奶白芍药、浅粉玫瑰干花
  * 黄金/古法金 → 暖黄蜡菊、驼色干芒草
  * 钻石/铂金 → 白色大理石石花 or 素白绣球
  * 彩色宝石 (帕拉伊巴/海蓝宝) → 同色系押花薰衣草/蓝星花
- FABRIC: a draped silk or velvet swatch in the palette (1/4 of frame edge)
- ACCENT: one small complementary object — 唇膏管 / 指甲油瓶 / 小香水瓶 / 宝石散件 in matching tone
- OPTIONAL: handwritten note card or small letter seal in same color family

ARRANGEMENT:
- Main jewelry piece as clear visual anchor (centered or golden-ratio position)
- Props distributed radially or in C-curve around jewelry
- Negative space must remain at ≥30% — props support, not overwhelm
- All props stay within 3cm of jewelry — tight grouping, no scattered layout

FLAT LAY TECHNIQUE:
- 90° overhead shot (flat lay standard)
- Lighting: soft diffused natural light OR soft box — even light, no harsh shadows
- Surface: choose one that belongs to the palette:
  * 白色大理石 for cool palettes (silver/pearl/blue stone)
  * 深色绒布 or 木纹板 for warm palettes (gold/warm stone)
  * 奶白麻布 for soft romantic palettes (珍珠/粉彩)

COLOR DISCIPLINE:
- 3 colors maximum in total composition (primary jewelry color + 1-2 supporting tones)
- No high-chroma competing colors — moodboard must feel like one coherent vision, not a market stall
- Metal and fabric must be within 2 Munsell steps of the same hue family

AESTHETIC:
- XHS 品牌情绪/氛围系 aesthetic: curated, editorial, "想要这种生活" feeling
- 3:4 vertical format
- NO large text overlays, NO price tags
- Optional tiny brand/logo watermark in lower corner (≤8pt, minimal opacity)

DIFFERENTIATION — this is a BRAND MOODBOARD, NOT:
- NOT flatLayEditorial (moodboard is multi-prop color story; flatLayEditorial is jewelry-on-surface with minimal props)
- NOT sceneStyleWear (flat lay overhead — no person, no location scene)
- NOT hero (multiple elements, color-story context — not a clean isolated product shot)
- NOT giftScene (this is aesthetic/branding, not transaction/gift-giving framing)"""


# ─── 7. wearStyleGrid — 一饰多搭四宫格 ───────────────────────────
def _suggest_style_quad(a: dict[str, Any]) -> list[dict[str, str]]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))}"
    ).lower()

    if re.search(r"古法|国风|翡翠|传统|錾刻|汉", all_text):
        return [
            {"zone": "top-left", "outfit": "新中式日常", "outfitDetail": "马面裙/改良汉服+中式盘扣上衣，配此件首饰", "label": "新中式"},
            {"zone": "top-right", "outfit": "通勤职场", "outfitDetail": "白衬衫+阔腿裤或西装，以首饰点睛", "label": "通勤风"},
            {"zone": "bottom-left", "outfit": "度假/周末", "outfitDetail": "素色棉麻连衣裙+草帽，自然轻松", "label": "度假感"},
            {"zone": "bottom-right", "outfit": "约会", "outfitDetail": "吊带裙或V领上衣，展示颈部/耳廓线条", "label": "约会感"},
        ]

    if re.search(r"钻石|diamond|铂金|platinum|婚|engagement", all_text):
        return [
            {"zone": "top-left", "outfit": "晚宴礼服", "outfitDetail": "黑色礼服/抹胸裙，钻石在低领处闪耀", "label": "晚宴感"},
            {"zone": "top-right", "outfit": "职场精致", "outfitDetail": "西装/职业套装，细款钻石配件低调奢华", "label": "职场精英"},
            {"zone": "bottom-left", "outfit": "约会轻奢", "outfitDetail": "丝绸衬衫+半裙，优雅休闲场合", "label": "约会精致"},
            {"zone": "bottom-right", "outfit": "日常通勤", "outfitDetail": "简约 T 恤/针织衫，首饰作为全身唯一高光点", "label": "日常高级"},
        ]

    return [
        {"zone": "top-left", "outfit": "通勤", "outfitDetail": "简约 T 恤+西装裤+平底鞋，首饰提升精致感", "label": "通勤风"},
        {"zone": "top-right", "outfit": "约会", "outfitDetail": "V领/吊带裙，突出颈部/耳廓，半卷发", "label": "约会感"},
        {"zone": "bottom-left", "outfit": "新中式", "outfitDetail": "马面裙/改良旗袍，搭配此件体现国风雅致", "label": "国风雅韵"},
        {"zone": "bottom-right", "outfit": "休闲 ins", "outfitDetail": "卫衣+牛仔裤+运动鞋，首饰成为混搭亮点", "label": "休闲酷感"},
    ]


def wear_style_grid_prompt(a: dict[str, Any]) -> str:
    cells = _suggest_style_quad(a)
    cells_lines = "\n".join(f"- Cell {i+1} ({c['zone']}): {c['outfit']} — {c['label']}" for i, c in enumerate(cells))
    outfit_detail_lines = "\n".join(f"- {c['label']}: {c['outfitDetail']}" for c in cells)
    label_quote = "\" / \"".join(c['label'] for c in cells)
    return f"""Generate a JEWELRY WEAR-STYLE FOUR-CELL GRID (一饰多搭 · 四宫格) — showing HOW ONE piece of jewelry pairs with four different outfit styles on Xiaohongshu.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

GRID LAYOUT — 2×2 equal quadrants:
{cells_lines}

TOP HEADER BAND (大字标题 — REQUIRED):
- Full-width header above the 2×2 grid
- Headline text (choose one based on product):
  * "1 条项链 × 4 种穿法"
  * "这条链子比我想的更能搭"
  * "买它！通勤约会都拿捏了"
  * "1 件首饰，4 套不同的你"
- Font: bold Chinese sans-serif (黑体/方正), white text on jewelry-tone background
  * 黄金/古法金 → 深墨绿或深棕背景
  * 珍珠/铂金 → 深海军蓝或炭黑背景
  * 彩色宝石 → 宝石主色系深色渐变
- Headline occupies full width, 28–36pt equivalent, fills ~15% of total frame height

EACH CELL CONTENT:
- Half-body or 3/4-body model wearing THE SAME jewelry piece throughout all 4 cells
- Jewelry must be visually identical (same piece, same angle) — only the outfit changes
- Small style tag at corner (white rounded-rect badge, ≤6 Chinese characters):
  * "{label_quote}"
- Natural lighting consistent across cells — same warm daylight feel

OUTFIT COORDINATION (per cell):
{outfit_detail_lines}

GRID COMPOSITION:
- Thin 2–3px white gutter between cells — clean separation
- All 4 cells share same color grading (same warm/cool tone) — feels like one shoot
- Model same person across cells (continuity) — face can be cropped or turned

AESTHETIC:
- XHS 商家账号风格 — aspirational yet relatable, not high-fashion editorial
- 3:4 vertical overall frame
- NO additional watermarks, NO price overlays (headline only at top)
- Small corner price tag (optional): "¥___ 起" at lower-right of header band, ≤12pt — leave as placeholder

DIFFERENTIATION — this is a WEAR-STYLE FOUR-CELL GRID, NOT:
- NOT sceneStyleWear (4-cell comparison structure, not a single atmospheric scene)
- NOT moodboard (real photographic outfit cells, not a prop collage)
- NOT flatLayEditorial (wearStyleGrid is on-person 4-cell outfit grid; flatLayEditorial is overhead product flat lay)
- NOT giftScene (styling proposal, not a gift-giving transaction poster)
- NOT hero (always on a person, not on a surface)"""


# ─── 8. giftScene — 送礼场景海报 ─────────────────────────────────
def _suggest_gift_scene(a: dict[str, Any]) -> dict[str, Any]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(g.get('name', '') for g in a.get('gemstones', []))}"
    ).lower()
    if re.search(r"翡翠|玉|jade|平安|福", all_text):
        return {
            "occasion": "母亲节/长辈礼",
            "recipient": "妈妈/婆婆/长辈",
            "palette": "暖白+淡绿+驼金，干花白牡丹，香槟色礼盒",
            "headlines": ["送妈妈 · 一件真正有分量的礼", "孝顺这件事，从这条项链开始", "送她·值得的心意"],
            "occasionTag": "母亲节首选 · 含礼盒",
        }
    if re.search(r"钻石|diamond|戒指|ring|对戒|婚戒|engagement", all_text):
        return {
            "occasion": "求婚/纪念日/七夕",
            "recipient": "爱人/女友",
            "palette": "深酒红+香槟金+奶白，玫瑰干花，黑色高档礼盒",
            "headlines": ["七夕不知道送什么？看这里", "把爱，装进这个盒子里", "送她 · 值得一辈子的礼"],
            "occasionTag": "七夕限定 · 含精美礼盒",
        }
    if re.search(r"珍珠|pearl", all_text):
        return {
            "occasion": "生日/纪念日/白色情人节",
            "recipient": "女友/闺蜜/自己",
            "palette": "奶白+粉藕+浅金，芍药干花，奶白丝绒礼盒",
            "headlines": ["送她 · 值得的心意", "每个女生都该有一件", "把这份温柔，送给她"],
            "occasionTag": "生日首选 · 含精美礼盒",
        }
    return {
        "occasion": "七夕/生日/纪念日",
        "recipient": "女友/爱人",
        "palette": "香槟金+奶白+深绿，干玫瑰花瓣，品牌礼盒",
        "headlines": ["送她 · 值得的心意", "七夕限定 | 送这条就够了", "有一种心意，叫做这件首饰"],
        "occasionTag": "含精美礼盒包装",
    }


def gift_scene_prompt(a: dict[str, Any]) -> str:
    gift = _suggest_gift_scene(a)
    headlines = "\n".join(f"  * \"{h}\"" for h in gift["headlines"])
    main_gem = a.get("gemstones", [{}])[0].get("name", "宝石") if a.get("gemstones") else "宝石"
    return f"""Generate a JEWELRY GIFT SCENE POSTER — a warm gift-giving lifestyle composition with large Chinese headline, for 珠宝首饰 Xiaohongshu merchants.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

GIFT CONTEXT: {gift['occasion']}
Target recipient: {gift['recipient']}

SCENE COMPOSITION:
- Jewelry piece displayed INSIDE or BESIDE an open luxury gift box (品牌礼盒)
  * Box: matte paper or rigid box lid open, interior lined with 丝绒/绢布 in brand color
  * Box lid angled ≤45° to show interior lining depth
- 1–2 decorative accents (choose from):
  * 干玫瑰花瓣 scattered on table surface (not overwhelming)
  * Satin ribbon tied around box (loose bow, not a stiff commercial bow)
  * Small envelope/gift card propped against box
  * Eucalyptus or dried cotton stems in background
- Surface: softly lit warm wooden table OR pale marble, no sharp shadows
- Scene color palette: {gift['palette']}

LARGE HEADLINE (大字标题 — REQUIRED, top 25–30% of frame):
- Chinese bold headline in large type (32–40pt equivalent):
{headlines}
  (Choose whichever fits the product best, or combine the first two lines)
- Font weight: 黑体/粗宋 for headline — high-impact
- Color: white text on a dark band overlay OR gold text on cream background
- Headline background: full-width color band (brand-tone) OR the scene background itself if high-contrast

SUPPORTING COPY (secondary text, smaller):
- Price line at lower area: "¥___ 送出·值得的心意" (LEAVE PLACEHOLDER as ¥___, NEVER bake in a number)
  OR occasion tag: "{gift['occasionTag']}"
- Material/craft line: e.g., "18K 金 · 天然{main_gem} · 含礼盒包装"
- Bottom right corner: tiny brand/shop name placeholder "[品牌]"

COLOR PALETTE:
- {gift['palette']}
- Avoid overusing red/pink unless it's CNY or Valentine's explicitly — it reads cheap
- 金色首饰 → 香槟金 + 深绿/深棕；珍珠 → 奶白 + 粉藕色；彩宝 → 宝石主色系渐变

LIGHTING:
- Soft warm studio light (3200–3800K) — "temperature" evokes warmth of gifting moment
- Jewelry must catch at least one catch light inside the box
- No harsh shadows on the box interior or table surface

AESTHETIC:
- XHS 珠宝礼赠内容 aesthetic: warm, thoughtful, premium — NOT a commercial catalog
- 3:4 vertical format
- Headline is the conversion hook — must be legible at thumbnail size in XHS feed

DIFFERENTIATION — this is a GIFT SCENE POSTER, NOT:
- NOT hero (jewelry is in a gift context with box + props, not isolated on a surface)
- NOT moodboard (this is transaction-oriented, with headline + price — not pure brand aesthetics)
- NOT sceneStyleWear (no person wearing it — gift presentation, not wearing context)
- NOT priceAnchor (emphasis on sentiment/occasion, not price comparison)
- NOT meaningCraftPoster (scene/occasion framing, not craft/寓意 explanation)"""


# ─── 9. priceAnchor — 价格锚点合集 ───────────────────────────────
def _suggest_price_anchor(a: dict[str, Any]) -> dict[str, Any]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))}"
    ).lower()
    if re.search(r"黄金|古法金|gold", all_text):
        return {
            "context": "古法金/黄金首饰价格揭秘",
            "headlines": ["救命！古法金也能这么便宜？", "黄金首饰不用花大价钱", "同款工艺，水贝直发价"],
            "headlineColor": "深金色或深棕色",
            "headlineBg": "香槟米白底",
        }
    if re.search(r"钻石|diamond", all_text):
        return {
            "context": "钻石首饰价格对标大牌，强调证书/品质与性价比",
            "headlines": ["¥___ vs 大牌 ¥___，差在哪里？", "GIA 证书钻戒，不用大牌价格", "救命！这家钻石也太值了"],
            "headlineColor": "纯黑或深炭色",
            "headlineBg": "纯白底",
        }
    if re.search(r"珍珠|pearl", all_text):
        return {
            "context": "淡水/akoya 珍珠价格揭秘",
            "headlines": ["天然珍珠，¥___ 就能拥有", "救命！这家珍珠也太好看了", "设计师珍珠款，不用大牌价"],
            "headlineColor": "深海军蓝",
            "headlineBg": "奶白底",
        }
    return {
        "context": "设计师款首饰直发价",
        "headlines": ["救命！这家珠宝也太便宜了", "设计师款 ≠ 高价", "3 件全拿走也不到 ¥___"],
        "headlineColor": "红色或深金色（吸引眼球）",
        "headlineBg": "白底",
    }


def price_anchor_prompt(a: dict[str, Any]) -> str:
    anchor = _suggest_price_anchor(a)
    headlines = "\n".join(f"  * \"{h}\"" for h in anchor["headlines"])
    return f"""Generate a JEWELRY PRICE ANCHOR GRID — a clean multi-piece price-display poster with a large emotional headline, designed to make jewelry look surprisingly affordable on Xiaohongshu.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

PRICE CONTEXT: {anchor['context']}

LAYOUT:
- 3–5 jewelry pieces arranged in a clean grid:
  * 3 pieces: single row, horizontal (1×3)
  * 4 pieces: 2×2 grid
  * 5 pieces: 2 top + 3 bottom, asymmetric
- Each piece: product shot on WHITE or VERY PALE background (no props, no scene)
- Below each piece: price label in bold black ink — render as "¥___" placeholder (DO NOT bake in a specific number — merchant fills in)
- Thin hairline borders between cells (1–2px, light gray)

HEADLINE (大字标题 — REQUIRED, top of image):
Choose from (render actual Chinese text):
{headlines}
- Font: 粗黑体, fullwidth, 32–42pt equivalent
- Color: {anchor['headlineColor']}
- Background of headline band: {anchor['headlineBg']}

PRICE DISPLAY (per piece):
- Price below each product: render "¥___" placeholder (large bold)
- Optional: crossed-out comparison price "原价 ¥___" in smaller gray
- Price font: bold, readable — NOT decorative
- DO NOT commit to specific numbers — placeholders only

PRODUCT IMAGES IN GRID:
- Each piece shown on pure white or very pale gray/cream background
- Consistent scale across cells — no one piece dramatically larger
- Studio-quality lighting on each piece — flat even light, no harsh shadows
- Pieces represent the SAME series/style family as the reference product

OPTIONAL CALLOUT ELEMENTS:
- "收藏慢慢买" or "全部加购" small text prompt at bottom center (≤12pt)
- "设计师款" or 销量 badge "🔥 本月销量 [X]+" on 1 piece (placeholder, optional)

BACKGROUND:
- Full image background: white or very pale off-white (米白/象牙白)
- No dark backgrounds — this is a price-revelation poster, needs clean readability
- Subtle thin outer border (1–2px) for composed feel

AESTHETIC:
- XHS 珠宝价格透明 aesthetic: clean, informative, confidence-inspiring
- Feels like a merchant's "明码标价" announcement, not a cluttered marketplace listing
- 3:4 vertical format
- Small shop logo / 店铺名 placeholder at bottom (≤8pt)

DIFFERENTIATION — this is a PRICE ANCHOR GRID, NOT:
- NOT flatLayEditorial (priceAnchor has prices/text; flatLayEditorial is no-text editorial product shot)
- NOT wearStyleGrid (no model, no outfit context — product + price only)
- NOT hero (multiple pieces in grid, not a single product hero)
- NOT giftScene (no occasion framing, no gift box — this is direct value proposition)
- NOT knowhowAvoid (topic is price/value, not consumer protection)"""


# ─── 10. meaningCraftPoster — 寓意工艺大字报 ─────────────────────
def _suggest_poster_copy(a: dict[str, Any]) -> dict[str, Any]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))} "
        f"{' '.join(g.get('name', '') for g in a.get('gemstones', []))}"
    ).lower()
    if re.search(r"古法|黄金|gold|錾刻|传统|手工|汉", all_text):
        return {
            "style": "传统古典风 · 楷体竖排",
            "headline": "錾刻 · 古法黄金 · 传承工艺",
            "bodyLines": ["一锤一凿，千年匠心", "手工錾刻纹样，源自传统纹饰", "每一件，皆是不可复制的孤品"],
            "materialTag": "18K 足金 · 手工錾刻",
            "textColor": "深金色或香槟金",
            "background": "白底 + 淡金色纸纹肌理；OR 哑光黑底 + 香槟金字（更高级感）",
        }
    if re.search(r"翡翠|jade|玉|平安|福寿", all_text):
        return {
            "style": "东方文人风 · 仿宋竖排",
            "headline": "翠色天成 · 一石一世界",
            "bodyLines": ["冰种起莹光，色正无杂", "玉养人，人养玉", "佩之以福，传之以情"],
            "materialTag": "天然翡翠 · 冰种阳绿",
            "textColor": "墨绿或深青，米白背景",
            "background": "米白宣纸肌理 + 淡竹纹底图；墨绿/深青边框细线",
        }
    if re.search(r"珍珠|pearl", all_text):
        return {
            "style": "现代轻奢风 · 细黑体横排",
            "headline": "珍珠 · 来自深海的温柔",
            "bodyLines": ["天然有核养殖，光泽层层叠叠", "Akoya 贝养育，6–8mm 正圆", "戴上，就是你最好的修饰"],
            "materialTag": "天然淡水珍珠 · 正圆 · 高光泽",
            "textColor": "深海军蓝，奶白背景",
            "background": "奶白色或极浅粉灰，丝绒纹理底",
        }
    if re.search(r"钻石|diamond|铂金|platinum", all_text):
        return {
            "style": "现代高奢风 · 几何细黑体",
            "headline": "钻石 · 永恒的本质",
            "bodyLines": ["4C 严选，每一颗都有身份", "GIA 国际认证，火彩清晰可见", "戴上它，光就在你身边"],
            "materialTag": "天然钻石 · GIA 认证 · 18K 铂金镶嵌",
            "textColor": "纯白，深黑底",
            "background": "哑光深黑底 + 冷银细线边框，极简奢感",
        }
    main_concept = (a.get("design_concept", "")[:20]) or "精工设计，源于热爱"
    main_mat = (a.get("materials", [{}])[0].get("material", "")) or "精选材质"
    return {
        "style": "现代简约风 · 细黑体",
        "headline": "设计 · 不止于美",
        "bodyLines": [main_concept, "每一件都经过手工调校", "让首饰，成为你最好的表达"],
        "materialTag": f"{main_mat} · 手工制作",
        "textColor": "深炭黑，白底；或白色，深色背景",
        "background": "纯白或极浅灰，底部细线装饰",
    }


def meaning_craft_poster_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    p = _suggest_poster_copy(a)
    body_lines = "\n  ".join(f'"{l}"' for l in p["bodyLines"])
    return f"""Generate a JEWELRY MEANING/CRAFT POSTER (工艺寓意大字报) — a typographic poster where ONE jewelry piece is the visual anchor and Chinese calligraphic/editorial text tells the craft or cultural story.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

POSTER STYLE: {p['style']}

LAYOUT (choose one based on product category):
Option A — Left-Right Split (recommended for 古法金/翡翠/传统工艺):
  - LEFT 60%: Jewelry product shot, clean background, no props
  - RIGHT 40%: Vertical Chinese text column (竖排)
  - Divider: hairline gold/silver rule separating image and text

Option B — Center Image + Bottom Text (recommended for 现代轻奢/彩宝):
  - TOP 55–60%: Jewelry hero shot (centered, studio lit, gemstone sparkle visible)
  - BOTTOM 40–45%: Large Chinese headline + 2-line subtitle block
  - Background: full bleed behind both zones, single color or subtle texture

JEWELRY PRODUCT SHOT (within poster):
- Show the FULL jewelry piece, studio lit, no person
- {lighting_hints}
- Surface: minimal prop (small velvet tray fragment or paper white) — jewelry must not float

TEXT CONTENT (REQUIRED — render actual Chinese characters):
HEADLINE (大标题, 28–36pt equivalent, most prominent):
  "{p['headline']}"

CRAFT/MEANING BODY (secondary text, 14–18pt):
  {body_lines}

MATERIAL TAG (small, 10–12pt, corner or below headline):
  "{p['materialTag']}"

TYPOGRAPHY STYLE:
- Traditional/古法金 pieces: 楷体 or 仿宋 for body text, 宋体 for headline — conveys 传承感
- Modern/轻奢 pieces: 细黑体 or geometric sans for headline, thin weight for body — conveys 精工感
- All Chinese text must render as LEGIBLE characters — NOT decorative stroke art or garbled AI text
- Text color: {p['textColor']}

BACKGROUND + COLOR:
- {p['background']}
- Accent rule/divider: thin gold (0.5pt) or warm ivory line

SMALL SUPPORTING ELEMENTS (optional):
- Corner brand micro-tag (lower-right, ≤8pt) — leave as "[品牌]" placeholder
- Material parameters in tiny monospace
- Red/gold seal stamp graphic (印章) if 国风/古典 theme — adds authenticity

AESTHETIC:
- XHS 珠宝知识海报 aesthetic: premium, educational, culturally resonant
- Feels like a brand campaign poster, not a product page layout
- 3:4 vertical format
- NO price overlays (this is brand-building, not price anchor)

DIFFERENTIATION — this is a MEANING/CRAFT POSTER, NOT:
- NOT hero (text is required — this is a text+image editorial, not a clean product shot)
- NOT giftScene (no gift box, no occasion framing — this explains the craft/寓意 of the piece itself)
- NOT knowhowAvoid (tone is brand storytelling/aspirational, not consumer protection/education)
- NOT starTestimonial (brand/craft story, not celebrity association or trend hook)
- NOT flatLayEditorial (meaningCraftPoster is text+image editorial with story; flatLayEditorial is no-text product shot)"""


# ─── 11. knowhowAvoid — 选购避坑指南 ─────────────────────────────
def _suggest_avoid_guide(a: dict[str, Any]) -> dict[str, Any]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(g.get('name', '') for g in a.get('gemstones', []))} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))}"
    ).lower()
    sub = a.get("subcategory", "首饰")

    if re.search(r"钻石|diamond", all_text):
        return {
            "topic": "钻石选购避坑：莫桑钻 vs 天然钻 vs 培育钻",
            "headlines": ["买钻戒前，这 3 个坑一定要知道", "钻石怎么挑？避开这些别再踩坑了", "花大价钱买钻石，先看这张图"],
            "headlineColor": "纯白",
            "headlineBg": "深黑底（紧迫感）",
            "useComparison": True,
            "comparisonBad": "莫桑钻/仿钻，在紫外线下会发出强蓝绿荧光，火彩过亮",
            "comparisonGood": "天然钻石，GIA 证书有激光腰纹编码，导热测试通过",
            "points": [
                "① 看荧光反应：天然钻在紫外线下有轻微蓝色荧光，莫桑钻发强绿色荧光",
                "② 看 GIA 证书：腰纹处有激光刻码，可在 GIA 官网验证",
                "③ 测导热率：钻石导热系数极高，莫桑钻相近但仍有差异",
                "④ 看 4C：切工 (Cut) 比克拉重量更影响火彩，优先选 Excellent",
            ],
            "background": "深黑底 or 深海军蓝 + 白字",
            "accentColor": "金色/香槟色",
        }
    if re.search(r"翡翠|jade|玉", all_text):
        return {
            "topic": "翡翠选购避坑：A 货 vs B 货 vs C 货辨别",
            "headlines": ["如何辨别翡翠真假？避开这 3 个坑", "买翡翠不看这个，你可能在交学费", "翡翠 A/B/C 货怎么分？一图看懂"],
            "headlineColor": "深墨绿",
            "headlineBg": "米白底",
            "useComparison": True,
            "comparisonBad": "B 货（漂白注胶处理）：表面有「橘皮纹」，UV 灯下胶质发蓝绿荧光",
            "comparisonGood": "A 货天然翡翠：证书标注 Natural Jadeite，棉絮/翠性可见",
            "points": [
                "① 看证书：正规珠宝鉴定证书（GIC/NGTC）标注 A 货才是天然",
                "② 看光泽：天然 A 货光泽柔和通透，B 货注胶后光泽偏「胶感」",
                "③ 看纹理：天然翡翠有「翠性」（闪光纤维），B 货注胶后翠性消失",
                "④ 看价格：价格极低的「高冰老坑」大概率非真，一物一价是常态",
            ],
            "background": "米白或淡绿底",
            "accentColor": "墨绿色",
        }
    if re.search(r"珍珠|pearl", all_text):
        return {
            "topic": "珍珠选购指南：天然 vs 人工、淡水 vs akoya",
            "headlines": ["珍珠怎么挑？这 3 点先搞清楚", "同是珍珠，为什么差这么多？", "买珍珠前，先看这张避坑图"],
            "headlineColor": "深海军蓝",
            "headlineBg": "奶白底",
            "useComparison": True,
            "comparisonBad": "低质淡水珍珠：表面有明显坑纹，光泽层薄，近看有「皱皮感」",
            "comparisonGood": "高光泽 Akoya/大颗淡水：镜面反光可见，Orient 彩虹光泽明显",
            "points": [
                "① 看光泽层：优质珍珠表面可以像镜子一样反射出自己的脸，称为「镜面光泽」",
                "② 看形状：正圆珍珠价值最高，接近正圆（偏差 ≤2%）次之",
                "③ 看瑕疵：在强光下转动，表面凹坑/环纹越少越好",
                "④ 淡水 vs Akoya：Akoya 光泽更强，价格更高；淡水性价比高，颗粒可更大",
            ],
            "background": "奶白底 + 淡蓝边框",
            "accentColor": "深海军蓝",
        }
    return {
        "topic": f"{sub} 选购避坑指南",
        "headlines": [f"买{sub}，这 3 个坑别踩", "珠宝选购指南 | 看这一张就够了", "买首饰前必看！避坑清单"],
        "headlineColor": "深炭黑或红色",
        "headlineBg": "白底或浅灰",
        "useComparison": False,
        "comparisonBad": "",
        "comparisonGood": "",
        "points": [
            "① 看材质证书：纯金/银必须有材质检测报告，认 Au999/AG999 标识",
            "② 看工艺质量：镶口是否牢固，爪齿是否均匀，焊点是否可见",
            "③ 看宝石真实性：彩宝须附鉴定证书，标注是否经过烧色/填充处理",
            "④ 看售后：真正的珠宝商家提供免费调圈/清洗服务，这是品质信号",
        ],
        "background": "白底 + 浅灰分区",
        "accentColor": "深金色或深蓝",
    }


def knowhow_avoid_prompt(a: dict[str, Any]) -> str:
    g = _suggest_avoid_guide(a)
    headlines = "\n".join(f"  * \"{h}\"" for h in g["headlines"])
    if g["useComparison"]:
        product_image_block = f"""- Split comparison (左/右 or 上/下):
  * LEFT/TOP labeled "❌ 踩坑" or "别买这种": {g['comparisonBad']}
  * RIGHT/BOTTOM labeled "✅ 这样选" or "正确做法": {g['comparisonGood']}
  * Labels: white text on red/green badge — small rounded rect"""
    else:
        product_image_block = """- Single product image: the reference jewelry piece centered, well-lit
  * Product represents "正确选择" — no comparison needed
  * Subtle "✅" or quality badge in corner"""
    points_block = "\n".join(f"  ① point {i+1}: \"{p}\"" for i, p in enumerate(g["points"]))
    return f"""Generate a JEWELRY KNOWHOW / AVOID-PITFALLS POSTER (选购避坑大字报) — a single-sheet information poster with a big question/warning headline, product or comparison image, and numbered dry-knowledge points.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

TOPIC: {g['topic']}

POSTER LAYOUT:
- TOP 30%: Large bold Chinese headline (疑问句 or 避坑句式)
- MIDDLE 35–40%: Product image OR comparison graphic (left = 踩坑, right = 正确/这家)
- BOTTOM 35–30%: 3–5 numbered knowledge points in condensed text

HEADLINE (大标题 — REQUIRED, render actual Chinese characters):
Choose one:
{headlines}
- Font: 粗黑体, 32–40pt equivalent — fills top 30% of frame width
- Color: {g['headlineColor']}
- Background for headline zone: {g['headlineBg']}

PRODUCT / COMPARISON IMAGE:
{product_image_block}

KNOWLEDGE POINTS (干货 — REQUIRED, render legible Chinese):
{points_block}
- Format: number + 粗体小标 + 1-2 sentence explanation
- Font: regular Chinese body text, 13–16pt
- 3–4pt spacing between points

VISUAL TONE:
- Background: {g['background']}
- Accent color: {g['accentColor']} for point numbers and call-to-action
- Small "收藏备用 ↑" prompt at bottom center (12pt) — this drives save rate

BOTTOM CALL-TO-ACTION:
- "收藏备用，别踩坑" or "看完收藏，省 ¥___" placeholder in small bold text (no specific number)
- Shop name placeholder "[店铺]" at bottom right (≤8pt, low opacity)

AESTHETIC:
- XHS 干货知识帖 style: informative, trustworthy, slightly urgent
- Headline must be scannable at XHS thumbnail size — this is the main click hook
- 3:4 vertical format
- NOT cluttered — generous spacing between sections

DIFFERENTIATION — this is a KNOWHOW/AVOID POSTER, NOT:
- NOT meaningCraftPoster (consumer protection tone, not brand storytelling)
- NOT priceAnchor (topic is quality/authenticity/selection, not price comparison)
- NOT starTestimonial (expertise-driven, not trend/celebrity hook)
- NOT hero or wristNeck (informational poster, not a pure product photo)
- NOT giftScene (practical guidance, not occasion-based transaction)"""


# ─── 12. starTestimonial — 明星同款/玄学种草 ─────────────────────
def _suggest_star_hook(a: dict[str, Any]) -> dict[str, Any]:
    import re

    all_text = (
        f"{a.get('category', '')} {a.get('subcategory', '')} {a.get('design_concept', '')} "
        f"{' '.join(g.get('name', '') + ' ' + g.get('color', '') for g in a.get('gemstones', []))} "
        f"{' '.join(m.get('material', '') for m in a.get('materials', []))}"
    ).lower()

    main_gem = a.get("gemstones", [{}])[0].get("name", "宝石") if a.get("gemstones") else "宝石"
    main_concept = (a.get("design_concept", "")[:25]) or "精工设计，品质保证"
    sub = a.get("subcategory", "首饰")

    if re.search(r"蝴蝶|butterfly|玄学|锁骨链|转运", all_text):
        return {
            "hookType": "玄学/转运",
            "background": "宝石主色系深色渐变底（蝴蝶款→蓝紫渐变，锁骨链→深金渐变）",
            "headlines": ["蝴蝶玄学 | 佩戴就转运", "今年流行戴这条，运气都变好了", "蝴蝶飞来，好事也来"],
            "textColor": "金色或白色，在深色背景上",
            "textPlacement": "左上角从顶部向下，或底部全宽覆盖",
            "subline": "设计师纯手工制作 · 寓意转运招财",
            "badgeText": "玄学爆款 🦋",
            "hashtag": "蝴蝶玄学",
        }
    if re.search(r"hefang|玫瑰|roses|刘|star|项链|necklace|吊坠|pendant", all_text):
        return {
            "hookType": "明星/IP 同款",
            "background": "深玫红/酒红渐变底 or 暗调花园摄影背景",
            "headlines": ["明星同款 · 璀璨项链", "《玫瑰的故事》同款 我也买了", "明星同款 · 同款美丽"],
            "textColor": "白色，在深色背景上",
            "textPlacement": "左上/顶部横排",
            "subline": f"天然{main_gem}镶嵌 · 限量设计",
            "badgeText": "明星同款",
            "hashtag": "明星同款首饰",
        }
    if re.search(r"珍珠|pearl|月光|moonstone", all_text):
        return {
            "hookType": "情绪种草/风格种草",
            "background": "奶白色薄雾背景 or 柔和窗光虚化，呈现梦幻纯净感",
            "headlines": ["她戴上这条，真的太好看了", "纯欲天花板 | 这串珍珠", "从她耳边经过，我就爱上了"],
            "textColor": "深海军蓝 or 深玫粉，在奶白背景上",
            "textPlacement": "底部全宽文字带",
            "subline": "天然淡水珍珠 · 高光泽正圆",
            "badgeText": "纯欲爆款",
            "hashtag": "珍珠首饰",
        }
    if re.search(r"古法|黄金|gold|新中式", all_text):
        return {
            "hookType": "国潮/新中式文化种草",
            "background": "深墨绿底 or 古铜金渐变，质感厚重呼应古法工艺",
            "headlines": ["国风玉人的首饰 就该是这条", "古法黄金 · 戴上就是一种气场", "新中式穿搭 | 这件首饰点睛"],
            "textColor": "香槟金 or 暖白，在深背景上",
            "textPlacement": "左侧竖排或顶部横排",
            "subline": "古法黄金錾刻工艺 · 传承匠心",
            "badgeText": "新中式爆款",
            "hashtag": "古法金首饰",
        }
    return {
        "hookType": "情绪/欲望种草",
        "background": "首饰主色系深色渐变底 or 简约纯色背景，突出首饰本身",
        "headlines": [f"这件{sub}，真的让我心动了", "看到就想要 | 买了后悔少一件", "今年最想入手的首饰，是它"],
        "textColor": "白色 or 金色，在深色背景上",
        "textPlacement": "左上区域或底部文字带",
        "subline": f"{main_concept} · 限量现货",
        "badgeText": "爆款在售",
        "hashtag": "珠宝首饰推荐",
    }


def star_testimonial_prompt(a: dict[str, Any]) -> str:
    lighting_hints = material_lighting_hints(a)
    h = _suggest_star_hook(a)
    headlines = "\n".join(f"  * \"{x}\"" for x in h["headlines"])
    main_mat = (
        a.get("gemstones", [{}])[0].get("name", "")
        if a.get("gemstones")
        else (a.get("materials", [{}])[0].get("material", "") or "精选材质")
    )
    return f"""Generate a JEWELRY STAR/TREND TESTIMONIAL POSTER (明星同款/玄学种草大字报) — a high-impact editorial poster with the jewelry as hero and large trend/celebrity hook text, designed to trigger desire and clicks on Xiaohongshu.

Product: {a.get('category', '')} — {a.get('subcategory', '')}

{product_anchor(a)}

HOOK TYPE: {h['hookType']}

POSTER COMPOSITION:
- Jewelry image occupies 50–65% of frame (centered or slightly right-weighted)
  * Show the full piece on a rich, atmospheric background (NOT a plain white studio shot)
  * Background: {h['background']}
  * Jewelry must catch light dramatically — this is an editorial image, not a product catalog shot
  {lighting_hints}
- Large text block in remaining 35–50% of frame area (left zone, top zone, or overlay at bottom)

LARGE HEADLINE (大字 — REQUIRED, most prominent element in frame):
Choose the most relevant line and render actual Chinese characters:
{headlines}
- Size: 36–44pt equivalent — MUST be legible in XHS feed thumbnail
- Weight: 超粗黑体 or 手写感粗体 — strong visual presence
- Color: {h['textColor']}
- Placement: {h['textPlacement']}

SECONDARY LINE (副文案, smaller, below or near headline):
  * "{h['subline']}"
- Size: 16–20pt, normal weight, same color family as headline
- Adds context/credibility after the hook lands

OPTIONAL ACCENT ELEMENTS:
- Star/celebrity reference badge (if applicable): small white rounded rect, ≤8pt text
  "{h['badgeText']}" — placed near the jewelry or in corner
- Trend hashtag: "#{h['hashtag']}" in small mono text (lower right, ≤10pt)
- Material tag: "{main_mat}" in fine text near image

BACKGROUND TREATMENT:
- {h['background']}
- The background must ENHANCE the jewelry — not compete with it
- Color gradient or solid tone — NO busy patterns or textures that obscure the jewelry

ATMOSPHERIC QUALITY:
- This is an editorial/fashion shoot feel, NOT a plain product shot
- Dramatic lighting on jewelry piece
- The overall composition should feel like a magazine crop or XHS 爆款 封面

AESTHETIC:
- XHS 种草 peak conversion aesthetic: bold, aspirational, culturally resonant
- Headline is the draw, jewelry is the proof
- 3:4 vertical format
- Optional small price tag at corner: "¥___" placeholder in small text — does NOT dominate

DIFFERENTIATION — this is a STAR/TREND TESTIMONIAL POSTER, NOT:
- NOT meaningCraftPoster (cultural/trend hook drives this, not craft education)
- NOT hero (atmospheric editorial background, not a clean isolated studio shot)
- NOT giftScene (trend/desire hook, not occasion/gift framing)
- NOT knowhowAvoid (emotional aspiration, not consumer protection)
- NOT wearStyleGrid (single editorial statement, not a 4-cell outfit matrix)"""


# ─── Registry ────────────────────────────────────────────────────

MARKETING_BUILDERS = {
    "hero": hero_prompt,
    "wristNeck": wrist_neck_prompt,
    "gemCutDetail": gem_cut_detail_prompt,
    "sceneStyleWear": scene_style_wear_prompt,
    "flatLayEditorial": flat_lay_editorial_prompt,
    "moodboard": moodboard_prompt,
    "wearStyleGrid": wear_style_grid_prompt,
    "giftScene": gift_scene_prompt,
    "priceAnchor": price_anchor_prompt,
    "meaningCraftPoster": meaning_craft_poster_prompt,
    "knowhowAvoid": knowhow_avoid_prompt,
    "starTestimonial": star_testimonial_prompt,
}

# Order for output filenames (01_hero.jpg, 02_wristNeck.jpg, ...)
MARKETING_ORDER = [
    "hero",
    "wristNeck",
    "gemCutDetail",
    "sceneStyleWear",
    "flatLayEditorial",
    "moodboard",
    "wearStyleGrid",
    "giftScene",
    "priceAnchor",
    "meaningCraftPoster",
    "knowhowAvoid",
    "starTestimonial",
]

# Photo-realistic templates need a realism constraint suffix.
# Others (posters, grids, infographics) intentionally have stylized text.
PHOTO_TEMPLATES = {
    "hero",
    "wristNeck",
    "gemCutDetail",
    "sceneStyleWear",
    "flatLayEditorial",
    "moodboard",
}

# Templates where the reference image must NOT be sent — they're meant to
# generate from text-only context, otherwise the model anchors to the
# product and ignores the prop/scene/aesthetic guidance.
OMIT_REFERENCE: set[str] = set()  # for jewelry-proper, all keep reference

REALISM_SUFFIX = """

CRITICAL RULES:
- Output MUST be a photorealistic photograph taken by a professional camera.
- Real lighting, real materials, real textures, real depth of field.
- NO cartoon, sketch, or low-quality AI artifacts."""

UNIVERSAL_SUFFIX = """

UNIVERSAL OUTPUT CONSTRAINTS:
- 3:4 vertical format unless explicitly overridden above
- NO watermarks, NO competitor brand logos
- NO fabricated product photos of brands not in the reference image
- Chinese text (if any) must render crisply with correct stroke order

MERCHANT-FILLABLE SLOT POLICY (CRITICAL — do NOT hardcode these):
- Prices: render a BLANK slot or "¥___" / "[价格]" placeholder. NEVER commit to a specific number
  like "¥299" or "¥89-120" — merchants set their own prices and baked-in numbers force regeneration.
- Contact info (WeChat / phone / Taobao handle): leave as blank underline or "[联系方式]" — never
  invent fake IDs or numbers.
- Specific quantitative claims (限量编号 "007/100", 销量 "[X]+", 优惠 "满 ¥___ 减 ¥___"): render as
  placeholder brackets — merchants fill in their real numbers before publishing.
- Celebrity / IP names: avoid direct naming. Use generic "明星同款" / "网红同款" / "人气款"
  if absolutely needed — never paste specific person names.
- Stock counts / urgency ("最后 3 件" / "仅剩 7 件"): skip unless the template's purpose is
  explicitly urgency-based — then leave count as "[X] 件".

The image should LOOK like a finished 爆款 card; the merchant adds their real numbers just before
publishing. Blank slots are a feature, not a bug."""
