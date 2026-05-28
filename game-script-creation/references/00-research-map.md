# Research Plan — game-script-creation skill

**Goal of the skill being built:** A full-loop, genre-agnostic guided workflow that takes a non-professional writer from a vague idea → worldview → story-mainline framework → core theme → character core traits → and then assists them through writing the actual mainline + linear plot, all the way to scene-level script. Must **calibrate to the user's real experience level and adapt scaffolding** (not assume "absolute beginner"). Deepest coverage for 二次元手游 (anime gacha mobile games), but adaptable to all game types.

**Why this research:** To build a skill that genuinely teaches craft (not vague pep talk), the knowledge base must be grounded in real story-craft frameworks, real game-narrative-design practice, and concrete dissection of how successful 二游 actually structure their stories. Each stream below is researched deeply with primary sources, cross-validated, and distilled into a reference file.

## Research rigor (applies to every stream)
- Force web search — do not rely on memory.
- Prefer primary/authoritative sources (craft books by named authors, GDC talks, official dev interviews, wiki story breakdowns) over listicles. Cross-check any claim that drives a recommendation.
- Capture **concrete examples** (named beats, named games, named techniques) — abstractions without examples are useless to a beginner.
- Cite URLs. Flag uncertainty honestly; never fabricate.
- Distill into the reference file: frameworks → when-to-use → concrete example → beginner pitfall. Not a link dump.

## The 8 streams

| # | Stream | Model | Output file |
|---|--------|-------|-------------|
| 1 | Universal story architecture: premise/theme/controlling-idea; structure frameworks (3-act, Hero's Journey/Vogler, Save the Cat, Harmon Story Circle, 起承转合 kishōtenketsu, 7-point, Freytag); conflict/stakes/tension/pacing; vague-idea → logline → spine procedure | sonnet | 01-story-architecture.md |
| 2 | Character craft: want vs need, wound/ghost/lie, arc types (positive/flat/negative), archetypes (Jungian 12, Propp), foils/relationships, character bible; how character ties to theme; character-FIRST design for gacha where characters are the product | sonnet | 02-character-craft.md |
| 3 | Worldbuilding methodology: systematic worldbuilding (geo/history/factions/culture/religion/economy/magic-tech systems), Sanderson's Laws, iceberg principle, internal consistency, worldview-revealed-through-play, worldbuilding-as-procrastination trap | sonnet | 03-worldbuilding.md |
| 4 | Game narrative design (genre-agnostic): how interactive narrative differs from linear media, player agency, embedded vs emergent, environmental storytelling, ludonarrative harmony, linear vs branching, quest/mission structure, main vs side vs character content, narrative-by-genre matrix (RPG/action/VN/roguelike/sim/etc.) | sonnet | 04-game-narrative-design.md |
| 5 | 二游 deep dive A — CN/miHoYo: 原神, 崩坏星穹铁道, 崩坏3, 明日方舟, 鸣潮, 重返未来1999, 战双帕弥什, 少女前线. Dissect 主线 chapter/act structure, character story quests (邀约/伴行), event 限时活动 structure, how new gacha characters are introduced narratively, fragmented worldview delivery (书页/图鉴/语音), version-cycle pacing, writing-team structure & 塌房/consistency risks | opus | 05-erciyuan-cn.md |
| 6 | 二游 deep dive B — JP/KR & gacha tradition: FGO, 蔚蓝档案 Blue Archive, 碧蓝航线 Azur Lane, 公主连结 PriConne, NIKKE, ウマ娘 Uma Musume, 学园偶像大师. Character-first design, bond/絆 episode stories, seasonal/event narrative, main-story vs character-story split, story-heavy vs gameplay-first spectrum; contrast with CN approach | opus | 06-erciyuan-jpkr.md |
| 7 | Writing craft for non-pros + adaptive coaching: scene/sequel (Swain: goal-conflict-disaster / reaction-dilemma-decision), dialogue/subtext/voice, show-don't-tell, POV, pacing/prose rhythm, beginner pitfalls (Mary Sue, info-dump, purple prose, white-room), revision/self-edit, overcoming blank-page paralysis; AND creative-writing pedagogy: how to scaffold/coach across skill levels, plotter-vs-pantser, role of constraints, a skill-level calibration rubric | opus | 07-writing-craft-coaching.md |
| 8 | Game script formats, branching tools, production handoff: how game scripts are formatted (vs screenplay), branching dialogue/choice nodes/flags/state, tools (Twine, ink/inkle, Ren'Py, Yarn Spinner, articy:draft, Celtx), 二游 script delivery format incl. 演出 layer (立绘/表情/背景/BGM cues), localization & 配音 considerations | sonnet | 08-script-formats.md |

## After research
Synthesize → curate reference library → write SKILL.md (the adaptive full-loop workflow) → build worksheet templates + a filled 二游 worked example → self-review against write-new-skill criteria → symlink + commit.

---

## v2 复研究与整合（2026-05-28，Opus 4.8 第二轮）

第一版（Opus 4.7）交付后，做了一次**全量复审 + 二轮深研究 + 整合三个外部 agent 产出**。

**整合的外部产出**（用户提供的三份独立研究/草案）：
1. compass artifact A —— Story-Bible-anchored 7-phase pipeline；character-first vs world-first 的"day-one declaration"；大量具名 dev 引用（Megill / Sasko / Cai Haoyu / Shaoji / Kim Ji-hoon）。
2. compass artifact B —— theme-first controlling-idea gateway；8 框架对照；**主线/角色故事/活动剧情 tri-layer 跨 6 游戏对照表**；硬性篇幅基准；Swain scene-sequel 作原子单位；Emily Short 选择架构分类；10 项修订清单。
3. v2.1 中文 skill 草案 —— 大量**生产/长线运营机制**（Canon 管理、Project State、角色价值栈、版本故事/卡池协同、玩家身份模型、skip-resilient、工作模式选择器、12 项交付）。

**二轮深研究（全部 Tavily-backed，force web search，primary sources，⚠️ 诚实标注不确定）：**
- **Wave 1（补盲案例 + 时效 + 核查）**：① 绝区零 ZZZ（TV 模式翻车→快速透明回应）；② 鸣潮 Wuthering Waves（90% 剧情重写→Rinascita 复盘→主角能动性教训）；③ 2025-26 二游格局（HSR 翁法罗斯伏笔节奏失控、无限暖暖/白荆回廊/重返1999、演出军备竞赛、AI 在叙事生产的边界）；④ **引述核查 + 概念纠正**（Cai Haoyu GDC 2021 部分付费/社区转录；Penacony 伏笔来自 Crunchyroll/Nasu 2024 而非 Kondo；Blue Archive "Vol F" 理由不可考；**character-first/world-first 轴正交于国别**——修正了 ref 06 旧的"中式=world-first"框架；工具时效 Twine 2.12/Yarn Spinner 3.1/articy:draft X/ink in Bloodlines 2）。
- **Wave 2（四种情感工艺 + 两个结构缺口）**：刀（赚来的悲剧/牺牲，Up 蒙太奇 / catharsis / 卖惨·fridging·抽卡矛盾反模式）、笑（七个命名喜剧机制 / tsukkomi-boke / 语调缓冲 / 降智·OOC 反模式）、萌·恋（脆弱时刻 / 亲密要挣得 / 万人迷陷阱 / 角色塌房一致性）、谜（公平伏笔 / 谜题箱陷阱 / 重新语境化 / 长线伏笔节奏）；以及 Emily Short 选择架构、序章 onboarding craft。

**整合产物**：
- 新增 `references/10-emotional-craft.md`（刀/笑/萌·恋/谜 四种情感工艺）。
- 新增 `references/11-production-liveops.md`（Canon/Project State、角色价值栈、卡池协同、玩家身份模型、skip-resilient、版本路线图、演出 scope、12 项交付、工作模式选择器、篇幅基准）。
- 增补 `04`（Emily Short 选择架构 §4.7 + 序章 §5.4 + 4 类游戏速查 §6.11）、`05`（ZZZ §2.9 + 翁法罗斯伏笔节奏 + 鸣潮官方重写/复盘）、`06`（**修正 character-first/world-first 两轴框架**）、`09`（卖惨/fridging/万人迷/降智/抽卡矛盾/谜题箱）、`02`（价值栈 + OOC 一致性指引）、`03`（阵营先于角色的生成顺序）、`08`（2026 工具时效）。
- SKILL.md 整合：工作模式选择器、Canon/Project State、character-first/world-first 表态、篇幅基准、四种情感工艺与选择架构/序章的工位指引、10 项修订清单、reference 索引与完成判据更新。
