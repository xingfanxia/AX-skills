"""Shared helpers for prompt building. Ported from shichuan/src/lib/gemini/prompts/shared.ts."""
from __future__ import annotations

from typing import Any, Optional


def domain_label(a: dict[str, Any]) -> str:
    """Domain string for prompt — fallback to category."""
    return a.get("domain") or a.get("category") or "珠宝首饰"


def material_lighting_hints(a: dict[str, Any]) -> str:
    """Material-aware lighting instructions. Different materials need different lighting."""
    gem_names = " ".join(g.get("name", "").lower() for g in a.get("gemstones", []))
    mat_names = " ".join(m.get("material", "").lower() for m in a.get("materials", []))
    all_text = f"{gem_names} {mat_names}"

    instructions: list[str] = []

    if any(k in all_text for k in ("钻石", "diamond")):
        instructions.append(
            "For diamonds: use high-contrast spotlight to create rainbow fire/dispersion in facets. Avoid pure soft light."
        )
    if any(k in all_text for k in ("珍珠", "pearl", "akoya")):
        instructions.append(
            "For pearls: single soft directional light. Keep some dark areas for contrast — this reveals the mirror-like luster. Avoid multiple light sources."
        )
    if any(k in all_text for k in ("月光石", "moonstone")):
        instructions.append(
            "For moonstone: angled light to reveal blue adularescence floating inside the stone. Light must enter from the side, not straight on."
        )
    if any(k in all_text for k in ("黄金", "gold", "18k", "古法金")):
        instructions.append(
            "For gold: warm color temperature (3000-4000K). Cool light makes gold look like brass."
        )
    if any(k in all_text for k in ("银", "silver", "铂金", "platinum")):
        instructions.append(
            "For silver/platinum: cool diffused light, controlled highlights to prevent blow-out."
        )
    if any(k in all_text for k in ("坦桑", "tanzanite", "蓝宝石", "sapphire")):
        instructions.append(
            "For colored gemstones: side lighting to reveal faceted brilliance and color depth."
        )
    if any(k in all_text for k in ("翡翠", "jade", "玉")):
        instructions.append(
            "For jade/jadeite: soft even lighting to reveal translucency and internal texture."
        )

    if not instructions:
        return ""
    return "MATERIAL-SPECIFIC LIGHTING:\n" + "\n".join(instructions)


def product_anchor(a: dict[str, Any]) -> str:
    """Brief product description for prompt injection."""
    materials = a.get("materials", [])
    mats = ", ".join(
        f"{m.get('part', '')}: {m.get('material', '')}"
        for m in materials[:3]
    )

    sections = [
        f"PRODUCT: {a.get('category', '')} — {a.get('subcategory', '')}",
        f"DESIGN: {a.get('design_concept', '')}",
        f"MATERIALS (external/visible only): {mats}",
    ]

    gemstones = a.get("gemstones", [])
    if gemstones:
        gems = ", ".join(
            f"{g.get('name', '')} ({g.get('color', '')}, {g.get('setting', '')})"
            for g in gemstones[:3]
        )
        sections.append(f"GEMSTONES: {gems}")

    sections.append(
        "NOTE: This describes the product's external appearance. "
        "Do NOT show internal mechanisms, cross-sections, or exploded views unless the template specifically asks for it."
    )

    return "\n".join(sections)


def constellation_labels(a: dict[str, Any]) -> str:
    """Labels for material constellation — gemstone specimens."""
    lines = []
    for g in a.get("gemstones", []):
        name = g.get("name", "")
        cn_name = name.split("(")[0].split("/")[0].strip()
        en_name = ""
        if "(" in name and ")" in name:
            en_name = name.split("(")[1].split(")")[0]
        special = g.get("special_effect", "")
        special_phrase = f"showing {special}" if special and special != "无" else ""
        lines.append(
            f"  * A {g.get('cut', '')} {en_name or cn_name} {special_phrase}, catching its own spotlight\n"
            f"    (label: '{cn_name}' below, '{en_name}' in smaller text)"
        )
    return "\n".join(lines)


def material_breakdown_labels(a: dict[str, Any]) -> str:
    """Labels for non-gemstone constellations."""
    materials = a.get("materials", [])
    if not materials:
        return "  * Key components from the product, each displayed separately with label"
    return "\n".join(
        f"  * {m.get('material', '')} ({m.get('part', '')}), displayed as an individual specimen\n"
        f"    (label: '{m.get('material', '')}' below, '{m.get('part', '')}' in smaller text)"
        for m in materials
    )


def color_dna_swatches(a: dict[str, Any]) -> str:
    """Color swatches for Color DNA template."""
    return "\n".join(
        f"  * {c.get('hex', '#FFFFFF')} watercolor wash (label: '{c.get('name', '')}')"
        for c in a.get("colors", [])
    )


def detect_jewelry_type(a: dict[str, Any]) -> str:
    """Infer JewelryType from analysis. Returns one of: ring | pendant | earring | brooch."""
    cat = f"{a.get('category', '')} {a.get('subcategory', '')}".lower()
    if any(k in cat for k in ("戒指", "ring", "对戒")):
        return "ring"
    if any(k in cat for k in ("耳环", "耳钉", "耳坠", "耳饰", "earring")):
        return "earring"
    if any(k in cat for k in ("胸针", "胸花", "brooch", "pin")):
        return "brooch"
    # Default — necklace/pendant/bracelet/bangle all fall under pendant for design pipeline
    return "pendant"


JEWELRY_TYPE_LABELS = {
    "ring": "戒指",
    "pendant": "吊坠 / 项链",
    "earring": "耳环 / 耳钉",
    "brooch": "胸针",
}


def metal_choice(a: dict[str, Any]) -> str:
    """Infer metal type from analysis colors."""
    color_names = " ".join(c.get("name", "") for c in a.get("colors", []))
    if any(k in color_names for k in ("暖", "粉", "红")):
        return "18K rose gold"
    if any(k in color_names for k in ("黄", "金")):
        return "18K yellow gold"
    return "18K white gold"


def stone_description(a: dict[str, Any]) -> str:
    """Build a brief stone description for the canonical sketch prompt."""
    gemstones = a.get("gemstones", [])
    if not gemstones:
        return "the gemstone from the reference photo"
    main = gemstones[0]
    parts = [main.get("name", ""), main.get("cut", ""), main.get("color", "")]
    parts = [p for p in parts if p]
    special = main.get("special_effect", "")
    if special and special != "无":
        parts.append(special)
    return ", ".join(parts)
