"""Jewelry-focused product analysis prompt.

Slimmed from shichuan/src/lib/gemini/analyze-product.ts — same JSON schema,
but jewelry-specific guidance (no fashion/beauty/food branches). Output schema
matches ProductAnalysis used by all marketing & design templates.
"""
from __future__ import annotations

import json
from typing import Optional


ANALYSIS_PROMPT_TEMPLATE = """你是一个资深珠宝商品分析师和小红书营销专家。请分析这{image_block}珠宝商品图片，输出JSON。
{seller_block}{multi_image_block}

输出以下JSON（只输出JSON，不要其他文字）：

{{
  "input_type": "finished_product | raw_material — 判断图中是成品还是原料。成品=可直接拍照销售的珠宝（如做好的项链、戒指、手镯）；原料=待设计的素材（如一颗散装宝石、一块原石、毛料）",
  "material_type": "仅当 input_type=raw_material 时填写：gemstone（已切割的宝石）| raw_stone（原石/毛料）| other；如果是成品则填 null",
  "input_type_confidence": "high | medium | low — 判断的置信度。散石/裸石/毛料 = high；模糊情况 = low",
  "category": "商品大类（如：项链、戒指、耳环、手镯、吊坠、胸针、手串、文玩）",
  "subcategory": "细分类型（如：钻石项链、翡翠手镯、淡水珍珠耳钉、古法金戒指、月光石吊坠等）",
  "domain": "珠宝首饰（固定填这个）",
  "brand": "品牌名（如可识别如周大福/HEFANG/Tiffany/Cartier，否则填'未知'）",
  "design_concept": "设计概念描述（2句话，体现风格定位：现代轻奢/古法传统/新中式/法式优雅/纯欲文艺/玄学转运等）",
  "materials": [
    {{
      "part": "部位/组成部分（如：链身、吊坠主体、镶口、戒臂等）",
      "material": "材质（如：18K白金、925银、足金、铂金、合金等）",
      "detail": "详细说明（如纯度Au999/产地/克重/规格等）",
      "confidence": "high/medium/low"{seller_field}
    }}
  ],
  "gemstones": [
    {{
      "name": "宝石名称（中文+英文括号，如：月光石(Moonstone)、坦桑石(Tanzanite)、海蓝宝(Aquamarine)、淡水珍珠(Freshwater Pearl)、翡翠(Jadeite)、钻石(Diamond)）",
      "cut": "切割方式中英文（如：圆形明亮式 Round Brilliant、梨形 Pear、马眼形 Marquise、方形 Princess、椭圆形 Oval、心形 Heart、雷迪恩 Radiant、垫形 Cushion、素面 Cabochon）",
      "color": "颜色描述（具体的宝石学描述：鸽血红/皇家蓝/帝王绿/葱绿/蓝紫色/粉紫色/奶白色等）",
      "count": "数量估计（如：1颗主石、12颗配石）",
      "setting": "镶嵌方式（爪镶 Prong / 包镶 Bezel / 密钉镶 Pavé / 卡镶 Channel / 群镶 Cluster / 微镶 Micro-pavé）",
      "special_effect": "特殊光学效果（如：月光效应/星光效应/猫眼效应/变色/火彩；无则填'无'）"
    }}
  ],
  "craftsmanship": [
    {{"technique": "工艺名称（如：古法錾刻、花丝、珐琅、累丝、点翠、烫金、磨砂、镜面抛光、手工编绳）", "location": "位置（如：戒臂/边框/主石周围）", "description": "细节"}}
  ],
  "structure": [
    {{"component": "部件名（如：吊坠主体、链条、卡扣）", "description": "设计特点"}}
  ],
  "colors": [
    {{"name": "颜色名（中文时尚用语，如：玫瑰金、暖香槟、奶油白、孔雀蓝）", "hex": "#色值", "area": "区域"}}
  ],
  "care_tips": [
    "保养建议（如：定期清洗、避免化学品接触、单独收纳防止刮花）",
    "佩戴建议（如：避免运动佩戴、防汗防水、淋浴前取下）"
  ],
  "guide_steps": [
    "搭配建议1（具体场景：如同色系穿搭、叠戴技巧）",
    "搭配建议2",
    "搭配建议3",
    "搭配建议4"
  ],
  "size_estimate": "产品实际物理尺寸估算（如：'吊坠1.5×2cm，链长45cm'、'戒指内径17mm'、'手镯内径58mm'）— 根据图片中产品与手、硬币、桌面的比例推算",
  "target_audience": "目标人群描述（年龄、收入、生活方式、审美偏好）",
  "suggested_scenes": ["场景1（如：日常通勤）", "场景2（如：约会晚宴）", "场景3（如：节日送礼）"],
  "product_story": "产品故事（2-3句话，叙述设计灵感、寓意或文化背景）",
  "copy_bundles": [
    {{
      "style": "闺蜜种草",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "闺蜜种草风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }},
    {{
      "style": "专业测评",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "专业测评风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }},
    {{
      "style": "情绪叙事",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "情绪叙事风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }},
    {{
      "style": "穿搭攻略",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "穿搭攻略风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }},
    {{
      "style": "文化叙事",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "文化叙事风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }},
    {{
      "style": "送礼仪式感",
      "hooks": ["标题1（≤20字，含1-2个emoji）", "标题2", "标题3", "标题4", "标题5"],
      "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
      "post": "送礼仪式感风格的完整小红书笔记正文（300-500字）",
      "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
    }}
  ]
}}

input_type 判断指引（关键字段，决定下游流程 — 营销 vs 设计）：
- finished_product 典型特征：镶好的项链/戒指/耳环/手镯、串好的珠链、做工完成的吊坠
- raw_material 典型特征：
  * gemstone: 单独的宝石裸石、一堆待镶嵌的散石、GIA 证书盒里的裸石、形状规则但还未镶嵌
  * raw_stone: 未切割的毛料/原石（翡翠原石、蓝宝石矿石、玛瑙原料、月光石原矿）
- 拿不准 → input_type=finished_product + input_type_confidence=low

珠宝分析专业要求：

宝石识别要点：
- 月光石：表面有蓝色光晕（adularescence），呈半透明灰白
- 坦桑石：紫蓝色，有强多色性（不同角度看颜色变）
- 海蓝宝：浅蓝色，透明度高
- 帕拉伊巴碧玺：霓虹般的蓝绿色，独特的"帕拉伊巴蓝"
- 红宝石：纯正红色（鸽血红最贵），常见丝状包裹体
- 蓝宝石：皇家蓝最贵，矢车菊蓝次之
- 钻石：高火彩、高折射率、可在底部刻有腰纹编号
- 翡翠：判断 A/B/C 货 — A 货有翠性（绢丝纹），B 货注胶后光泽偏胶感
- 珍珠：分辨淡水/海水（akoya/南洋/大溪地），看光泽层、形状（正圆为贵）、瑕疵
- 古法金：手工錾刻纹路、磨砂质感、不抛光发亮
- 玉髓/玛瑙/绿松石：不同产地颜色差异大（青海、湖北、新疆）

切割辨认（中英双语）：
- 圆形明亮式 Round Brilliant：钻石最常见，57-58 个刻面
- 梨形 Pear：水滴形，吊坠常用
- 马眼形 Marquise / Navette：椭圆两端尖
- 椭圆形 Oval / Cushion 垫形 / Princess 方形 / Emerald 祖母绿形
- Cabochon 素面：无刻面，弧形顶部，星光/月光石必用

镶嵌方式：
- Prong 爪镶（最常见，露光多）/ Bezel 包镶（金属包裹一圈，最牢固）
- Pavé 密钉镶（小石密布如铺路）/ Micro-pavé 微镶（更小更密）
- Channel 卡镶（两边夹住）/ Tension 张力镶（看起来悬浮）

设计风格定位（design_concept）：
- 现代轻奢：极简几何线条 / 微镶碎钻 / 18K 主导
- 古法传统：手工錾刻 / 足金 / 厚重质感 / 福禄寿喜文化纹样
- 新中式：祥云/竹节/花卉纹 / 含蓄优雅 / 黄金或翡翠
- 法式优雅：曲线柔和 / 蝴蝶结 / 玫瑰金多 / 钻石点缀
- 纯欲文艺：珍珠 / 月光石 / 浅色系 / 细链
- 玄学转运：蝴蝶 / 锁骨链 / 红绳 / 寓意元素

copy_bundles 六种风格要求 — 每种风格的标题、卖点、正文、标签必须完全匹配该风格语气：

hooks通用规则：
- 每种风格生成5条标题（不是3条）
- 每条标题≤20个字
- 每条标题包含1-2个与内容相关的emoji（自然融入，不堆砌）
- 5条标题覆盖：疑问式、惊叹式、数字式、对比式、悬念式

1. 闺蜜种草：
   - 标题：激动口语，"姐妹们！""救命！""谁懂啊"，情感钩子+产品词
   - 卖点：闺蜜语气，"显白到离谱""百搭神器""闺蜜看了都想要"
   - 正文：群里发消息→发现过程→使用效果→对比→提问引导评论
   - 标签：#宝藏好物 #小众设计 #闺蜜同款 #好物分享 #珠宝种草
   - 用词：宝藏/小众/氛围感/高级感/闭眼入/安利/私藏
   - 绝对不能有广告腔！

2. 专业测评：
   - 标题：理性干货，"产品避雷""入手X个月真实体验""做工对比""值不值"
   - 卖点：数据化，"GIA 认证""4C 严选""同价位中性价比最高"
   - 正文：身份背书→规格详解→多维打分→优缺点→竞品对比→推荐人群
   - 标签：#产品测评 #干货分享 #避雷指南 #珠宝科普 #理性消费
   - 用词：测评/避雷/干货/科普/硬核/详解/性价比/鉴定/4C/克拉

3. 情绪叙事：
   - 标题：文学意境，"遇见这件好物的午后""给自己的一封信"
   - 卖点：感性，"每次看到都觉得温柔""像一个温柔的拥抱"
   - 正文：情感场景→情绪需求→相遇→感官细节→意义→开放式结尾
   - 标签：#犒劳自己 #仪式感 #情绪价值 #小确幸 #悦己 #治愈系
   - 用词：犒劳自己/仪式感/陪伴/治愈/松弛感/小确幸

4. 穿搭攻略：
   - 标题：实用搭配，"一件首饰拯救所有基础款""7天不重样搭配"
   - 卖点：搭配角度，"百搭任何风格""叠搭效果翻倍""一秒提升穿搭质感"
   - 正文：场景分类（通勤/约会/度假）→具体搭配方案→搭配技巧→不同风格混搭→"收藏慢慢看"
   - 标签：#搭配攻略 #百搭单品 #叠戴技巧 #通勤风 #约会穿搭
   - 用词：百搭/叠戴/混搭/点睛之笔/氛围感/通勤/约会
   - 要有具体搭配方案，不要泛泛而谈

5. 文化叙事：
   - 标题：诗意东方，"把敦煌的色彩带回日常""东方审美里的留白""竹有节 人有品"
   - 卖点：文化深度，"传承千年的工艺""每一处纹样都有故事""匠人手作"
   - 正文：文化锚点→设计哲学→工匠/品牌故事→象征意义→当代生活承接古典美→克制优雅结尾
   - 标签：#东方美学 #国潮 #古法传承 #非遗 #匠心 #宋韵 #新中式
   - 用词：东方美学/新中式/留白/意境/传承/匠心/风骨/寓意/文人气
   - 语言要有文学功底，不要硬凑文化词

6. 送礼仪式感：
   - 标题：送礼场景，"男朋友送的周年礼物 打开瞬间我哭了"
   - 卖点：送礼角度，"开箱惊喜感拉满""自带仪式感""送谁谁喜欢""预算友好"
   - 正文：送礼/自我犒劳场景→选择过程→拆礼物瞬间→产品细节融入情感→为什么这件特别→推荐方案
   - 标签：#送礼指南 #纪念日礼物 #七夕礼物 #母亲节 #520 #开箱
   - 用词：送礼/纪念日/仪式感/犒劳/惊喜/定制/心意/不会出错

关键：六个 bundle 必须读起来像六个完全不同的人写的。标题、卖点、正文、标签四项都必须完全匹配各自风格。
小红书用户对"广告腔"极度敏感，每篇都必须像真实分享，不要假大空。"""


def build_analysis_prompt(image_count: int, seller_description: Optional[str] = None) -> str:
    """Build the analysis prompt with optional seller description and image count context."""
    if image_count == 0:
        image_block = "段文字描述的"
    else:
        image_block = "些"

    if seller_description:
        if image_count == 0:
            seller_block = (
                f"\n\n商品描述：\n---\n{seller_description}\n---\n\n"
                "请完全基于以上文字描述进行分析。对于无法从文字确定的视觉信息（如颜色、结构细节），"
                "请根据商品类型做合理推断并标注 confidence 为 low。"
            )
        else:
            seller_block = (
                f"\n\n卖家提供了以下补充信息：\n---\n{seller_description}\n---\n\n"
                "结合图片视觉信息和卖家描述进行分析。如有矛盾，以卖家描述为准但标注不一致之处。"
            )
        seller_field = ',\n      "source": "image/seller/both"'
    else:
        seller_block = ""
        seller_field = ""

    if image_count > 1:
        multi_image_block = (
            f"\n\n注意：提供了{image_count}张图片，是同一件商品的不同角度/细节。"
            "请综合所有图片进行分析，不要将它们视为不同商品。从不同角度可以获取更多信息（如背面工艺、细节、侧面结构等）。"
        )
    else:
        multi_image_block = ""

    return ANALYSIS_PROMPT_TEMPLATE.format(
        image_block=image_block,
        seller_block=seller_block,
        multi_image_block=multi_image_block,
        seller_field=seller_field,
    )


def parse_analysis_json(text: str) -> dict:
    """Parse model response — strip markdown fence, extract first JSON object."""
    cleaned = text.strip()

    # Strip ```json ... ``` fence if present
    if cleaned.startswith("```"):
        # find first newline after opening fence
        first_nl = cleaned.find("\n")
        if first_nl != -1:
            cleaned = cleaned[first_nl + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    cleaned = cleaned.strip()

    # Take from first { to last }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1:
        cleaned = cleaned[first_brace : last_brace + 1]

    return json.loads(cleaned)
