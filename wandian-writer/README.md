# wandian-writer

> 晚点 LatePost 风格中文深度长文 skill — 冷静判断 + 数据先行 + 判断式 header + 段尾落点 + 类比有锚 + 不端一面之词。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Write Chinese long-form deep-dives in the voice of [晚点 LatePost](https://www.latepost.com/) — a respected business/tech publication known for cold judgment, data-first reporting, judgment-style headers, and balanced analysis (always presenting the cost / opposing view, never one-sided cheerleading).

Bundled with `references/fanwen-wandian.md` — an in-context analysis of 6 actual LatePost long-reads with 12 reusable structural patterns. The skill reads this reference before writing.

## When to use

- 行业分析 / 公司或产品拆解 / 趋势观察
- 一线投资人或创业者 observation 专栏
- 技术深度访谈整理
- 政策/新闻深度解读
- "Write me a 3000+ char Chinese industry analysis on X"

## When NOT to use

- Personal experience / 活人感叙事 → use [`khazix-writer`](../khazix-writer/)
- Corporate PR copy → use a different skill
- Short-form content → use a short-form skill

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/wandian-writer ~/.claude/skills/wandian-writer
```

## Coverage

- 5-step writing workflow (research → outline → draft → fact-check → polish)
- 12 structural patterns extracted from 6 LatePost long-reads
- Lightweight mode for short pieces (< 2000 chars)
- L1-L4 self-check pipeline (banned phrases, AI slop, marketing-speak detection)

See [SKILL.md](./SKILL.md) for the full prompting contract and `references/fanwen-wandian.md` for the范文 reference (read before writing).

## Credit

Style profile distilled from public 晚点 LatePost articles. Used here as a writing-style reference, with full credit to the publication and the named authors of each范文. The skill encodes the *style*, not any author's specific opinions.
