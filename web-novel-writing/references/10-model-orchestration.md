> Purpose: 模型编排与选型的可执行规格 —— 把 9 步循环里"哪一步用什么模型 / 开不开 thinking / 温度多少 / 要不要异模型"定成 driver 用代码设的旋钮（不是写进 prompt 求模型自觉），并给一套"不信榜、用本 skill rubric 盲测 A/B"的选型协议。核心立场：**模型只是可选优化旋钮，不是依赖；按"思考 vs 写正文"切分工，不按品牌信仰切。** 主要用在**选模型**这一步，以及 9 步循环的步骤 3/4（writer 配置）、5/6（continuity/reviewer 配置）、8（去味异模型）。

---

## 0. 一句话原理

长篇崩坏的根因是"AI 自我一致性随篇幅衰减"，**这是内在衰减，换更贵的模型解决不了**（来源：腾讯复盘，见 `01-six-stream-findings`）。所以模型编排不解决"会不会崩"（那是架构层 §3 循环 + 状态层的事），它解决两件次要但有 ROI 的事：① 把**对的能力放到对的步骤**（推理强的去做结构/校验，文笔强的去写正文，异模型去交叉审校）；② 在**模型天花板以内**把可控旋钮（thinking / temperature / 候选采样）调到最优。

三条贯穿全文的诚实边界：

| 命题 | 状态 | 谁能修 |
|---|---|---|
| 一致性崩坏 / prompt 泄漏 / 流程纪律 | **工程能修** | 架构（状态层 + 确定性校验 + 独立 reviewer），与模型无关 |
| 词句层 AI 味（翻译腔/华美空洞/节奏匀速） | **工程能压低**（换模型只降这层、治标） | 生成期约束 + 句子层 lint（见 `09-anti-ai-slop`） |
| 叙事层 AI 味（语感/留白/道德模糊/"人味儿"） | **模型天花板**，换模型换不掉 | 只能靠人类在大纲阶段注入（RLHF mode collapse，见 §8） |

> ⚠️ 元铁律落地：本文所有"旋钮"（关 thinking / 温度 / 异模型 / 候选数）都由 **driver 用代码在调用时设参数**，绝不能写成 prompt 里"请你不要把思考写进正文""请你保持多样性"这类 prose——那是会随模型漂移的伪约束。能 code 设的参数绝不交给模型自觉。

---

## 1. 为什么按"思考 vs 写正文"切（不按品牌信仰切）

**原理（反直觉，易错）**：reasoning / agentic 训练与"按硬约束写正文"是**负相关**的。NeurIPS 2025 实测：开启 CoT（chain-of-thought）后，14 个模型里有 **13 个 IFEval 指令遵循变差**——漏掉字数规则、擅自加冗余的"贴心"补充、把推理过程混进正文（来源：`02-critique-ax-framework` §五 / `03-pipeline-design-blueprint` §6）。

对网文 pipeline 这意味着两条因果：

1. **正文生成开 thinking = 主动制造泄漏**。开 thinking 的模型倾向把"它在想什么"溢出到输出里（元叙述、"本章将…"、"作为助手我…"）。这正是平台一秒鉴 AI 的残留指令符号来源。**根因防治 = 写正文时关 thinking**；`03-prompt-compiler` 的 SUFFIX + 正则剥离只是事后安全网，不是根治。
2. **结构/校验关 thinking = 自废武功**。大纲推演、逻辑一致性、时间线区间运算这类活恰恰需要 reasoning，该开就开。

所以分工轴是**能力性质（思考型 vs 生成型）**，不是"哪个品牌中文好"。"GLM 比 GPT 文笔好"是品牌信仰式选型，会让你在该开 thinking 的校验步上用了关 thinking 的文笔模型，南辕北辙。

---

## 2. 9 步循环 × 模型配置表（driver 按此设参，逐步收回控制权）

每个 LLM 调用是窄子程序，调用完代码立刻收回控制权。下表是 driver 给每一步设的旋钮（模型 ID 一律不写死，只写**能力画像**）：

| 步 | 角色 | 能力画像 | thinking | temperature ⚠️起步值 | 异模型要求 | 依据 |
|---|---|---|---|---|---|---|
| 1 | planner（每卷/arc） | 强 reasoning / 长程规划 | **开** | 0.6 | 与 writer 可同可异 | 结构推演吃 CoT |
| 2 | outliner（章纲） | 强 reasoning + 懂套路 | **开** | 0.6 | — | 同上 |
| 3 | prompt-compiler | 无（纯代码） | — | — | — | 确定性流程，不调 LLM（见 `03`） |
| 4 | **writer（正文）** | **强中文文学性** | **关** | 高潮 0.5 / 日常 0.8（§4） | 精华章可换强文笔模型 | NeurIPS：写正文关 thinking |
| 5 | continuity-checker | 强 reasoning / 严谨 | **开** | 0.2（求稳） | **必须 ≠ writer** | 吃事实判对错，要确定性（见 `04`） |
| 6 | reviewer（rubric） | 强 reasoning / 批判 | **开** | 0.3 | **必须 ≠ writer，最好异厂** | 自审即自欺（见 `04`） |
| 7 | revise（改稿） | 同 writer 或更强 | 关 | 0.6 | 第 2-3 轮可换模型/换候选 | 不反复重抽同一 prompt |
| 8 | style/anti-slop-editor | 文笔强 + **异源** | 关 | 0.7 | **必须 ≠ writer 同源** | 同源互洗无效（见 §8 / `09`） |
| 9 | state-updater（抽 delta） | 强结构化抽取 | 开 | 0.0-0.2 | — | 只吐 JSON delta，要可复现 |

**三条硬规则**（都是 code 强制，不是 prose 求）：

- **步骤 4 写正文必须关 thinking**——这是防泄漏的根因层，不是可选项。
- **步骤 5/6 必须与 writer 独立调用**（独立上下文 + 最好异厂模型）——共享上下文的"自审"必然自欺（执行者没变）。`04-review-rubric` 已把"reviewer 只返 JSON、不持 Write"钉死。
- **步骤 8 去味必须异源**——同源模型把自己的 AI 味文本喂回去重写，检测器仍 96-98% 判 AI（来源：`02-critique` §二.8）。

> ⚠️ temperature 起步值：研究只硬给了"高潮 0.5 / 日常 0.8"（来源：`03-blueprint` §6）；校验/抽取的低温值（0.0-0.3）是按"要可复现/求稳"的合理推断，需在自己项目上微调，不是定数。

---

## 3. client 可注入 = provider-agnostic + 测试 seam

**原理**：把 LLM client 做成可注入的（`base_url + model` 可换），一箭三雕——既是**换 provider 的旋钮**（GPT/DeepSeek/GLM/本地模型随 `base_url` 切），又是**异模型编排的接口**（步骤 5/6/8 注入不同 client 实例），还是**离线测试的 seam**（测试注入假 client，确定性、零额度、无凭据）。这与创作者 CLAUDE.md 的 AI-pipeline 铁律同构：**LLM 是被确定性代码包裹的子程序，client 用注入而非硬编。**

```python
# 编排骨架（硬化 mode 的 chapter_loop 才需要；agent-driven MVP 由 agent 本体充当各角色）
def make_call(client=None, *, base_url=None, model=None, thinking=False, temperature=0.8):
    client = client or build_client(base_url, model)   # None → 建真 client；测试传 fake
    return client.complete(prompt, thinking=thinking, temperature=temperature)

writer   = lambda p: make_call(base_url=PROSE_URL,  model=PROSE_MODEL,  thinking=False, temperature=0.8)
reviewer = lambda p: make_call(base_url=REASON_URL, model=REASON_MODEL, thinking=True,  temperature=0.3)  # 异厂
```

**两种 mode 的诚实区分**：
- **Agent-driven mode（默认 MVP）**：没有上面的 client 代码——你（Codex/Claude Code 这个 agent）**本体**轮流扮 writer/reviewer/continuity，"换模型"= 人类/编排层换调用哪个模型来跑这一步。`scripts/` 里现有的 `compile_prompt.py` / `state_check.py` / `antislop_lint.py` 是**纯确定性、不调 LLM**的。
- **硬化 mode（可选）**：未来若把循环真正脚本化（`chapter_loop.py`），client 注入是必须的接口设计——别在脚本里硬编一个 provider。

---

## 4. temperature 分场景（不是全程一个值）

**原理**：温度是"分布陡峭度"旋钮。爽点高潮/打脸/关键反转要的是**稳准狠**（别让模型在该把话说死的地方发散跑偏），温度调低；日常过渡/环境扩写要的是**活与变化**（别千篇一律），温度调高。但**别用高温来救多样性**——高温会触发退化（重复、语无伦次、突然崩中文），多样性恢复要用 §5 的 Verbalized Sampling。

| 场景 | temperature ⚠️ | 为什么 |
|---|---|---|
| 爽点高潮 / 打脸四部曲 / 关键反转 | 0.5 | 节拍要稳、话要说死，发散会泄气（来源：`03` §6） |
| 日常过渡 / 环境/旁白扩写 | 0.8 | 要活、避免匀速寡淡（来源：`03` §6） |
| continuity / reviewer / state 抽取 | 0.0-0.3 ⚠️推断 | 判对错、抽 delta 要可复现 |
| 候选生成（提案/命名/钩子多版） | 用 Verbalized Sampling，不靠高温 | 见 §5 |

落地：温度挂在章纲 beat sheet 上（高潮章 vs 日常章），由 driver 读字段设参，**不写进 prompt 让模型"自己把握分寸"**。

---

## 5. 多样性恢复用 Verbalized Sampling（不靠调高温）

**原理**：RLHF 把模型分布收窄成了 mode collapse——你问"给一个章末钩子"，它给的是分布峰值那个**最套路**的答案。调高温只是在退化边缘抖动，不是真多样。**Verbalized Sampling**（先让模型显式列出 N 个候选再选）绕开这一点：让模型把概率质量"说出来"，在低温/正常温下也能覆盖到非峰值的好候选（来源：`02-critique` §五 / `03-blueprint` §6）。

**用在哪**（正好对齐人机边界里 semi-auto 的"AI 出多版供人选"）：

| 场景 | 怎么用 | 对接人机边界 |
|---|---|---|
| 剧情提案 | 让 AI 在顶层契约约束内出 **3 套方向**，列差异点，人选 | 剧情=走向 human-only / 提案 semi-auto |
| 命名（功法/地名/章节名） | 一次列 5-8 个候选 + 各自调性标签，人选 | automate 出候选，人拍板 |
| 章末钩子 | 按 4 型钩子各出 1 版，对比兑现度 | 见 `07-sao-engine-emotion` 钩子 4 型 |
| 黄金三章开篇 | 多版草稿（先抑后扬/楔子/复仇…），人选最能落地的 | semi-auto |

**铁律**：候选由模型列、**拍板永远是人**（走向/爽点力度/品类调性是 human-only）。Verbalized Sampling 只是把"AI 自由发挥那个旧套路答案"换成"一组可选项让人挑"。

---

## 6. 选型协议：不信任何榜，用本 skill rubric 盲测 A/B

**原理**：公开榜不可信。EQ-Bench 已被"堆砌文学手法"reward-hack——刷分文本与人类专家判断**仅 43% 一致**（来源：`02-critique` §三 / `03` §6）。营销话术（"最强中文文笔"）和单一作者实测（"GLM>GPT"）都不能照搬。**唯一可信的选型证据 = 在你自己的对标章上、用本 pipeline 的三道闸盲测。**

**盲测 A/B 协议（控制变量，可复用）**：

1. **取对标章**：选 1-2 章有代表性的（含一个爽点高潮 + 一段日常过渡），用**同一份编译好的 prompt**（同 beat sheet、同 canon、同温度）。控制变量是关键，否则比的是 prompt 不是模型。
2. **各候选生成**：正文模型一律关 thinking、结构/校验候选一律开 thinking，分别跑出 A/B/C 稿。
3. **盲化**：抹掉模型标识，只留编号 A/B/C，避免品牌偏见污染评分。
4. **过三道闸**（复用既有机制，得到可比的 `final`）：
   - `scripts/antislop_lint.py` → 机械 AI 味扣分（桶1 词句层指纹）
   - continuity-checker → 一致性 F1 / 硬门命中（F1≈0.68，只"标记可疑"⚠️）
   - reviewer rubric → 7 维加权分（见 `04-review-rubric`）
   - `final = LLM 加权分 − 机械扣分`（双免疫终分）
5. **看维度分布，不看总分单点**：哪个模型在「文笔/对白/AI 味」强、哪个在「一致性/逻辑」强。**很可能不是同一个**——于是可分环节用不同模型（精华章用强文笔的、批量日更章用性价比高的、校验用异厂推理强的）。
6. **样本量 + 抗运气**：至少 N 章（N≥3），别用单章定生死；结果落进一张**选型矩阵**（品类 × 平台 × 环节 → 选哪类模型），随项目演进更新。
7. **定期复测**：模型迭代极快，季度级复测，别把半年前的结论当常量。

> 选型矩阵是"画像→环节"的映射，**不写死 ID**：例：`{精华高潮章: 强文笔关thinking}` / `{批量日更章: 性价比关thinking}` / `{reviewer: 异厂强reasoning开thinking}` / `{style去味: 与writer异源}`。

---

## 7. 模型口碑一律标存疑（别照搬营销/单点实测）

下面这些流传说法**全部是单一来源 / 单一作者实测**，本 skill 不采信为结论，只作"盲测时优先验证的假设"：

| 流传说法 | 来源性质 | 本 skill 态度 |
|---|---|---|
| "GLM > GPT（中文文笔/AI 味淡）" | 单一作者实测 ⚠️ | 存疑，盲测覆盖（来源：`01-six-stream` 标 medium） |
| "DeepSeek 描写细腻但'语言怪'/慢热，八千字才到爽点" | CSDN 实测 + 单作者 ⚠️ | 存疑；可能更适合**起点慢热品类的描写/扩写**环节，不适合快节奏开篇（来源：`01` 调研流二 medium） |
| "Claude 中文文笔优于 GPT、AI 味淡、超大上下文" | 多方体感 ⚠️ | 方向可参考，量级存疑；上下文大不等于不崩（崩是衰减问题） |
| "国产模型更懂中文术语" | 单作者实测 ⚠️ | 存疑，盲测覆盖 |

**为什么都存疑**：本调研未找到一份控制变量的中文网文文笔横评（马良有"Claude/Gemini/GPT/DeepSeek 实测排名"文但未取到具体打分）。结论缺位时，**自己的对标章盲测 > 任何二手口碑**。

---

## 8. 诚实的能力边界：叙事层 AI 味换模型换不掉

**原理（必须对创作者讲清，否则他会一直换模型试图根治）**：叙事层 AI 味是 RLHF 对齐导致的 **mode collapse**，不是某个模型的缺陷。StoryScope 仅用 **30 个叙事特征就 93.2% 区分人/AI**（来源：`02-critique` §三 / `03` §5）——这些特征是叙事结构层的（情绪曲线、留白、道德模糊度），不是换个 provider 能抹掉的。

| 换模型能改的 | 换模型改不掉的 |
|---|---|
| 句子层指纹（连接词癖、形容词叠罗汉、否定平行）—— 但只降这层、治标 | 叙事层"匀速安全"、不敢留白、爱点题升华、道德非黑即白 |
| 个别术语/语感顺不顺 | "做加法不推进剧情"的结构惯性 |
| 一致性？**不能**——一致性靠架构不靠模型 | "人味儿"的手工感（节奏取舍、克制、意在言外） |

**根治路径**（与模型无关）：靠人类在**大纲阶段**注入留白/不点题/道德模糊/多线（human-only），靠**生成期约束**（禁用词清单 + Show-Don't-Tell 分层 + 感官配额，见 `09-anti-ai-slop` 桶2/桶3）。换国产文学性强的模型是**可选优化旋钮**——它能让句子层好看一档，但叙事层的天花板要靠人。把这点诚实告诉创作者，比给他"换了 X 模型就不 AI 了"的虚假承诺更负责。

---

## 9. 反模式 + 可复用要点

**反模式（命中即纠正）**：

- ❌ 按品牌信仰分工（"GLM 中文好就全用 GLM"）→ 会让校验步用了关 thinking 的文笔模型。按思考 vs 写正文切。
- ❌ 写正文开 thinking → 推理溢出到正文 = 泄漏诱因。关 thinking 是根因防治。
- ❌ reviewer/continuity 与 writer 同上下文同模型 → 自审即自欺，质量门形同虚设。
- ❌ 去味把同源模型文本喂回自己重写 → 检测器仍 96-98% 判 AI。必须异源。
- ❌ 调高温救多样性 → 触发退化（重复/崩中文）。用 Verbalized Sampling。
- ❌ 信榜选型（EQ-Bench 等）→ 已被 reward-hack，与专家仅 43% 一致。用自己对标章盲测。
- ❌ 把"换更贵模型"当一致性解药 → 崩是衰减问题，架构修，不是模型修。
- ❌ 把旋钮（thinking/温度/异模型）写进 prompt 求模型自觉 → 伪约束。driver 用代码设参。
- ❌ 模型 ID 硬编进 skill → 违反 model-agnostic，且迭代快即过时。只写能力画像。

**可复用要点**：

1. 分工轴 = **思考 vs 写正文**；结构/校验开 thinking，正文关 thinking，去味/审校异模型交叉。
2. 旋钮（thinking/温度/候选数/异源）一律 **driver 代码设参**，挂在章纲字段上，不写进 prompt。
3. client **可注入**（base_url+model）：换 provider 的旋钮 + 异模型接口 + 测试 seam 三合一。
4. 温度**分场景**：高潮 0.5 稳 / 日常 0.8 活；校验抽取低温求稳。⚠️起步值，项目微调。
5. 多样性用 **Verbalized Sampling**（先列 N 候选再选），不靠高温；候选 AI 出、拍板永远人。
6. 选型**不信榜**，用本 skill 三道闸（antislop_lint + continuity + rubric）在对标章盲测 A/B，看维度分布分环节选模型，季度复测。
7. 一切模型口碑（GLM>GPT / DeepSeek 语言怪）**标 ⚠️ 存疑**，当待验证假设不当结论。
8. **诚实**：叙事层 AI 味 = 模型天花板（RLHF mode collapse），换模型只降句子层；模型是**可选优化旋钮、不是依赖**，默认就能在 Codex/GPT 上跑。

---

## Sources

- `docs/research/02-critique-ax-framework.md` §五（思考 vs 写正文分工 / NeurIPS 2025 CoT-vs-IFEval / Verbalized Sampling / 高温退化）、§三（EQ-Bench reward-hack 43% / StoryScope 30 特征 93.2% / 叙事层 AI 味 = RLHF mode collapse）、§二.8（同源互洗无效 96-98%）
- `docs/research/03-pipeline-design-blueprint.md` §6（模型分工方案：thinking 开关 / temperature 0.5-0.8 / client 注入 / 盲测不信榜）、§5（去 AI 味叙事层换模型换不掉）、§7（生成期约束）
- `docs/research/01-six-stream-findings.md` 调研流一（AI 自我一致性随篇幅衰减、贵模型解决不了；自审即自欺）、调研流二 medium（DeepSeek 慢热细腻 / 平台识别 AI 文三类缺陷）、存疑节（GLM>GPT 单一来源）
- 本 skill 内部对齐：`references/03-prompt-compiler.md`（SUFFIX + 残留符号剥离 = 泄漏事后网）、`references/04-review-rubric.md`（continuity/reviewer 分离 + 异模型 + 双免疫终分 + 净改善≥ε + sentinel）、`references/07-sao-engine-emotion.md`（钩子 4 型 / 爽点编排）、`references/09-anti-ai-slop.md`（三桶 + 句子层 lint + 生成期约束）、`scripts/antislop_lint.py`·`scripts/state_check.py`（确定性机械层，不调 LLM）
- ⚠️ 标注项：temperature 校验/抽取低温值、模型口碑（GLM>GPT、DeepSeek 语言怪、Claude 文笔）均为推断或单一来源，须以自有对标章盲测为准；不信任何公开榜。
