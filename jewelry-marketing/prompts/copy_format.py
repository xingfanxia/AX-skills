"""Markdown writer for the 6-style copy bundle from the analysis JSON."""
from __future__ import annotations

from typing import Any


STYLE_DESCRIPTIONS = {
    "闺蜜种草": "Bestie Recommendation · 激动口语种草",
    "专业测评": "Expert Review · 理性干货评测",
    "情绪叙事": "Emotional Storytelling · 文学意境叙事",
    "穿搭攻略": "Styling Guide · 搭配场景方案",
    "文化叙事": "Cultural Heritage · 东方美学传承",
    "送礼仪式感": "Gift Ritual · 节日送礼场景",
}


def format_copy_md(analysis: dict[str, Any]) -> str:
    """Convert analysis['copy_bundles'] (6 styles) into a clean markdown doc."""
    lines: list[str] = []

    # ─── Header ──────────────────────────────────────────────────
    cat = analysis.get("category", "")
    sub = analysis.get("subcategory", "")
    brand = analysis.get("brand", "")
    concept = analysis.get("design_concept", "")

    lines.append(f"# {cat} — {sub}")
    if brand and brand != "未知":
        lines.append(f"\n**品牌**: {brand}")
    if concept:
        lines.append(f"\n**设计概念**: {concept}")

    target = analysis.get("target_audience", "")
    if target:
        lines.append(f"\n**目标人群**: {target}")

    scenes = analysis.get("suggested_scenes", [])
    if scenes:
        lines.append(f"\n**适用场景**: {' · '.join(scenes)}")

    story = analysis.get("product_story", "")
    if story:
        lines.append(f"\n**产品故事**: {story}")

    # ─── Material/gemstone summary ───────────────────────────────
    materials = analysis.get("materials", [])
    if materials:
        lines.append("\n## 材质")
        for m in materials:
            line = f"- **{m.get('part', '')}**: {m.get('material', '')}"
            detail = m.get("detail", "")
            if detail:
                line += f" — {detail}"
            lines.append(line)

    gemstones = analysis.get("gemstones", [])
    if gemstones:
        lines.append("\n## 宝石")
        for g in gemstones:
            parts = [
                g.get("name", ""),
                f"切割: {g.get('cut', '')}" if g.get("cut") else "",
                f"颜色: {g.get('color', '')}" if g.get("color") else "",
                f"数量: {g.get('count', '')}" if g.get("count") else "",
                f"镶嵌: {g.get('setting', '')}" if g.get("setting") else "",
            ]
            line = "- " + " · ".join(p for p in parts if p)
            special = g.get("special_effect", "")
            if special and special != "无":
                line += f" · 特殊效果: {special}"
            lines.append(line)

    craft = analysis.get("craftsmanship", [])
    if craft:
        lines.append("\n## 工艺")
        for c in craft:
            lines.append(
                f"- **{c.get('technique', '')}** ({c.get('location', '')}): {c.get('description', '')}"
            )

    care = analysis.get("care_tips", [])
    if care:
        lines.append("\n## 保养建议")
        for tip in care:
            lines.append(f"- {tip}")

    # ─── 6-style copy bundles ────────────────────────────────────
    lines.append("\n---\n")
    lines.append("# 小红书文案 · 6 种风格\n")
    lines.append(
        "**说明**: 6 种风格对应 6 种不同人设的发文角度。商家可根据目标受众挑选 1-3 种交替投放，"
        "或每种风格各发 1 条做 A/B 测试。每种风格内含 5 条标题、5 条卖点、1 篇正文 (300-500字)、5 个标签。\n"
    )

    bundles = analysis.get("copy_bundles", [])
    for i, b in enumerate(bundles, 1):
        style = b.get("style", "")
        desc = STYLE_DESCRIPTIONS.get(style, "")
        lines.append(f"\n## {i}. {style}")
        if desc:
            lines.append(f"_{desc}_\n")

        hooks = b.get("hooks", [])
        if hooks:
            lines.append("### 标题（5 条候选）")
            for j, h in enumerate(hooks, 1):
                lines.append(f"{j}. {h}")

        sps = b.get("selling_points", [])
        if sps:
            lines.append("\n### 卖点")
            for sp in sps:
                lines.append(f"- {sp}")

        post = b.get("post", "")
        if post:
            lines.append("\n### 正文")
            lines.append(f"\n{post}\n")

        tags = b.get("tags", [])
        if tags:
            lines.append("### 话题标签")
            # Strip any leading '#' the model already added so we don't double-up.
            lines.append(" ".join(f"#{t.lstrip('#').strip()}" for t in tags))

    # ─── Footer hint ─────────────────────────────────────────────
    lines.append("\n---\n")
    lines.append(
        "**使用建议**:\n"
        "1. 选标题：每种风格挑 1 条最贴合该篇主题的，配合封面图发布。\n"
        "2. 卖点融入正文：不要干巴列点，把卖点编进故事里。\n"
        "3. 标签策略：每篇 5-10 个标签，混合大词（如 #珠宝）+ 小众词（如 #古法金錾刻）。\n"
        "4. 配图建议：6 种风格分别匹配本 bundle 中的不同营销图（如「闺蜜种草」配 wristNeck 上手图，"
        "「专业测评」配 gemCutDetail 工艺微距，「文化叙事」配 meaningCraftPoster 寓意大字报）。\n"
    )

    return "\n".join(lines)
