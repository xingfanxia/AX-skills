# 08 — Game Script Formats, Branching Tools & Production Handoff

> **Stream purpose:** How game stories are actually written down and handed to production teams. Concrete, copy-pasteable templates. Focus on 二游 (anime-gacha mobile) ADV/AVG scene scripts and the 演出 (staging direction) layer. Audience: AI agent guiding a non-professional Chinese writer.

---

## 1. Game Script Format vs. Screenplay vs. Novel

### The core difference

A film screenplay is linear — it describes one fixed chain of events. A novel is pure prose in the author's voice. A **game script is neither**: it must account for interactivity, branching, asset pipeline (voice files, emotion states, sprite IDs), and multiple downstream readers (engineers, voice directors, localization vendors, QA).

There is **no universal game script format**. Format follows the game type:

| Game type | Script form used in practice |
|---|---|
| Cinematic cutscene (action RPG, AAA) | Screenplay-adjacent "passive format" |
| In-world interactive dialogue (RPG, adventure) | Spreadsheet / dialogue table |
| Visual novel / ADV / galgame | ADV演出脚本 (staging script) |
| Branching choice narrative (80 Days, Heaven's Vault) | ink / Twine source files |
| Mobile gacha ADV story (原神, 崩铁, 蔚蓝档案) | Hybrid: writer drafts ADV演出脚本, engineers convert to engine format |

---

## 2. The Three Core Formats

### Format A — Screenplay-adjacent (Passive Format)

**What it is:** Looks like a film script. Courier New 12pt, wide margins, all-caps scene headings, action lines, character names centered above dialogue. Used for cutscenes where the player is a passive viewer (not making choices).

**When to use:** Opening CGI, major boss reveals, ending sequences. Any moment where you want full cinematic control and no branching.

**Pitfall:** Overkill for interactive dialogue. Wastes space for anything with choices or variable states.

```
INT. OBSERVATORY — NIGHT

Hua Jing stands at the telescope, back to the player.

                    HUA JING
          You came. I wasn't sure you would.

She turns. Her expression is unreadable.

                    HUA JING (CONT'D)
          The Veil opened at midnight. We have
          maybe three hours before the gate seals.

CHOICE:
          1. "I'm here. Tell me everything."
          2. "Why didn't you warn us sooner?"
          3. [Say nothing]
```

**Note:** The screenplay form breaks down the moment branching enters. That's where the spreadsheet takes over.

---

### Format B — Dialogue Spreadsheet / Active Format

**What it is:** A multi-column table (Excel, Google Sheets, CSV) where every line of dialogue is one row. Each row carries all metadata needed for engineering, voice recording, localization, and QA. This is **what most mobile game teams actually use for the bulk of their dialogue** — especially for anything that needs to be localized or voice-recorded.

**When to use:** Any dialogue that is: (a) interactive / branching, (b) will be translated, (c) will be voice-acted, or (d) needs to be tracked by ID in code. In practice: 90% of a mobile gacha game's text lives here.

**Pitfall:** Writers who skip this format cause production nightmares — duplicate voice-file names crash the game, lines not added to the master sheet don't get translated, QA files diverge from engineering files. (Source: *Organizing and Formatting Game Dialogue*, Game Developer / Gamedeveloper.com)

#### Minimal viable dialogue table (copy this):

| line_id | scene_id | speaker | emotion | zh_text | en_text | voice_file | branch_to | condition | notes |
|---|---|---|---|---|---|---|---|---|---|
| SCN01_010 | SCN01 | 华镜 | neutral | 你来了。 | You came. | hua_jing_scn01_010 | SCN01_020 | — | — |
| SCN01_020 | SCN01 | PLAYER_CHOICE | — | [选择支] | [Choice] | — | — | — | Show choice UI |
| SCN01_021 | SCN01 | 主角 | determined | 我在这里。说吧。 | I'm here. Tell me everything. | player_scn01_021 | SCN01_030 | choice==A | — |
| SCN01_022 | SCN01 | 主角 | accusing | 你为什么没提前警告我们？ | Why didn't you warn us? | player_scn01_022 | SCN01_030 | choice==B | — |
| SCN01_030 | SCN01 | 华镜 | sad | 帷幕在午夜打开了。我们只有三个小时。 | The Veil opened at midnight. Three hours left. | hua_jing_scn01_030 | SCN01_040 | — | — |

**Column glossary:**
- `line_id` — unique, never reuse, never rename after voice recording locks
- `scene_id` — groups lines for QA filter / export batch
- `speaker` — consistent name form (decide: 华镜 or Hua_Jing — pick one and enforce)
- `emotion` — maps to a sprite emotion state; must match the art asset list
- `zh_text` / `en_text` — separate columns; localization vendor works in their own column, never overwrites original
- `voice_file` — naming convention example: `{char}_{scene}_{line_number}` e.g. `hua_jing_scn01_030`
- `branch_to` — which line_id follows; allows engineers to reconstruct the graph
- `condition` — what flag/variable must be set for this line to appear
- `notes` — VA direction notes, context, do-not-translate markers

**Voice file naming rule:** Use a convention that encodes character + scene + sequence. Never use the same filename twice. After recording locks, the `voice_file` column is frozen — changing it requires a re-import in engine.

---

### Format C — Annotated Prose Script

**What it is:** Reads like a short story or stage play, but with inline direction notes in brackets. Useful as a first draft or pitch document before the spreadsheet is built. Some indie teams write their entire game this way and convert manually.

**When to use:** Early drafting, pitching to a director, single-writer projects without an engineering team. Not production-ready for team workflows.

```
[场景: 观星台·深夜 / BGM: 《碎镜》淡入]

华镜站在望远镜前，背对玩家。[立绘: 华镜·普通服, 位置: 右, 表情: neutral]

华镜："你来了。我还以为你不会来。"

她转身。表情难以名状。[立绘: 华镜, 表情 → wistful]

华镜："帷幕在午夜开启了。我们大概只有三个小时，在门封闭之前。"

[选项分支]
  A: "我在这里，你说吧。" → 跳至 SCN01_030_A
  B: "你为什么没有提前警告我们？" → 跳至 SCN01_030_B
  C: [沉默] → 跳至 SCN01_030_C
```

---

## 3. Branching Dialogue: Choices, Flags, and State

### The core concepts

**Choice node:** A moment where the player selects from 2–5 options. Each option is a branch. Branches usually reconverge after 1–3 lines (called a "diamond" or "bowtie" structure) or lead to divergent content (true branching).

**Flag / variable:** A boolean (true/false) or integer stored in game state. Example: `met_hua_jing = true`, `relationship_score += 1`. Conditions on later lines check flags to decide whether a line appears.

**Conditional line:** A line that only shows if a condition is met. Example: "You found the letter" only appears if `found_letter == true`.

**Reconvergence:** Branches that merge back to a single "spine" line. Most mobile ADV games use heavy reconvergence to control content budget — they cannot afford to write 4x content for every branch.

**Gating:** Preventing a choice from appearing unless a condition is met (e.g., player must have talked to NPC X first). Shown in spreadsheet as a `condition` value on the choice row.

### Notating branching readably (for writer handoff)

In a prose/annotated script, use indentation and labels. The writer's job is to make branching legible before it becomes a spreadsheet row:

```
[CHOICE NODE — SCN01_020]

  OPTION A (always available): "我在这里，你说吧。"
    → 华镜叹气，点头。→ 跳至 SCN01_030

  OPTION B (always available): "你为什么不提前警告？"
    → 华镜眼神闪过一丝痛苦。→ 跳至 SCN01_031
    → [SET FLAG: player_accused_hua = true]

  OPTION C (gate: only if player found the letter): "我看到了那封信。"
    → 华镜愣住，随即苦笑。→ 跳至 SCN01_032

[RECONVERGE — SCN01_040]
  全部分支在此汇合。
  华镜："无论如何，时间不等人。"
```

**Rule:** Every branch must have an exit. A branch with no `→` is a dead end — the player is trapped. Always check this in writer review before handoff.

---

## 4. Tool Guide for Beginners

### Tool selection by situation

| Situation | Tool | Why |
|---|---|---|
| Just want to draft and share a branching story, zero code | Twine (twinery.org) | Visual click-to-link passages, runs in browser |
| Writing branching narrative that will go into Unity | ink + Inky | Script-first, writer-friendly, Unity plugin available |
| Building a visual novel / galgame | Ren'Py | Purpose-built VN engine + scripting language |
| Unity game with dialogue system | Yarn Spinner | Yarn script language integrates with Unity natively |
| Professional team, full narrative DB needed | articy:draft X | Asset DB + flow editor + localization toolset |
| Mobile team, spreadsheet-based pipeline | Google Sheets / Excel | What most CN mobile teams actually use |

---

### Twine

**What:** Free, browser-based, no-code authoring tool. Write passages, click to link them. Exports to HTML for web play. Two main story formats: Harlowe (default, beginner-friendly), Sugarcube (more powerful, allows variables).

**When to use:** Prototyping a branching structure before committing to an engine; personal projects; sharing a demo with non-technical collaborators; learning branching narrative concepts.

**Pitfall:** No built-in export to production game format. Twine is for prototyping, not for shipping to an engine. You will have to manually convert your Twine structure into a spreadsheet or engine format.

**Mini-example (Harlowe / Sugarcube syntax):**

```
:: Start
你站在观星台前。华镜的背影映在月光下。

[[走近她 -> AproachHua]]
[[先环顾四周 -> LookAround]]

:: AproachHua
华镜转身，目光中有一丝惊喜。
"你来了。"

[[回答"我在这里" -> Reply_A]]
[[保持沉默 -> Silence]]

:: Reply_A
你点点头。"我来了。"
华镜似乎松了口气。

:: Silence
两人沉默片刻，风吹过。

:: LookAround
台上只有你们两人。星空很美，但不是看星星的时候。
[[走向华镜 -> AproachHua]]
```

---

### ink / Inky (by inkle)

**What:** Open-source scripting language designed by inkle (makers of 80 Days, Heaven's Vault). Write stories as text scripts. Inky is the official editor with a live preview panel. Compiled ink integrates with Unity via the official `ink-unity-integration` plugin. Also runs standalone as a web story via `ink.js`.

**When to use:** Branching narrative that will be embedded in a game engine (Unity preferred); stories with complex conditional logic; professional indie projects. Design philosophy: the script should be readable as prose — the author is the primary audience.

**Key concepts:**
- **Knot** (`=== knot_name ===`): largest unit, equivalent to a scene or node
- **Stitch** (`= stitch_name`): sub-section within a knot
- **Divert** (`-> knot_name`): jump to another knot/stitch
- **Choice** (`*` single-use, `+` sticky/repeatable): player options
- **Variable** (`VAR x = 0`): global state
- **Conditional** (`{x > 0: this text}`)

**Tiny ink example:**

```ink
VAR accusation = false

=== observatory ===
华镜站在望远镜前，背对你。
"你来了。我还以为你不会来。"
"帷幕在午夜开启了。我们只有三个小时。"

* [我在这里，你说吧。]
  "好。那我们就从头说起。" -> explain

* [你为什么不提前警告我们？]
  ~ accusation = true
  华镜顿了一下，苦笑。"对不起。" -> explain

* + [沉默]
  两人沉默片刻。 -> explain

=== explain ===
{accusation:
  - 华镜说话时眼神有些回避。
  - 华镜平静地开口了。
}
"那封信——你看到了吗？"
-> END
```

**Official docs:** https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md

**Pitfall:** ink is a scripting language, not a full game engine. You still need an engine (Unity, Godot, web) to render characters, sprites, music. It handles narrative logic, not presentation.

---

### Ren'Py

**What:** Free, open-source visual novel engine with its own Python-based scripting language. Handles sprites, backgrounds, music, sound, animations, menus. Ships cross-platform (Windows, Mac, Linux, Android, iOS, web). The standard tool for indie VN / galgame production.

**When to use:** Standalone visual novel; galgame; indie ADV game; any project where the writer also controls production and doesn't need a separate engine team. Easy to get a playable demo in hours.

**Key syntax concepts:**
- `label start:` — entry point
- `scene bg_name` — set background image
- `show char_name expression at position` — display character sprite
- `hide char_name` — remove sprite
- `play music filename` — BGM
- `"Text"` — narration (no speaker)
- `character_var "Text"` — character dialogue
- `menu:` — choice block

**Ren'Py mini-example:**

```renpy
# Characters defined at top of script
define hj = Character("华镜", color="#c8a2c8")

label observatory_scene:
    scene bg_observatory_night
    play music "BGM_shattered_mirror" fadein 1.0

    show huajing normal at right
    hj "你来了。我还以为你不会来。"

    show huajing wistful
    hj "帷幕在午夜开启了。我们只有三个小时。"

    menu:
        "我在这里，你说吧。":
            $ accusation = False
            jump reply_calm
        "你为什么不提前警告我们？":
            $ accusation = True
            show huajing pained
            hj "对不起。"
            jump reply_accused
        "（沉默）":
            jump reply_silent

label reply_calm:
    show huajing relieved
    hj "好。那我们就从头说起。"
    jump converge

label reply_accused:
    hj "我以为还有时间。"
    jump converge

label reply_silent:
    "风吹过台上，没有人说话。"
    jump converge

label converge:
    hj "那封信——你看到了吗？"
```

**Official docs:** https://www.renpy.org/doc/html/

**Pitfall:** Ren'Py scripts tightly couple narrative and staging. For large teams, this means writers must coordinate with artists (sprite names must match exactly). Establish a shared asset-naming spreadsheet before writing.

---

### Yarn Spinner

**What:** Open-source dialogue scripting language for Unity. Sister tool to Twine in feel (node-based thinking), but outputs to Unity's dialogue system. Script files use `.yarn` extension. Good Unity Asset Store tooling.

**When to use:** Unity-based game (action RPG, adventure, sim) where you want a dedicated dialogue scripting layer separate from game code. Writers write `.yarn` files; engineers handle the Unity Dialogue Runner.

**Mini-example:**

```yarn
title: Start
---
Player: 华镜？
Huajing: 你来了。我还以为你不会来。
Huajing: 帷幕在午夜开启了，我们只有三个小时。
-> 我在这里，说吧。
    <<set $accusation to false>>
    Huajing: 好。从头说起。
-> 你为什么不警告我们？
    <<set $accusation to true>>
    Huajing: 对不起，我以为还有时间。
<<jump explain>>
===

title: explain
---
<<if $accusation>>
    Huajing: 说话时她没怎么看你。
<<else>>
    Huajing: 她平静地开口了。
<<endif>>
Huajing: 那封信，你看到了吗？
===
```

**Official docs:** https://docs.yarnspinner.dev/

---

### articy:draft X

**What:** Professional-grade narrative design suite. Full game content database: characters, locations, items, dialogue flows, variables, conditions. Flow editor (visual node graph), localization toolset with DeepL auto-translation, Unity/Unreal plugins, JSON export for other engines. Free tier: 700 objects. Paid plans from €6.99/month.

**When to use:** Medium-to-large team; game with thousands of lines; multiple writers who need to co-edit; formal narrative Bible that needs to link to dialogue. Used on major titles.

**Pitfall for beginners:** Heavy onboarding cost. A solo writer making their first game should not start here. Start with Twine or ink, graduate to articy when the project scales.

---

### Plain Spreadsheet (Google Sheets / Excel)

**What:** The actual workhorse of most mobile game teams. No learning curve, everyone can open it, filters work for QA, export to CSV for engineering, share with localization vendor directly.

**When to use:** Any team pipeline. Always maintain a master dialogue sheet even if you also use ink or Ren'Py for scripting. The sheet is the source of truth for voice file IDs and localization.

**Pitfall:** Without strict naming conventions and access controls, the sheet becomes chaotic fast. Lock the `line_id` and `voice_file` columns after voice recording begins — changing them after the recording session means re-importing all audio.

> **工具现状（截至 2026，给选型参考）**：上述工具均在活跃维护——**Twine** 2.12.0（2026-04）；**Yarn Spinner** 3.1（2025-12，新增异步对话、分支兜底防死锁）；**articy:draft X** 2025-08 大版本更新；**ink** 持续获 AAA 采用（2025《吸血鬼避世血族 2》即用 ink，并开源了 UE 运行时 Inkpot）；**Ren'Py** 仍是视觉小说引擎事实标准。结论不变：新手从 Twine / ink / Ren'Py 起步，团队规模化再上 articy。⚠️ 版本号会继续滚动，选型前查官网最新。

---

## 5. 二游 ADV 演出脚本 — The Staging Layer

### What the 演出 layer is

In an anime-gacha mobile game ADV scene (think 原神 story quests, 崩坏:星穹铁道 space station conversations, 蔚蓝档案 school events, 明日方舟 operator files), the script is not just dialogue. The writer must also specify:

- **立绘 (sprite) show/hide/move** — which character sprite appears, at which screen position (left / center / right), whether it fades in or slides in
- **表情 (expression) changes** — the sprite's emotion state: `normal`, `happy`, `shocked`, `sad`, `angry`, etc. These must match the art team's sprite sheet names exactly
- **背景 (background) swap** — which background image loads; transition effect (cut, fade, scroll)
- **BGM change** — music track name, volume, fade in/out
- **SE (sound effect)** — footsteps, door open, impact, rain
- **演出 FX** — screen flash, shake, CG insert, full-screen VFX
- **Voice line cue** — the `voice_file` ID that triggers playback (matches the spreadsheet's `voice_file` column exactly)
- **Text box type** — NVL (full-screen text, novel mode) vs ADV (bottom text box over scene)

This staging layer is what separates a "visual novel" from a "wall of text with character portraits." The writer who understands it controls the emotional pacing of the scene.

### ADV 演出脚本 — Annotated Template (Copy This)

The following is a writer-facing annotated script. Engineers convert this into engine-specific commands. The annotation style uses `[方括号]` for direction, with Chinese labels for the direction type.

```
========================================
场景名称: 观星台·初遇
场景编号: SCN_OBS_01
作者: [作者名]
版本: v0.2
========================================

[背景: bg_observatory_night_01 | 切换方式: 淡入 | 时长: 1s]
[BGM: BGM_碎镜_低音 | 音量: 60% | 淡入: 2s]

--- 旁白 ---
深夜。观星台上只有风声。
你推开门，看见一个熟悉的背影。

[SE: se_door_open]

--- 华镜 ---
[立绘: HuaJing | 位置: 右 | 出现方式: 淡入 | 表情: neutral_back]
（台词，华镜背对镜头）
"你来了。我还以为你不会来。"
[配音: hua_jing_scn01_010]

[立绘: HuaJing | 动作: 转身 | 表情: wistful_front]
"帷幕在午夜开启了。"
[配音: hua_jing_scn01_020]
[演出FX: 屏幕轻微震动 | 强度: 轻 | 时长: 0.3s]

"我们只有三个小时，在门封闭之前。"
[配音: hua_jing_scn01_030]

--- 选择支 ---
[UI: 显示选项框]

  选项 A: "我在这里，你说吧。"
  [配音: player_scn01_021]
  → 跳至: SCN_OBS_01_A
  [SET FLAG: accusation = false]

  选项 B: "你为什么不提前警告我们？"
  [配音: player_scn01_022]
  → 跳至: SCN_OBS_01_B
  [SET FLAG: accusation = true]

  选项 C: [沉默] （无配音）
  → 跳至: SCN_OBS_01_C

--- 分支 A (SCN_OBS_01_A) ---
[立绘: HuaJing | 表情: relieved]
华镜："好。那我们就从头说起。"
[配音: hua_jing_scn01_031_a]
→ 跳至: SCN_OBS_01_CONVERGE

--- 分支 B (SCN_OBS_01_B) ---
[立绘: HuaJing | 表情: pained]
华镜："对不起。我以为还有时间。"
[配音: hua_jing_scn01_031_b]
[BGM: 音量降低至 40%]
→ 跳至: SCN_OBS_01_CONVERGE

--- 分支 C (SCN_OBS_01_C) ---
[立绘: HuaJing | 表情: uncertain]
（旁白）
风吹过台上。没有人说话。
→ 跳至: SCN_OBS_01_CONVERGE

--- 汇合点 (SCN_OBS_01_CONVERGE) ---
[BGM: 音量恢复 60%]
[立绘: HuaJing | 表情: determined]
华镜："那封信——你看到了吗？"
[配音: hua_jing_scn01_040]

[背景: 淡出]
[立绘: HuaJing | 消失方式: 淡出]
[BGM: 淡出 | 时长: 2s]
--- 场景结束 ---
```

### Naming convention for sprite expressions

Establish this list with your art director before writing any scene. Keep it in the master spreadsheet as a reference tab. Typical set for a 二游 character:

| Expression key | 含义 |
|---|---|
| `normal` | 标准表情，微表情 |
| `happy` | 开心，微笑 |
| `laugh` | 大笑 |
| `sad` | 悲伤 |
| `crying` | 哭泣 |
| `angry` | 生气 |
| `surprised` | 惊讶 |
| `pained` | 痛苦 |
| `shy` | 害羞 |
| `determined` | 坚定 |
| `wistful` | 若有所思 |
| `relieved` | 松了口气 |
| `uncertain` | 困惑 / 迟疑 |
| `neutral_back` | 背对（有背影立绘时） |

**Writer's rule:** Only use expressions on this list. If you write `[表情: guilty_but_resolved]` and that sprite doesn't exist in the art sheet, the engineer will either break the build or default to `normal`. Agree on the set before drafting.

---

## 6. Localization and Voice Considerations

### Writing for translation (localization hygiene)

**Use stable IDs, never rename them.** The `line_id` in your spreadsheet is what the localization vendor references. Renaming `SCN01_010` to `OBS01_010` after handoff invalidates their translation files.

**Separate source from translation in columns.** Your `zh_text` column is frozen after handoff. The vendor fills `en_text`, `ja_text`, etc. Never let them overwrite the source.

**Avoid embedded formatting in text.** If possible, keep `{player_name}` as a placeholder in text rather than hard-coding "旅行者". This allows the localization vendor to place the variable correctly for each language's word order.

**Write short.** Mobile screens have limited text box space. A Chinese sentence of 20–25 characters often expands to 40+ characters in German or 35+ in English. The safe rule: if your Chinese line is under 25 chars and reads naturally, it will probably fit everywhere. Budget generously when writing lines that exceed 40 Chinese chars.

**Avoid idioms and puns that only work in one language.** If a line's emotional impact depends on a Chinese four-character idiom (成语) or a pun on a character's name, add a translator note column explaining the original intent. The translator can then find an equivalent, rather than producing a flat literal.

**Do not translate before the script is locked.** Every revision to zh_text after translation has already begun costs money and risks version drift.

### Voice-line script handoff

The VA recording package must include:

1. **The voice-file ID** — `hua_jing_scn01_010` — matches the spreadsheet exactly
2. **The dialogue text** — what is actually spoken
3. **Character brief** — personality, relationship to player, current emotional state in this scene (one paragraph per character, given to the VA at session start)
4. **Direction note** — optional but valuable for nuanced lines. Keep it to one sentence: "She's trying to sound calm but is failing." or "Teasing, not cruel."
5. **Context line** — the line before and after, so the VA understands the flow

**Voice script format for recording (per-session sheet):**

| voice_file | character | zh_text | direction | context_prev | context_next |
|---|---|---|---|---|---|
| hua_jing_scn01_010 | 华镜 | 你来了。我还以为你不会来。 | 表面淡定，实则如释重负 | （玩家推门进入） | 帷幕在午夜开启了。 |
| hua_jing_scn01_020 | 华镜 | 帷幕在午夜开启了。 | 陈述事实，声音压低 | 你来了。我还以为你不会来。 | 我们只有三个小时。 |

**Note on time-synced lines:** If a line plays during a CG or animated cutscene where the speaker's lips are visible, note it with `[LIP_SYNC]` in the direction column. These lines must be re-recorded for each localization language if you want lip-sync to match.

---

## 7. Quick Decision Guide for the Writer

The agent can use this flow when a writer asks "how do I write this down?":

```
Q: Is this a single cutscene with no choices?
  → Use screenplay-adjacent format (Format A)
  → Or annotated prose script (Format C)

Q: Does this scene have choices / branching / conditions?
  → Use dialogue spreadsheet (Format B)
  → Annotate with choice notation in prose draft first, then fill the sheet

Q: Is this for a visual novel / ADV game with sprites and BGM?
  → Use 演出脚本 template (Section 5)
  → Keep a parallel spreadsheet for voice file IDs and localization

Q: Do I need a tool to prototype quickly?
  → Twine (no code, browser)
  → ink + Inky (code-light, integrates with Unity)
  → Ren'Py (if you want a playable VN immediately)

Q: Will this be translated?
  → Spreadsheet is mandatory — use stable line_id from day one
  → Separate zh_text and en_text columns, never overwrite source
```

---

## Common Pitfalls Recap

| Pitfall | Fix |
|---|---|
| Using the same voice_file name twice | Naming convention enforced in spreadsheet from day one |
| Renaming line_id after localization starts | Freeze IDs when handoff begins |
| Referencing a sprite expression not in the art asset list | Agree on expression set with art director before writing |
| Branches with no exit | Writer checklist: every branch must have a `→` target |
| Writing idiom-dependent lines without translation notes | Add a `translator_note` column; note the original intent |
| Putting staging direction in the dialogue text cell | Keep direction in a separate `action` column |
| Building a whole game in screenplay format | Screenplay breaks down with choices; switch to spreadsheet early |

---

## Sources

- Organizing and Formatting Game Dialogue — Game Developer (Gamedeveloper.com): https://www.gamedeveloper.com/design/organizing-and-formatting-game-dialogue
- Arcweave blog, free game writing resources (spreadsheet template reference): https://blog.arcweave.com/free-games-writing-resources
- inkle official ink documentation (WritingWithInk.md): https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md
- inkle web tutorial for ink: https://www.inklestudios.com/ink/web-tutorial
- Creating Playable Stories with Ink and Inky (Toronto Metropolitan University Pressbooks): https://pressbooks.library.torontomu.ca/playablestoriesink/chapter/chapter-2-your-first-story/
- Ren'Py official documentation: https://www.renpy.org/doc/html/
- Yarn Spinner for Unity documentation: https://docs.yarnspinner.dev/yarn-spinner-for-unity/yarn-spinner-in-unity-scenes
- articy:draft X feature overview (via Storyflow Editor blog): https://storyflow-editor.com/blog/best-narrative-design-tools-for-game-developers-2025
- Twine introduction guide (Toronto NVM): https://thenvm.org/wp-content/uploads/2024/04/PDF-Introduction-to-Writing-Stories-with-Twine-.pdf
- IGDA Best Practices for Game Localization v2.2: https://igda-website.s3.us-east-2.amazonaws.com/wp-content/uploads/2021/04/09142137/Best-Practices-for-Game-Localization-v22.pdf
- Screenplays vs Game Scripts: 5 Differences — WriteOnSisters.com: http://writeonsisters.com/writing-craft/screenplays-vs-game-scripts-5-differences
- Storyflow Editor: Branching Dialogue Nightmare (node graph patterns): https://storyflow-editor.com/blog/branching-dialogue-nightmare-how-to-fix
- 机核GCORES 千篇一律的二次元手游叙事 (二游演出分析): https://www.gcores.com/articles/176345
- Bilibili 我花2个月做了叙事短篇游戏·剧情演出实现 (Unity Timeline + signal track演出实现): https://www.bilibili.com/read/cv6423536
- Hedberg Games Ink Glossary: https://www.hedberggames.com/glossary/ink

> **Confidence note:** The ADV 演出脚本 template (Section 5) is synthesized from multiple sources (Bilibili dev blog, 机核 analysis, galgame Zhihu discussions, Ren'Py documentation patterns) and industry observation — no single authoritative spec exists because each 二游 studio uses a proprietary engine format. The template represents common conventions, not an official standard. Writers should treat it as a starting point and adapt to their engine's actual command set.
