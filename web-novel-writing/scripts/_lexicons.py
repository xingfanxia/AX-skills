"""
_lexicons.py —— 跨脚本共享的词表【单一真相源】

工程/流水线术语黑名单原本在 output_check.py 与 degeneration_check.py 各抄了一份、且发散
（改一处忘另一处=drift）。按 scripts/README『共享检测逻辑只住一处』，统一放这里，两脚本 import。
两脚本的【职责差异】（output_check=no_prompt_leak 硬门；degeneration_check=meta-leak blocking +
对话行豁免）各自保留，但词表只有一份。
"""

# tier1：纯写作流水线术语，正文里几乎永不合法 → 硬门 / blocking
ENGINEERING_LEAK_TIER1 = (
    r"细纲|卷纲|章纲|情节点|功能标签|目标情绪|字数目标|章首钩子|章尾钩子|"
    r"爽点|毒点|金手指|伏笔池|context_pack|chapter_contract|本章任务|读者爽点|"
    r"must_happen|must_not_happen|sao_payoff|ending_hook"
)

# tier2：章节结构/歧义词，角色在故事内真讨论创作/系统界面用语时可能合法 → advisory
ENGINEERING_LEAK_TIER2 = (
    r"第[一二三四五六七八九十百千万两0-9]+章|本章|这一章|上一章|下一章|上章|下章|"
    r"前一章|后一章|前文|后文|伏笔|读者|任务描述|大纲"
)
