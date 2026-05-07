"""8 jewelry design prompts (raw stone → finished design suite).

Ported from shichuan/src/lib/gemini/design-prompt-templates.ts. The `sketch`
template is canonical — its output is the input image for all 7 others, which
guarantees design consistency across the suite.
"""
from __future__ import annotations

from typing import Any
from .helpers import (
    JEWELRY_TYPE_LABELS,
    metal_choice,
    stone_description,
)


def _design_anchor(a: dict[str, Any], jt: str) -> str:
    stone = stone_description(a)
    metal = metal_choice(a)
    settings = {
        "ring": "organic bezel or prong setting that follows the stone's natural shape, flowing asymmetric band with diamond accents on shoulders",
        "pendant": "elegant bail with bezel or prong setting, loop for chain attachment, halo of small diamonds optional",
        "earring": "stud setting with secure post-and-butterfly back, halo of small round diamonds surrounding the main stone",
        "brooch": "secure pin mechanism with decorative frame, organic floral or geometric surround with diamond accents",
    }
    setting = settings[jt]
    gem_specs = "; ".join(
        f"{g.get('name', '')} ({g.get('cut', '')}, {g.get('color', '')}, x{g.get('count', '')})"
        for g in a.get("gemstones", [])
    )
    return f"""PRODUCT: {JEWELRY_TYPE_LABELS[jt]} using {stone}.
DESIGN DETAILS:
- Main stone: {stone}
- Metal: {metal}
- Setting: {setting}
- Accent stones: ~12 small brilliant-cut diamonds (1.2-1.5mm each)
- Overall aesthetic: modern, elegant, feminine luxury
GEMSTONE DATA: {gem_specs or "see reference photo"}"""


def _sketch_reference_prefix(jt: str) -> str:
    return f"""You are looking at a HAND-DRAWN JEWELRY DESIGN SKETCH of a {JEWELRY_TYPE_LABELS[jt]}.
This sketch is the CANONICAL DESIGN — you MUST replicate this EXACT SAME design.
Match the stone shape, setting style, metal color, diamond placement, and proportions EXACTLY.
Do NOT invent a different design. The output must clearly be the same piece as shown in the sketch."""


# ─── 1. sketch — canonical watercolor + pencil ───────────────────
def sketch_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    return f"""Look at the gemstone in this photo. Create a professional HAND-DRAWN JEWELRY DESIGN ILLUSTRATION for a {JEWELRY_TYPE_LABELS[jt]}.

{_design_anchor(a, jt)}

PAGE LAYOUT:
- Top half: large 3/4 angle hero rendering of the {JEWELRY_TYPE_LABELS[jt]}, watercolor + pencil
- Bottom left: side cross-section view (pencil line drawing with mm dimensions)
- Bottom right: top-down view showing stone shape in the setting
- Right margin: small watercolor study of the raw stone itself for color reference
- Handwritten annotations: '{metal}', stone dimensions, setting type
- 2-3 tiny pencil thumbnail variations in margins

RENDERING STYLE:
- Medium: watercolor and gouache on cream textured paper
- Fine pencil linework with sketch quality, visible construction lines
- Gemstones: watercolor wash for transparency, white gouache highlights for light
- Metal: pencil shading + paper left blank for highlights
- Background: cream textured paper with subtle grain
- Small handwritten signature in bottom right corner
- Quality level: Harry Winston / Chopard design house illustration"""


# ─── 2. sketchMulti — pencil engineering blueprint ───────────────
def sketch_multi_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    j_label = JEWELRY_TYPE_LABELS[jt]
    dim_map = {
        "ring": {"height": "Setting height ~12mm", "width": "Stone ~20x10mm", "band": "Band width ~3mm"},
        "pendant": {"height": "Setting height ~15mm", "width": "Stone ~12x10mm", "band": "Bail width ~4mm"},
        "earring": {"height": "Setting height ~5mm", "width": "Stone ~7x5mm", "band": "Post length ~10mm"},
        "brooch": {"height": "Depth ~8mm", "width": "Stone ~15x12mm", "band": "Pin length ~25mm"},
    }
    dims = dim_map[jt]
    return f"""You are looking at a watercolor design sketch of a {j_label}. Your task is to create a completely
DIFFERENT style image: a PURE PENCIL/GRAPHITE TECHNICAL ORTHOGRAPHIC DRAWING of the same piece.

This must look like an ENGINEERING BLUEPRINT, NOT a pretty illustration. Think architectural drawings.

{_design_anchor(a, jt)}

PAGE LAYOUT — 6 EQUAL-SIZED orthographic views arranged in a 3x2 grid:
- ROW 1 LEFT: FRONT elevation (face-on, straight ahead)
- ROW 1 CENTER: SIDE elevation (90° profile, showing height "{dims['height']}")
- ROW 1 RIGHT: TOP plan view (looking down, showing "{dims['width']}")
- ROW 2 LEFT: BACK elevation (reverse side, showing gallery/mechanism)
- ROW 2 CENTER: 3/4 perspective view (the only angled view)
- ROW 2 RIGHT: CROSS-SECTION (cut-through showing internal structure, stone seat depth)

ALL 6 VIEWS MUST BE THE SAME SIZE — no hero image. This is a technical drawing, not art.

DRAWING STYLE — CRITICAL DIFFERENCES FROM A WATERCOLOR SKETCH:
- PURE PENCIL/GRAPHITE ONLY — absolutely NO color, NO watercolor, NO paint
- The gemstone is rendered in GRAY pencil shading ONLY, not colored
- Thin precise linework like a technical pen (0.3mm), not loose brushstrokes
- Heavy use of construction lines: center axes, symmetry lines, projection lines between views
- Dimension annotations on EVERY view: bracket lines with mm values, arrow callouts
- "{dims['height']}", "{dims['width']}", "{dims['band']}" must all appear
- Cross-hatching for shaded areas and cross-sections
- Background: clean white/cream drafting paper
- Title block in bottom right: "{j_label} — {metal}" with scale notation
- Cursive signature below title block

This should look like a PAGE FROM A JEWELRY ENGINEERING TEXTBOOK — precise, technical,
informational — the OPPOSITE of the artistic watercolor sketch it's based on."""


# ─── 3. rendering3d — photorealistic CAD render ──────────────────
def rendering3d_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    return f"""{_sketch_reference_prefix(jt)}

Create a PHOTOREALISTIC 3D RENDERING of the EXACT {JEWELRY_TYPE_LABELS[jt]} shown in this design sketch.

{_design_anchor(a, jt)}

RENDERING:
- Photorealistic CAD-quality rendering, like KeyShot or V-Ray output
- Show the {JEWELRY_TYPE_LABELS[jt]} floating at a 3/4 angle on a pure white background
- {metal} metal with accurate reflections, subtle warm highlights
- The gemstone must show realistic translucency and depth — same color as in the sketch
- Accent diamonds should sparkle with visible fire/dispersion
- Soft shadow beneath for grounding
- Ultra high detail: visible bezel texture, individual prongs for diamonds
- The stone shape, setting style, and proportions must MATCH the sketch exactly
- Quality: Tiffany or Cartier product page level

CRITICAL: This is a 3D render of the SAME design from the sketch, not a new design."""


# ─── 4. wearing — lifestyle wearing photo ────────────────────────
def wearing_prompt(a: dict[str, Any], jt: str) -> str:
    scenes = {
        "ring": "A woman's hand resting elegantly on a marble cafe table, ring on the right middle finger",
        "pendant": "Close-up of collarbone area, cream cashmere V-neck sweater, pendant as focal point on a delicate chain",
        "earring": "Three-quarter profile, hair tucked behind one ear to reveal the earring, soft window light on face",
        "brooch": "Close-up of a silk blouse lapel with the brooch pinned elegantly, soft focus on fabric",
    }
    return f"""{_sketch_reference_prefix(jt)}

Create a LIFESTYLE WEARING PHOTO showing a person wearing the EXACT {JEWELRY_TYPE_LABELS[jt]}
from this design sketch. The piece must look like a real, physical version of the sketched design.

{_design_anchor(a, jt)}

SCENE:
- {scenes[jt]}
- Natural golden hour light from a nearby window
- Nail color: nude/blush pink (if hands visible)
- Outfit hint: cream silk or cashmere, complementing the metal tone
- Soft bokeh background with warm ambient atmosphere
- Xiaohongshu aesthetic: aspirational but authentic

CRITICAL: The jewelry piece must be the SAME design as the sketch — same stone shape, color, setting, proportions. It should look like the sketch was manufactured into a real piece."""


# ─── 5. materialBreak — material constellation ───────────────────
def material_break_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    gem_labels = "\n".join(
        f"  * The raw {g.get('name', '').split('(')[0].split('/')[0].strip()}, lit dramatically (label: '{g.get('name', '').split('(')[0].split('/')[0].strip()}')"
        for g in a.get("gemstones", [])
    )
    return f"""{_sketch_reference_prefix(jt)}

Create a luxury editorial MATERIAL CONSTELLATION for the {JEWELRY_TYPE_LABELS[jt]} shown in this design sketch.

{_design_anchor(a, jt)}

LAYOUT:
- Deep charcoal slate background with subtle texture
- Top center: the finished {JEWELRY_TYPE_LABELS[jt]} matching the sketch design exactly (small, rendered in watercolor style, labeled '成品效果')
- Below, spread with generous breathing space, individual 'ingredients':
{gem_labels}
  * A small pile of loose brilliant-cut diamonds (label: '圆形明亮式钻石')
  * A {metal} band/wire (label: '{metal}')
- Each element sits alone with its own spotlight, like museum specimens
- Labels: thin elegant type, Chinese + English, light grey on dark background
- Chinese labels max 8 characters each

CRITICAL: The finished piece at top must be the SAME design as the sketch."""


# ─── 6. moodboard — Pinterest-style inspiration board ────────────
def moodboard_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    color_names = ", ".join(c.get("name", "") for c in a.get("colors", []))
    return f"""{_sketch_reference_prefix(jt)}

Create a MOOD BOARD / AESTHETIC INSPIRATION BOARD for the {JEWELRY_TYPE_LABELS[jt]} shown in this design sketch.

{_design_anchor(a, jt)}

LAYOUT — collage style, like a designer's Pinterest board:
- A blooming flower in the main stone's color palette (the color inspiration)
- Close-up of {metal} metal surface with warm reflections
- Organic natural forms (vines, leaves, water drops — the form inspiration)
- Morning dew drops on a flower petal (the diamond placement inspiration)
- A small rendering of the SAME {JEWELRY_TYPE_LABELS[jt]} from the sketch (the final design)
- Soft overlapping composition, images bleeding into each other slightly
- Color palette derived from the stone: {color_names}
- Small handwritten notes: '有机曲线', '灵感之源', '自然之美'
- Title in thin serif: 'Design Inspiration | 设计灵感'
- Dreamy, feminine, editorial — like a page from Vogue Jewelry

CRITICAL: The jewelry piece shown must match the sketch design exactly."""


# ─── 7. colorDna — color palette deconstruction ──────────────────
def color_dna_prompt(a: dict[str, Any], jt: str) -> str:
    swatches = "\n".join(
        f"  * {c.get('hex', '#FFFFFF')} watercolor wash — '{c.get('name', '')}' label"
        for c in a.get("colors", [])
    )
    metal = metal_choice(a)
    metal_name = metal.replace("18K ", "")
    return f"""{_sketch_reference_prefix(jt)}

Create a COLOR DNA image deconstructing the color palette of the {JEWELRY_TYPE_LABELS[jt]} in this design sketch.

{_design_anchor(a, jt)}

LAYOUT — horizontal split:
- LEFT (40%): the SAME {JEWELRY_TYPE_LABELS[jt]} from the sketch, rendered in watercolor, resting on soft silk fabric
- RIGHT (60%): a vertical flow of watercolor color swatches:
{swatches}
  * {metal_name} metallic wash — '{metal}' label
  * Diamond sparkle white with prismatic hints — '钻石火彩' label
  Each swatch is a soft painterly watercolor blob that bleeds slightly into the next

STYLE:
- Title at top: '色彩基因 Color DNA' in thin serif
- Background: warm cream paper texture
- Labels: small elegant Chinese text beside each swatch

CRITICAL: The jewelry piece on the left must match the sketch design exactly — same stone, setting, proportions."""


# ─── 8. cad3d — 3D CAD technical render sheet ────────────────────
def cad3d_prompt(a: dict[str, Any], jt: str) -> str:
    metal = metal_choice(a)
    j_label = JEWELRY_TYPE_LABELS[jt]
    gem_rows = "\n".join(
        f"  * \"{g.get('name', '').split('(')[0].split('/')[0].strip()} | 主石 | 1\""
        for g in a.get("gemstones", [])
    )
    dim_hints = {
        "ring": "overall stone width (~20mm), ring height (~12.5mm), band width (~3mm)",
        "pendant": "overall height (~25mm), width (~15mm), bail width (~4mm)",
        "earring": "overall face width (~7mm), post length (~4.5mm), height (~8mm)",
        "brooch": "overall width (~35mm), height (~30mm), pin length (~25mm)",
    }
    return f"""{_sketch_reference_prefix(jt)}

Convert this hand-drawn design into a PROFESSIONAL 3D CAD TECHNICAL RENDER SHEET.
Faithfully reproduce the EXACT SAME DESIGN — same stone shape, setting style, proportions, diamond placement.

PAGE LAYOUT — single image, multi-angle views:
- Background: solid soft teal/sky blue (#7BB5C0), clean and uniform
- 5 views of the {j_label}:
  * TOP-LEFT (LARGEST, ~35%): Front 3/4 view matching the sketch's main angle
  * TOP-RIGHT: Top-down view showing stone and setting from above
  * BOTTOM-LEFT: Side profile with dimension bracket line
  * BOTTOM-CENTER: Back/underside showing gallery and construction
  * BOTTOM-RIGHT: 3/4 view from opposite side

- SPECS TABLE (small white card, upper-right):
  * Header: "计算圆形宝石数量"
  * Columns: 宝石 | 直径 | 数目
{gem_rows}
  * "钻石 | 1.50 | 12"
  * Below: "{metal}倒模重约: 4.5g"

- DIMENSION ANNOTATIONS: {dim_hints[jt]}
  Thin black lines with arrows/brackets, values in mm

3D RENDERING: Photorealistic CAD (RhinoGold/KeyShot level), {metal}, visible diamond facets.

CRITICAL: ALL views must show the SAME design from the sketch."""


# ─── Registry ────────────────────────────────────────────────────

DESIGN_BUILDERS = {
    "sketch": sketch_prompt,
    "sketchMulti": sketch_multi_prompt,
    "rendering3d": rendering3d_prompt,
    "wearing": wearing_prompt,
    "materialBreak": material_break_prompt,
    "moodboard": moodboard_prompt,
    "colorDna": color_dna_prompt,
    "cad3d": cad3d_prompt,
}

# Order for output filenames. sketch comes first because all others depend on it.
DESIGN_ORDER = [
    "sketch",
    "sketchMulti",
    "rendering3d",
    "wearing",
    "materialBreak",
    "moodboard",
    "colorDna",
    "cad3d",
]

# All non-sketch templates take the sketch output as their reference image,
# guaranteeing design consistency. Phase 1: generate sketch. Phase 2: generate
# all 7 dependents in parallel using sketch's output as reference.
DESIGN_DEPS = {
    "sketchMulti": "sketch",
    "rendering3d": "sketch",
    "wearing": "sketch",
    "materialBreak": "sketch",
    "moodboard": "sketch",
    "colorDna": "sketch",
    "cad3d": "sketch",
}
