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
