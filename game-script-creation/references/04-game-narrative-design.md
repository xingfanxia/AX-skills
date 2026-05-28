# 04 — Game Narrative Design: Genre-Agnostic Architecture
*Reference stream for the `game-script-creation` skill*
*Audience: AI agent guiding a non-professional writer. Be actionable.*

---

## 1. How Game Narrative Differs from Linear Media

Games are not films or novels that happen to have a controller. The differences are structural, and a writer who ignores them will produce story that feels grafted on rather than grown from the game.

### 1.1 The Player as Co-Author

In film, the author controls time, camera, and pace. In games, the player controls at least one of those axes — usually all three. Jesse Schell's foundational framing (*The Art of Game Design*, 2008) is that a designer creates an *experience*, not a text. The story is something that emerges from the interaction between the authored material and the player's choices. This means:

- **Exposition must be earnable, not mandatory.** A player who skips a cutscene has chosen to skip it. If the story only exists in cutscenes, the player can opt out of your story entirely.
- **The player's self-narrative competes with the authored narrative.** Players create meaning from their own actions ("I chose to spare that character") that can conflict with or enrich the written story.
- **Pace is controlled by the player, not the writer.** You can write a tense, urgent scene — and then the player alt-tabs for ten minutes. Narrative tension must be designed to survive interruption.

**Pitfall:** Writing long, unskippable cutscenes that freeze player agency. The player experiences these as punishment for finishing a battle, not as reward.

**Apply:** Make exposition diegetic (dialogue during travel, lore during gameplay) so the player absorbs story while doing something, not while waiting.

### 1.2 The Author-Player Contract

The writer must decide in advance: *How much authorial control am I claiming?* The spectrum runs from:

- **Fully authored protagonist** (Last of Us, BioShock) — the player inhabits a character with a fixed name, voice, and backstory. High narrative coherence, low player identity projection.
- **Defined but mutable protagonist** (Witcher 3, Persona 5) — named protagonist with fixed personality, but player choices shape relationships and endings. Middle ground.
- **Blank slate protagonist** (Elden Ring, most gacha games, older JRPGs) — minimal defined personality so players project themselves. High immersion potential, harder to write compelling character-driven drama.
- **Player as architect** (Dwarf Fortress, RimWorld) — no authored protagonist at all. Story emerges from systems.

The writer's job differs radically depending on where on this spectrum the game sits. A gacha game protagonist is almost always blank-slate; writing must compensate by making *other* characters richly defined.

---

## 2. Jenkins' Four Spatial Narrative Modes

Henry Jenkins' essay "Game Design as Narrative Architecture" (2004) is the foundational text for understanding how games tell stories through *space*, not just text. His core argument: "Game designers don't simply tell stories; they design worlds and sculpt spaces." Narrative in games is spatial before it is textual.

Jenkins identifies four modes — not mutually exclusive, often layered:

### 2.1 Evocative Spaces
The game world **evokes** pre-existing narrative knowledge. The player brings story to the space.

- **What it is:** Spaces that resonate with prior cultural or fictional knowledge (fairy-tale forests, haunted mansions, post-apocalyptic cities). The designer isn't creating narrative from scratch — they're activating it.
- **When to use:** World-building shorthand; establishing tone quickly.
- **Example:** Elden Ring's rotting erdtree visible from everywhere — the player understands "this world is dying" without a line of dialogue.
- **Pitfall:** Relying entirely on evocation produces empty worlds. Evocative space sets mood; it doesn't substitute for authored story beats.

### 2.2 Enacted Stories (Micro-Drama)
The player's movement through space **enacts** narrative actions — the structure of the space *is* the plot.

- **What it is:** The layout of a level tells the story. Corridor → ambush room → environmental clue → revelation room is a story beat sequence encoded in architecture.
- **When to use:** Action sequences, horror encounters, any scene where dramatic structure maps to spatial progression.
- **Example:** The Baker house in Resident Evil 7 — the domestic space warped into threat. Moving through rooms IS the story of discovering what happened.
- **Pitfall:** Enacted stories collapse when players sequence-break or ignore the intended path.

### 2.3 Embedded Narratives
Narrative information is **hidden in the space**, waiting to be uncovered. The game world functions as a "memory palace" the player excavates.

- **What it is:** Lore items, audio logs, NPC dialogue, environmental clues that reward exploration with story. The information exists whether or not the player finds it.
- **When to use:** World-building depth; rewarding curious players; backstory delivery.
- **Example:** Dark Souls item descriptions, BioShock audio logs, Disco Elysium's thoughts encyclopedia.
- **Pitfall:** Too much embedded narrative and the primary story feels thin. Too little and the world feels hollow to explorers.
- **Apply:** Design embedded narrative in concentric circles — inner circle is story-critical (players will find it), middle circle rewards thorough players, outer circle is for lore enthusiasts.

### 2.4 Emergent Narratives
The game's **systems** generate stories unpredictably. No author wrote this specific story — it arose from rule interaction.

- **What it is:** Systemic games (Dwarf Fortress, RimWorld, Crusader Kings) create narrative as a byproduct of mechanics interacting. The designer authors rules, not stories.
- **When to use:** Simulation, survival, management games; roguelikes; sandboxes.
- **Example:** A Dwarf Fortress player's legendary fortress flooding when a berserk miner collapses a dam — no writer scripted this; the systems created it.
- **Pitfall:** Emergent narrative has no guaranteed emotional arc. Players may experience chaos without meaning. Some authored scaffolding (tutorial narrative, win/lose conditions) helps give emergent stories a frame.

---

## 3. Ludonarrative Harmony and Dissonance

Clint Hocking coined "ludonarrative dissonance" in a 2007 blog post about BioShock: the game's *story* preaches collectivism and the danger of selfishness, while its *mechanics* reward the player for choosing the selfish option (harvesting Little Sisters gives more resources). The mechanics undermine the theme.

**Ludonarrative harmony** is the opposite: mechanics *embody* or *reinforce* the thematic content.

### Achieving Harmony

| Game | Theme | How Mechanics Reinforce It |
|------|-------|---------------------------|
| Papers Please | Moral compromise under authoritarianism | You must make immoral choices to survive — the mechanic IS the moral trap |
| Spec Ops: The Line | Cost of violence and heroism myth | The more violence you commit, the more the game's "heroic" framing collapses |
| Celeste | Mental health and self-compassion | Assist mode exists; the game is designed to not punish you for needing help |
| Persona 5 | Rebellion and identity | Social links = building real relationships; dungeon mechanics = confronting repressed psychology |

**Pitfall:** Writing a villain who preaches compassion in cutscenes while the player murders hundreds of enemies with no narrative acknowledgment. This is the most common form of dissonance in action-RPGs.

**Apply:** Before finalizing a game's core mechanic, ask: "What is this mechanic *saying*? What does the player learn about the world by doing this repeatedly for 40 hours?" If the answer contradicts the written theme, either change the mechanic or change the theme.

---

## 4. Branching Narrative Structures

Based on the taxonomy from "Standard Patterns in Choice-Based Games" (Emily Short / Sam Kabo Ashwell, 2015) and industry practice:

### 4.1 Linear (Pure String)
One path. No branches. All story delivery is authored sequentially.
- **Cost:** Lowest. Easiest to QA, write, and localize.
- **Games:** Most early JRPGs, visual novels on single routes, The Last of Us.
- **Pitfall:** Players feel like spectators, not participants. Only works when character drama is compelling enough to sustain the illusion.

### 4.2 String of Pearls (Gauntlet)
Linear throughline with local freedom at each "pearl" — the player explores, but the plot advances in one direction.
- **Cost:** Low-medium. Main story is linear; side content is bounded.
- **Games:** Most gacha games' main stories, Final Fantasy XIII, God of War (2018).
- **Apply:** The gold standard for story-heavy games that need budget control. Keep the main quest pearl-strung; use side content for world depth.

### 4.3 Hub and Spoke
A central hub NPC or location connects to radiating story branches. Player chooses order but usually completes all spokes.
- **Cost:** Medium. Each spoke must be self-contained but connect to hub state.
- **Games:** Mass Effect's Citadel conversations, Dragon Age: Origins origin stories, traditional RPG town NPCs.
- **Apply:** Order-agnostic content (character episodes, companion quests) works perfectly here. The hub is usually the protagonist's home base or a recurring NPC.

### 4.4 Branch and Bottleneck (Foldback)
Branches diverge after choice points but reconverge at mandatory plot beats. Choices affect *how* you arrive at a beat, not whether it happens.
- **Cost:** Medium-high. Each branch needs its own content; bottlenecks must feel earned from any path.
- **Games:** Telltale's The Walking Dead, most Quantic Dream games, Witcher 3 quest resolutions.
- **Apply:** Best for cinematic narrative games that want player agency without exponential content cost. The illusion of consequence is powerful here — players remember their choices more than the reconvergence.

### 4.5 True Branching (Time Cave)
Choices create genuinely divergent paths with separate content and endings.
- **Cost:** Exponential. Each branch doubles content needs. Rarely achievable at AAA scale.
- **Games:** Fate/stay night (3 routes = 3 complete stories), Clannad (6 routes), 80 Days.
- **Apply:** Visual novels can afford this because per-scene production cost is low. AAA games cannot. For non-VN games: reserve true branching for endings only (Mass Effect 3 model, flawed but cost-effective).

### 4.6 Emergent / Floating Modules
No central plot; story emerges from system interaction and accumulated encounters.
- **Cost:** Extremely high content volume required; systems design complexity is very high.
- **Games:** Hades (encounter conversations trigger by game state), Dwarf Fortress, Crusader Kings III.
- **Apply:** Hades' innovation: treat every death as a scheduled story delivery moment. Design for the loop, not the line.

### Key Concept: The Illusion of Choice
Research consensus is that players *remember* choices more vividly than they experience their consequences. In Telltale's Walking Dead, most choices foldback — but players recall them as deeply consequential. This is a design superpower: you can create emotional investment in agency without paying the exponential content cost of true branching. The mechanism is *acknowledgment* — NPCs must verbally confirm they remember your choices, even if the outcome was identical.

### 4.7 Emily Short 的"选择架构"分类（与上面的分支拓扑正交，可叠加）

§4.1–4.6 讲的是**分支拓扑**(故事图的形状)；Emily Short 的分类讲的是**内容如何被选中**——两者正交，可同时使用。对预算有限的二游/独立游戏尤其有用。

- **Storylet / 质量驱动叙事(QBN, Quality-Based Narrative)**：把内容拆成一个个 storylet(一段内容 + 出现的前置条件 + 触发后对状态的改变)；场景按**数值状态(quality)跨过阈值**解锁，而非按"走过哪条分支序列"。Failbetter《Fallen London》靠这个运营 15 年——每段新内容只要嵌进现有 quality 矩阵，**无需重写旧路径**。**对长线二游极契合**：哪怕一个简单的 5 变量系统(对 A/B/C 的好感 + 阵营值 + 故事阶段)就能在线性框架上生成大量"个性化"内容而不组合爆炸。
- **显著性驱动(salience-based)**：系统从一个内容池里**自动挑"当前最相关"的一条**，玩家不显式选择。用于 NPC 环境对白(《求生之路》闲聊、《看火人》无线电)。适合在线性主干上叠一层"环境反应"。
- **路标叙事(waypoint)**：固定"必经的关键节拍(路标)"，**路标之间自由探索/任意顺序**(《Outer Wilds》是典范——谜底固定，但 30+ 信息节点任意顺序发现，系统"不断把故事缝合回来")。
- **反思性选择(reflective choices, Cat Manning)**：**不改变世界状态、只改变玩家"感受"**的选择——表达角色性格、澄清情感、让玩家参与主角的内心。是预算最低的"代入"超能力。**前提**：场景必须已建立足够情感语境，否则它就像没意义的"左还是右"。
- **预算内的"被看见"(reactivity on a budget, Hades 法)**：与其加一条真分支，不如加一句反应性台词。"我记得你救了她"只花一行写作 + 一个旗标判断；一条新分支要花 3 倍内容。**玩家对"被游戏记住"的感受，比对"看不见的分叉"更值钱。** 二游里"角色记得你之前的选择/赠礼/战绩"就是这套思路（详见 ref 11 §5 的"微反应"）。

> 来源：Emily Short — Storylets / QBN https://emshort.blog/2019/11/29/storylets-you-want-them/ ; 选择架构分类 https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/ ; Cat Manning 反思性选择 https://catacalypto.wordpress.com/2018/06/19/successful-reflective-choices-in-interactive-narrative/ ; Hades 反应性叙事 https://www.gamedeveloper.com/design/how-supergiant-weaves-narrative-rewards-into-i-hades-i-cycle-of-perpetual-death

---

## 5. Quest and Mission Architecture

### 5.1 The Three-Quest Tier System

Every narrative-carrying game needs:

1. **Main Quest (Critical Path):** The spine. Must be completable solo. Carries the primary theme, the protagonist's core arc, and world-stakes conflict. Chunked into chapters/acts to create pacing rhythm and save points.

2. **Side Quests / World Quests:** Optional but should illuminate the world and theme from oblique angles. The best side quests in Witcher 3 are complete short stories that happen to intersect with the main world — they don't just give XP, they argue for the game's themes from unexpected directions.

3. **Character Quests (Companion/Bond Stories):** Deepening content focused on specific characters. Often the most emotionally resonant writing in the game because the reader already cares about the character. Persona's social links, Dragon Age companion quests, gacha character episodes.

### 5.2 Quest as Story Beat

A quest is a story beat with gameplay attached. It should have:
- **Inciting trigger** (NPC asks for help, world event detected)
- **Complication** (the obvious solution doesn't work / reveals something worse)
- **Climax** (player action determines outcome)
- **Resolution** (consequence acknowledged in world state, ideally with NPC follow-up)

The failure mode is quests that are: trigger → go here → kill thing → return. No complication, no emotional consequence, no world acknowledgment.

### 5.3 Pacing: Chapter Chunking

Games chunk main story into chapters not just for save-state reasons — chapters are breathing architecture:
- **Chapter opening:** Re-establish stakes, recap where we are, introduce chapter-specific threat
- **Chapter body:** Escalation through missions, with rest beats (town visits, relationship dialogue, non-combat exploration) interspersed
- **Chapter close:** Climax event + revelation that changes the protagonist's situation for the next chapter

**Pacing ratio:** AAA narrative games typically target 60-70% gameplay, 15-20% cutscene/dialogue, 10-15% exploration/incidental. Gacha games invert this for story chapters: heavy text/VN presentation with lighter combat gating.

### 5.4 开场一小时 / 序章叙事（onboarding craft）

第一次会话决定玩家有没有第二次。二游尤其致命：序章常**一口气甩五个阵营、十二个专名、一套宇宙观和"世界危机"**——可玩家还没有理由在乎任何角色。理解需要记忆，记忆需要在乎，在乎需要一个**人**。鸣潮 1.0、白荆回廊前两章、HSR 翁法罗斯 3.0 都栽在这（见 ref 05 §2.2/§2.5、ref 11 §10）。

**开场处方（按顺序）**：
1. **先给一个值得在乎的"人"**——前 5 分钟一个角色、一个具体问题。不是世界，是一个人。
2. **给一个具体张力**——一个具体、迫在眉睫的威胁/疑问，不是泛泛的"世界有难"。
3. **给一个清晰的下一步**——玩家接下来做什么、为什么这对那个角色重要。
- **先点名敌人，再点名世界**："她正冲我们来"先于"游荡之潮使回声共鸣框架失稳"。威胁在前，专名在后。
- **In-medias-res(入场即动作) vs 慢热**：前者适合"动作本身无需背景也读得懂情绪"(《尼尔:机械纪元》开场即战斗)；后者适合"先把开场关系做到动人，再揭世界复杂度"(早期原神靠空/荧兄妹失散撑起 30 分钟世界观)。最差是"开场即动作、却需要没解释的设定才看得懂"——多数被骂的二游序章正是这种。

**教学即叙事(tutorial-as-narrative)**：用**后果**教规则，不用讲座。"按 A 闪避，闪避减伤"是说明书；让导师角色**因为没闪避而受伤/牺牲、玩家亲眼目睹**，世界规则(闪避=活命)就被赋予了情感重量(《传送门》GLaDOS 边教边塑造角色是范例)。二游序章常用一个**不是主角的可玩角色**(导师/老兵)在教完机制后离场或牺牲——既用有性格的角色教了机制，又在赌注到来前建立情感投资(HSR 序章用姬子作向导即此结构)。

> 来源：Microsoft Research "The First Hour Experience" https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/First20Hour20-20CHIPlay20201420-20preprint2.pdf ; 教学即叙事 https://www.meegle.com/en_us/topics/game-design/tutorial-narrative-integration ; 翻车案例交叉引用 ref 05 §2.5(鸣潮)

---

## 6. THE BY-GENRE NARRATIVE MATRIX

This is the primary deliverable for the skill. For each genre: how narrative is structured, how much story it carries, where main and side lines live, and the writer's primary job.

---

### 6.1 JRPG / Turn-Based RPG
**Examples:** Final Fantasy series, Persona series, Dragon Quest, Trails series, Xenoblade

**Narrative delivery:** Primarily through cutscenes, voiced/text dialogue, scripted events between and after battles. Story is front-loaded and back-loaded around chapters; combat is the pacing mechanism between story beats.

**Linear vs. branching:** Typically linear to very lightly branching main story (string of pearls). The Persona series adds hub-and-spoke (social links) that branch into character-focused stories while the main dungeon path remains linear.

**Main line:** A clear protagonist journey with defined acts and escalating world stakes. Usually 30-60 hours of primary content. Cutscenes are cinematic and lengthy.

**Side line:** Side quests (optional combat challenges, NPC help), character quests (companion-specific stories that often explore the chapter's theme from a personal angle), exploration-based lore gathering.

**Writer's primary job:** Character writing. JRPG players bond with party members, not just protagonists. The ensemble cast must be individually distinct, with personal arcs that develop in parallel with the main plot. Secondary job: theme coherence — JRPGs often carry ambitious themes (identity, fate vs. free will, found family) that must be expressed consistently across 50+ hours of content.

**Pitfall:** Over-relying on cutscenes. Players who love the game forgive long cutscenes; players who don't bounce off them and never return. Persona 5's UI design makes even menus feel narratively charged — model this.

**Gacha-adjacent note:** Many gacha games (especially CN/JP 二次元 titles) model their main story structure on JRPG conventions. Writers from JRPG backgrounds adapt well to gacha.

---

### 6.2 Action-RPG / Open World
**Examples:** Witcher 3, Elden Ring, Red Dead Redemption 2, Horizon series, Cyberpunk 2077

**Narrative delivery:** Mixed. Scripted story missions (cutscene-heavy), environmental storytelling (item descriptions, world state), incidental NPC dialogue, discoverable lore (journals, audio logs), ambient world narrative.

**Linear vs. branching:** Main quest is typically linear with consequence branching at key decision points (Witcher 3's ending branches). Open world creates an *illusion* of narrative freedom — the world exists simultaneously but story missions progress linearly when accessed.

**Main line:** Chunked into acts, often with a hub region per act. Player accesses missions in any order within act constraints.

**Side line:** Where the best writing often lives. Witcher 3's Blood Baron quest is a complete tragedy-in-miniature that exceeds most AAA main stories in craft. Side quests in open worlds should be self-contained short stories, not fetch errands.

**Writer's primary job:** World coherence. Every region, faction, and NPC must feel like it existed before the player arrived. Environmental narrative must reward exploration without requiring it for main story comprehension. Secondary job: quest design — making optional content feel worth the player's time.

**Pitfall:** Open-world bloat. "Checklist" quest design (kill 10 wolves) destroys narrative credibility. Quantity of markers does not equal narrative richness.

**Apply:** The Witcher 3 standard — every side quest should have a specific NPC with a name, a problem that has context, and a resolution that changes something. Avoid anonymous quest givers.

---

### 6.3 GACHA / 二次元手游 (DEEP-FOCUS GENRE)
**Examples:** Genshin Impact, Honkai: Star Rail, Arknights, Fate/Grand Order, Azur Lane, Blue Archive, Reverse: 1999, Girls' Frontline

**Overview:** Gacha games are the most narratively complex mobile game genre because they must sustain story delivery across years of live-service operation, across multiple content types simultaneously, while constantly introducing new characters tied to monetization.

**Narrative delivery layers (critical to understand all of them):**

#### Layer 1 — Main Story (主线剧情 / メインストーリー)
- The spine of the game's world narrative. Delivered in chapters, often with full voice acting.
- Structure: String of pearls — each chapter is a self-contained arc within an overarching world threat.
- Pacing: CN gacha norms: ~3-6 months between major chapters. Each chapter typically 4-8 hours of content.
- Writer's job: World stakes, faction politics, protagonist growth. Must be accessible to players who joined at any chapter. Each chapter must introduce new readers while rewarding veterans.
- **Key technique:** Arknights delivers main story in "Episodes" with self-contained arcs (Lungmen political crisis in Ch. 7-8, Babel backstory in Prelude to Ch. 9) that interlock into an overarching dystopia narrative. Each episode can be read standalone but gains depth from the whole.

#### Layer 2 — Character Stories / Bond Episodes (角色故事 / キャラクターストーリー)
- Unlocked by raising character bond/affection level (typically via pulling the character and spending in-game currency to level the bond).
- Structure: Hub-and-spoke. Each character has 3-6 episodes covering their backstory, present motivations, and relationship with the player.
- Writer's job: These are the most personal writing in the game. Players who pull a character invest emotionally. Bond episodes must deliver on the character's appeal archetype while adding complexity. Avoid revealing everything in the gacha banner's introduction — save reveals for bond content.
- **Example:** Honkai: Star Rail character stories develop characters introduced in main story into full emotional portraits. March 7th's bond story recontextualizes her cheerful affect as a coping mechanism — the main story cannot carry this; only the intimate bond episode structure can.

#### Layer 3 — Event Stories (活动剧情 / イベントストーリー)
- Time-limited story content tied to banners and seasonal events. The most varied writing format in gacha.
- Structure: Ranges from full-chapter main story expansions to short VN vignettes. Typically 1-4 hours of content.
- Function: (a) Introduce upcoming characters before their banner to create emotional investment; (b) Expand lore for existing characters; (c) Seasonal/holiday content for fan service and relationship deepening; (d) Crossover events (especially FGO/collab-heavy games).
- Writer's job: Create a complete emotional beat within 1-4 hours. Must be accessible to players who missed prior events (since events are often removed from the game after they end). Strong hook in the first 10 minutes. Character-focused rather than world-stakes.
- **Critical constraint:** Event stories are tied to monetization. The character being featured in the event's banner must appear compellingly in the story — but the story cannot feel like an advertisement. The craft is creating genuine emotional stakes around a character the player is being asked to spend money on.

#### Layer 4 — Banner Introduction / Gacha Character Reveal Stories (角色PV / 自我介绍)
- Short (2-10 minute) voiced vignettes introducing a new banner character.
- Structure: Usually a single scene or sequence that establishes the character's personality, voice, and hook.
- Writer's job: First impression. In 2-10 minutes, establish: (a) who this character is; (b) why they're compelling; (c) what emotional need they fulfill for the player. This is pure character hook writing. Avoid world-stakes — focus entirely on personality and relationship potential.
- **Example:** Blue Archive excels here — teacher-student character intros establish relationship dynamic and archetype within minutes, giving players immediately clear "this is my type / not my type" reads.

#### Layer 5 — Incidental Dialogue (日常对话 / ホーム会話)
- Short voiced lines triggered by player interactions on the home screen, in menus, or during combat.
- Writer's job: Voice consistency and fan-service. These lines are repeated hundreds of times; they must be charming without becoming grating. They reinforce the character's archetype established in bond stories.

**The gacha writer's unique constraints:**

1. **Long tail writing:** You are writing a character whose story will unfold across 2-5 years. Establish character clearly but leave room for growth. Avoid resolving character arcs prematurely — save the big reveals for anniversary events.

2. **Banner cadence:** New characters release every 3-4 weeks. Each must feel distinct. Establish a character bible at project start and maintain strict consistency across writers.

3. **The pull-incentive tension:** Story that makes players care deeply enough to spend money, without feeling like manipulation. The ethical and craft solution: write stories that stand independently as good fiction. Players will pull because they love the character, not because the story pressured them.

4. **Accessibility for new players:** Main story in a 3-year-old gacha has 60+ hours of prior content. Each new chapter must briefly re-establish context. Use recurring characters as orientation anchors.

5. **Community engagement:** Gacha player communities read every line intensely and cross-reference across all content layers. Continuity errors become viral criticism. Maintain a detailed lore bible.

**Pitfall:** Writing every new character as a variant of existing popular archetypes (the stoic warrior, the cheerful airhead, the tsundere). Gacha players are sophisticated and recognize archetype recycling immediately. The craft is finding the *specific* version of an archetype that feels fresh.

---

### 6.4 Visual Novel / Story-Rich
**Examples:** Fate/stay night, Clannad, 13 Sentinels, Nier: Automata (hybrid), Disco Elysium, Ace Attorney

**Narrative delivery:** Text-first, with voice acting, CG illustrations, and music as emotional amplifiers. Story is the product; gameplay is minimal (choices, light puzzles, investigations).

**Linear vs. branching:** Highly variable. Fate/stay night has 3 complete routes (true branching — ~50 hours total). Clannad has 6 routes. Ace Attorney is essentially linear with investigation mechanics. Disco Elysium is quasi-branching with heavy systemic choice.

**Main line:** The route structure IS the main line. Often there is a canonical "true" route unlocked after completing others (Fate/stay night's Heaven's Feel, Clannad's After Story).

**Side line:** Bonus CGs, replay with different choices, unlockable side scenes.

**Writer's primary job:** Prose quality, dialogue, and emotional arc. There is nowhere to hide — the writing IS the product. Every line must earn its place. The writer controls pacing completely (the reader advances text at will). Use this control: vary sentence rhythm, use silence/white space, earn the emotional beats.

**Pitfall:** Overwriting. Visual novel writers, freed from page/time constraints, often write 3x as much as the scene requires. Kill your darlings. Readers will skip text that doesn't move the story or character forward.

---

### 6.5 Roguelike / Roguelite
**Examples:** Hades, Dead Cells, Slay the Spire, FTL, Binding of Isaac, Returnal

**Narrative delivery:** Varies enormously. FTL and Slay the Spire: embedded narrative through cards/events, minimal authored story. Hades: authored story delivered across runs through NPC conversation, with death as the narrative engine. Returnal: surrealist environmental narrative.

**Linear vs. branching:** By necessity, narrative is modular and non-linear. The player experiences content in random order across multiple runs. Think floating modules and loop-and-grow structures.

**Main line:** Does not exist in the traditional sense. Instead: a *progression of revelations* — the player learns more world lore and character context as they accumulate runs. Story gates unlock based on run count or boss completions, not linear chapter progression.

**Side line:** Every run IS a side story. Encountering a specific event, finding a specific item, or triggering a specific NPC conversation IS the story delivery.

**Writer's primary job:** Writing for repetition. Every line of NPC dialogue must work on the 1st encounter, the 10th, and the 50th — because the player will hear it many times. Hades solved this with massive dialogue variation pools (Greg Kasavin: "fill the game with unnecessary, pointless things — you cannot predict which details resonate"). Write dialogue that rewards re-listening: early lines gain new meaning once the player understands the full story.

**Hades' specific technique:** The "encounter memory" system — every time the player meets a boss, the boss acknowledges how many times they've fought and who won. This turns mechanical repetition into narrative continuity.

**Pitfall:** Writing a roguelike story that requires the player to experience events in order. They won't. Design for non-sequential discovery; add context-awareness flags to dialogue to prevent impossible ordering.

**Apply:** Write NPC conversation pools with at minimum 5-10 variations for high-frequency interactions. Index by context state (first meeting, 3+ meetings, player just died to this boss, etc.).

---

### 6.6 Action / Shooter (Single-Player Story)
**Examples:** Half-Life 2, BioShock, Doom Eternal, Control, Spec Ops: The Line

**Narrative delivery:** Environmental storytelling, audio logs/lore items, scripted setpieces, incidental NPC dialogue during combat, minimal cutscenes. The genre tradition is of *show-don't-tell* — the player moves through the story rather than watching it.

**Linear vs. branching:** Almost always linear. The shooter loop (encounter → clear → advance) demands forward momentum that branching disrupts.

**Main line:** Tight linear progression. Story beats are paced between combat encounters as relief/reward. The player encounters the story through combat, not despite it.

**Side line:** Collectible lore (audio logs, notes, environmental clues), optional exploration rooms with embedded narrative.

**Writer's primary job:** Environmental narrative and subtext. The best shooter stories are never told directly — they're assembled by the player from what they see, hear, and discover. BioShock's Rapture is a story told entirely through architecture, decay, and audio recordings. The writer works closely with level designers to ensure spatial storytelling is coherent.

**Pitfall:** Exposition dumps via radio chatter during combat. Players are managing threat — they cannot process story information while being shot at. Save complex exposition for quiet rooms.

**Apply:** Use audio logs sparingly — they must be short enough to complete before the player re-enters combat. Environmental storytelling (a family photo, a wheelchair, a barricade) is infinitely cheaper and more effective.

---

### 6.7 Simulation / Management
**Examples:** Dwarf Fortress, RimWorld, Stardew Valley, Crusader Kings III, Spiritfarer

**Narrative delivery:** Primarily emergent (systemic). Some games add authored story beats (Stardew Valley's seasonal events, Spiritfarer's character departure scenes).

**Linear vs. branching:** Inapplicable for pure simulation; authored segments are usually linear vignettes within an emergent sandbox.

**Main line:** Often absent. The player creates their own main line through play (the story of how their colony survived the first winter, the saga of their king's dynasty).

**Side line:** Authored character events (Stardew Valley friendship stories, Spiritfarer character arcs) that trigger at specific relationship milestones. These function like gacha character episodes — each character has a defined story arc that unfolds over time.

**Writer's primary job:** Writing character vignettes that feel emotionally complete within brief, triggered encounters. Also: writing text-based events (Crusader Kings III's event cards) that create memorable stories in 2-3 sentences. Compression is the core skill.

**Pitfall:** Over-scripting emergent games. Spiritfarer's authored character departure scenes work because they're at relationship endpoints — the player has spent hours with the character by then. Forcing authored beats too early breaks the emergent immersion.

---

### 6.8 Puzzle Games
**Examples:** Portal series, The Witness, Return of the Obra Dinn, Her Story, Storyteller

**Narrative delivery:** Highly varied. Portal: comedic character voice-over during puzzle completion. The Witness: environmental philosophy quotes, no plot. Obra Dinn: detective narrative assembled through discovery. Her Story: fragmented FMV that the player reassembles.

**Linear vs. branching:** Puzzle solutions are usually deterministic; narrative may branch around solution discovery.

**Main line:** For narrative puzzles (Obra Dinn, Her Story): the puzzle IS the story — solving the puzzle IS reading the story. For atmospheric puzzles (The Witness): minimal or entirely environmental.

**Writer's primary job:** In comedy puzzle games (Portal), the writer creates a character relationship (GLaDOS/player) that makes the player laugh while solving. In detective puzzles, the writer must construct a mystery that is solvable from available evidence — every narrative element is also a clue. Precision is paramount.

**Pitfall:** In detective puzzle games: hiding necessary information, making clues too obscure, or making the solution logically impossible without prior knowledge. The writer must solve their own mystery, then work backward to plant fair clues.

---

### 6.9 MOBA / Competitive (Lore Without Campaign)
**Examples:** League of Legends, DOTA 2, Overwatch, Valorant

**Narrative delivery:** Entirely external to gameplay — lore via champion bio pages, comic series, short stories, animated cinematics, limited seasonal events, spin-off games (Runeterra, Legends of the Fallen, Arcane).

**Linear vs. branching:** Not applicable. The live game has no narrative throughline. Lore exists in parallel media.

**Main line:** Franchise mythology, not in-game campaign. A player who only plays the competitive game receives no narrative.

**Side line:** Everything is side content from a competitive standpoint, but from a lore standpoint, the comics/shorts ARE the main content.

**Writer's primary job:** World-building and character design that is compelling enough to inspire players to seek out lore *voluntarily*. Characters must be interesting enough in-game (through voice lines, visual design, personality cues) that players want to know their backstory. The competitive game is a perpetual advertisement for the lore.

**Apply:** Every playable character needs: a core personality expressible in 3 voice lines, a relationship to at least 2 other characters in the roster, and a narrative hook (what do they want? what secret are they hiding?) that invites further exploration.

**Pitfall:** Retconning established lore to accommodate new champions, making the universe feel incoherent to dedicated lore readers. Maintain a central canon document with strict gate-keeping.

---

### 6.10 Survival / Sandbox
**Examples:** Minecraft, The Long Dark, Green Hell, Subnautica, Don't Starve

**Narrative delivery:** Mostly emergent. Authored story elements (Subnautica's full narrative arc, The Long Dark's Wintermute campaign) exist as an optional overlay on a fundamentally emergent base.

**Linear vs. branching:** Authored campaigns are typically linear within an otherwise open world. Subnautica's main story progresses through environmental discovery — players find story by exploring, not by following a quest marker.

**Main line:** For pure sandboxes (Minecraft), none. For survival games with authored content (Subnautica), the main line is environmental discovery-gated — key story beats unlock as the player explores deeper regions.

**Writer's primary job:** Creating a survival world that feels like it has a history — like people lived and died here before the player arrived. Environmental storytelling and found-text (journals, logs, distress signals) carry the burden of implied narrative. The writer creates backstory that the player discovers, not story that the player watches.

**Pitfall:** Making story content feel mandatory in a genre where player freedom is the contract. Subnautica's solution: story discoveries are never required to survive, but they recontextualize everything the player has experienced and motivate endgame exploration.

---

### 6.11 其余类型速查（adapter quick-table — 未在上面单列的类型）

下面四类未单列深拆，给一行式适配表（叙事核心单位 / 关键风险 / 核心文档），需要时再展开。其余如 视觉小说 / JRPG / 开放世界 / Roguelike / 模拟 / 解谜 / MOBA / 沙盒 已在 §6.1–6.10 详述。

| 类型 | 叙事核心单位 | 关键风险 | 核心文档 |
|---|---|---|---|
| **策略 / 4X**（文明 / 战棋 / 全战） | 阵营、战役、外交、科技树 | 阵营同质化；剧情跟不上系统（玩家自己生成的叙事盖过作者写的） | 阵营圣经、战役脚本、事件卡池（CK3 式事件卡） |
| **恐怖**（生存恐怖 / 心理恐怖） | 信息控制、脆弱感、未知 | **解释太多 → 恐怖失效**；节奏疲劳（一直紧绷会麻木） | 恐怖节拍表、信息释放表、怪物规则（何时让玩家看清 / 永远不让看清） |
| **MMO** | 区域、职业、阵营、团队副本 | 玩家不是唯一主角，个人化困难；区域剧情各自为政 | 区域故事线、职业任务、世界事件表、阵营冲突圣经 |
| **卡牌 / TCG** | 卡牌 flavor 文本、阵营关键词、套牌主题 | 卡牌 lore 零散、机制与世界无关（贴皮） | 卡牌文本规范、阵营关键词表、扩展包主题圣经 |

> 恐怖的核心铁律值得单记：**恐惧来自未知，解释是恐惧的解药**——给规则，但永远留一块不解释的暗处（参 ref 03 软魔法 + ref 10 谜的"留白"）。4X / MMO / 沙盒大量依赖**涌现叙事**（见 §2.4、§6.7），作者写的是"规则与事件卡"，不是"一条线"。

---

## 7. Cross-Genre Principles for the Skill

Regardless of genre, these principles apply to all game writing:

1. **The player cannot be confused about what to do next, even if the world is emotionally complex.** Narrative complexity ≠ mechanical ambiguity.

2. **Every mechanic makes a statement.** Before writing, ask: "What does the player learn about this world by doing [core mechanic] for 40 hours?" The answer is your theme whether you planned it or not.

3. **Environmental storytelling scales; cutscenes don't.** A destroyed building tells a story to every player who passes it. A cutscene can only be watched, not discovered.

4. **Repetition is the enemy in authored content, the ally in systemic content.** Authored dialogue and cutscenes lose power on repeat exposure. Systemic events (Crusader Kings III's event cards, Hades' encounter dialogue) gain richness through accumulated context.

5. **The player must feel their choices matter, even when they don't.** Acknowledgment by the game world — an NPC mentioning your past choice, a small world-state change — costs little to implement and pays enormous emotional dividends.

6. **Write to the player's curiosity, not their patience.** Give players reasons to seek out your embedded narrative; never force it on them.

---

## Sources

- Jenkins, Henry. "Game Design as Narrative Architecture" (2004). PDF: [https://paas.org.pl/wp-content/uploads/2012/12/09.-Henry-Jenkins-Game-Design-As-Narrative-Architecture.pdf](https://paas.org.pl/wp-content/uploads/2012/12/09.-Henry-Jenkins-Game-Design-As-Narrative-Architecture.pdf). Full text also at [ResearchGate](https://www.researchgate.net/publication/238654339_Game_Design_as_Narrative_Architecture).

- Hocking, Clint. "Ludonarrative Dissonance in BioShock" (2007). Wikipedia summary: [https://en.wikipedia.org/wiki/Ludonarrative_dissonance](https://en.wikipedia.org/wiki/Ludonarrative_dissonance). Academic analysis: [https://www.fredericseraphine.com/index.php/2016/09/02/ludonarrative-dissonance-is-storytelling-about-reaching-harmony/](https://www.fredericseraphine.com/index.php/2016/09/02/ludonarrative-dissonance-is-storytelling-about-reaching-harmony/)

- Ashwell, Sam Kabo. "Standard Patterns in Choice-Based Games" (2015): [https://heterogenoustasks.wordpress.com/2015/01/26/standard-patterns-in-choice-based-games/](https://heterogenoustasks.wordpress.com/2015/01/26/standard-patterns-in-choice-based-games/)

- Kasavin, Greg (Supergiant Games). "Roguelikes and Narrative Design with Hades Creative Director Greg Kasavin" — GDC Podcast Ep. 16: [https://gdconf.com/article/roguelikes-and-narrative-design-with-hades-creative-director-greg-kasavin-gdc-podcast-ep-16/](https://gdconf.com/article/roguelikes-and-narrative-design-with-hades-creative-director-greg-kasavin-gdc-podcast-ep-16/)

- Game Developer. "How Supergiant Weaves Narrative Rewards into Hades' Cycle of Perpetual Death": [https://www.gamedeveloper.com/design/how-supergiant-weaves-narrative-rewards-into-i-hades-i-cycle-of-perpetual-death](https://www.gamedeveloper.com/design/how-supergiant-weaves-narrative-rewards-into-i-hades-i-cycle-of-perpetual-death)

- Schell, Jesse. *The Art of Game Design: A Book of Lenses* (3rd ed., 2019). Routledge: [https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059](https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059)

- Game Developer. "The Evolution of Video Games as a Storytelling Medium": [https://www.gamedeveloper.com/design/the-evolution-of-video-games-as-a-storytelling-medium-and-the-role-of-narrative-in-modern-games](https://www.gamedeveloper.com/design/the-evolution-of-video-games-as-a-storytelling-medium-and-the-role-of-narrative-in-modern-games)

- Inkle Studios. "ink — the narrative scripting language": [https://www.inklestudios.com/ink/](https://www.inklestudios.com/ink/). GDC Vault talk on ink and 80 Days: [https://gdcvault.com/play/1023221/Ink-The-Narrative-Scripting-Language](https://gdcvault.com/play/1023221/Ink-The-Narrative-Scripting-Language)

- Game Developer. "Open Sourcing 80 Days' Narrative Scripting Language: Ink": [https://www.gamedeveloper.com/design/open-sourcing-80-days-narrative-scripting-language-ink](https://www.gamedeveloper.com/design/open-sourcing-80-days-narrative-scripting-language-ink)

- Wayline. "The Illusion of Choice: Deconstructing Agency in Procedural Narrative": [https://www.wayline.io/blog/illusion-of-choice-procedural-narrative](https://www.wayline.io/blog/illusion-of-choice-procedural-narrative)

- Millard, David. "The Narrative Structure of The Witcher 3": [https://davidmillard.org/2016/12/03/the-narrative-structure-of-the-witcher-3/](https://davidmillard.org/2016/12/03/the-narrative-structure-of-the-witcher-3/)

- Ultimate Gacha. "Best Story-Driven Gacha Games": [https://ultimategacha.com/best-story-driven-gacha-games/](https://ultimategacha.com/best-story-driven-gacha-games/)

- Honkai: Star Rail narrative analysis (Medium): [https://medium.com/@Chantiment/see-you-tomorrow-amphoreus-lets-talk-about-honkai-star-rail-s-most-ambitious-narrative-yet-f05c6a4212e1](https://medium.com/@Chantiment/see-you-tomorrow-amphoreus-lets-talk-about-honkai-star-rail-s-most-ambitious-narrative-yet-f05c6a4212e1)

- The Artifice. "Player Agency or Illusion? Examining Moral Dilemmas in Narrative-Driven Games": [https://the-artifice.com/player-agency-or-illusion-examining-moral-dilemmas-in-narrative-driven-games/](https://the-artifice.com/player-agency-or-illusion-examining-moral-dilemmas-in-narrative-driven-games/)

- PulseGeek. "Game Narrative Design: Principles, Patterns, and Flow": [https://pulsegeek.com/articles/game-narrative-design-principles-patterns-and-flow/](https://pulsegeek.com/articles/game-narrative-design-principles-patterns-and-flow/)

- Level Design Book. "Pacing": [https://book.leveldesignbook.com/process/preproduction/pacing](https://book.leveldesignbook.com/process/preproduction/pacing)

- Oreate AI Blog. "Fate/Stay Night: The Dawn of a Visual Novel Legend": [https://www.oreateai.com/blog/fatestay-night-the-dawn-of-a-visual-novel-legend/fc5e788a2fb02986d749ad108703dcc0](https://www.oreateai.com/blog/fatestay-night-the-dawn-of-a-visual-novel-legend/fc5e788a2fb02986d749ad108703dcc0)

*Note: GDC Vault narrative talks require free GDC registration to access; all Vault URLs verified as real sessions. Jenkins' original essay PDF is freely downloadable. Hocking's original 2007 blog post is no longer live but is comprehensively cited in academic sources above.*
