# 产品路线图 — 低动机·理解优先学习者的学习辅助产品族

> ⚠️ **PIVOT 2026-06-02:** 产品已从"陪伴者(AX)→朋友 的转发工具箱"转向 **"在 Claude Code 里主动引导用户学任何东西的教练"**——学习者直接驱动 skill,领域无关(英语降为一个可选 playbook)。目标用户=有 Claude Code、愿意主动学的人。下面这版路线图按【旧的陪伴者模型】写,保留作历史与素材;skill 现状以 `SKILL.md` + `data/_shared/teaching-loop.md` 为准。插件/雷达/课程包等多数已被"主动教练"单点吸收。

---


> 来源:规划 workflow `plan-english-learning-products`(4 路探索 + 批判 + 综合,6 agent)。严格套用 `references/research/02-generalization-principle.md` 的领域无关架构。
> 调研事实地基见 `references/research/`。

## 统一愿景(system thesis)

**"把朋友(AX)武装成一个永不变监工的零评判私教,让学习者在自己已有的娱乐流里,靠 AI 降维成 i-1 的英文,不痛苦地『撞见』英语而非背单词。"**

三层系统:

```
① 方法论内核层(领域无关) ─── coaching skill 内核:诊断 / 8 原则 / 陪伴话术 / 反监工护栏 / 进度仪式
        ↓ 实例化                【keystone — 没有它,插件只是翻译器、雷达只是推送、清单只是 todo】
② 垂类 playbook 层 ────────── playbooks/english(4 窄场景判定 / Hu&Nation 阈值 / AI-English Lite 种子库 / 降维 prompt)
        ↓ 调用                  英语是首个 playbook,编程/健身/乐器后续可插拔
③ 工具/执行件层(英语特有) ── 「懂了」插件(学习者端阅读执行器) + 窄窗雷达(内容供给器) + 学 AI 中文降维课程包
                                全部复用 playbook 里同一个 i-1 降维能力 + 同一套多 provider 抽象,绝不各自重造
```

**Keystone = coaching skill 内核 + 英语 playbook。** 其余是配件。系统连贯的前提是先画这张三层依赖图,否则会做出四个互相重叠的孤岛。

---

## 产品 1:coaching skill(keystone)

- **命名**:`learning-coach`(内核领域无关)+ `playbooks/english/`(首个垂类,MVP 唯一实现)。**不要叫 `english-learning-coach`。**
- **scope**:一个跑在 **AX 自己 Claude Code** 里的**陪伴者工具箱**。AX 按需触发,产出可直接复制粘贴转发给朋友的弹药——i-1 降维材料、归因重置/降焦虑话术、AI-English Lite 种子库取用。**学习者本人永远零接触、不安装、不登录、不面对任何学习工具。**
- **谁用**:直接用户=陪伴者 AX(自己 CC 里,可用梯子、跑高质量模型);受益人=学习者(只在微信里被动收到 AX 转发的内容)。把工具装在唯一可控的人一侧——研究结论 #9 的直接落地,从架构上消除"她要应付的负担"。
- **核心能力**:
  1. **内容降维器**:AX 丢任意英文 → 出 i-1 三栏(简化英文 + 中文兜底 + 3-5 个重点词只标不要求记)+ 已填好的豆包/DeepSeek 改写 prompt + 国产无梯入口。system prompt 强约束"只用最常见 ~2000 词、句更短、不引新难词"逼近 i-1。
  2. **归因重置 & 降焦虑话术库**:按场景(启动谈话 / "我又学不会了" / 连断两天 / plateau / 她想自测)给口语化零评判回话模板 + reframe voice 指南(防变鸡汤说教)。
  3. **AI-English Lite 种子库检索**:50 词 + 10 prompt 模板 + Elements of AI/AI for Everyone 中文课程线 + AI 安全核查观。框架永远是"给朋友当工具用、不背";AX 要生成背诵词表会被劝阻。
  4. **反监工护栏(领域无关内核)**:拒绝输出任何含查岗/纠错/打卡语气的措辞;面向她的产物都是"我刷到个好玩的,你瞄一眼觉得讲啥?"式开放零对错邀请。
- **交互**:AX 在 CC 说"陪练官""给朋友降维这段""她说她又学不会了怎么回""取个降维 prompt"等触发;每次产出一段可直接复制到微信的中文内容或 AX 照着说的话术。跑在 AX 的 CC 主会话(skill,非独立 agent/后台 daemon)。状态(MVP 后再加):本地 JSON,朋友用代号、不存真名、不上传。
- **明确不做**:不追踪学习者、不推送、不问"学了吗"、不统计连续天数当 KPI;**不向 AX 展示她的行为统计(哪怕正向数据)——防 AX 自己变监工的结构性护栏**;不做学习者端日常陪练 agent/bot/小程序;不生成背诵词表/SRS/抽认卡;不把方法论硬编码进英语。
- **MVP**:只做两个动作(内容降维器 + 归因重置话术库覆盖启动谈话 + 5 个高频卡点),纯 prompt + data/ 知识库,无联网无状态无 py,一周内可落地,与 `banxian-skill` 同构。目录从一开始就分层。验证假设:"武装陪伴者比直接给学习者工具更有效" + "i-1 降维 prompt 能否产出她看得懂的材料"。

## 产品 2:「懂了 Donglle」AI 理解优先阅读器(浏览器插件)

- **build vs extend**:**fork 并扩展 Read Frog**(github.com/mengxi-ream/read-frog,GPLv3/WXT/MV3)。不全新构建、不只做多模型网关。
  - 沉浸式翻译官方闭源(老开源版 2023-01 已 archive);Read Frog 定位就是"AI 语言学习扩展",已具备 WXT/MV3、Vercel AI SDK 接 20+ provider、自定义 OpenAI-compatible endpoint、YouTube 字幕、按等级解释、selection toolbar——最烧时间的脏活已完成。
  - **关键判定**:值得做,但**只有当它真正实现 i-1 降维楔子时才值得做**;若退化成"沉浸式翻译 + 选模型 + 选 Azure"=纯重造轮子(沉浸式翻译 2000 万用户、已 100% 支持最新模型 + 自填 OpenAI-compatible)。
- **MVP features**:① 选中英文 → 强模型三栏改写(simplified_en/zh/key_words[],用 generateObject + Zod 硬约束)——**唯一真楔子:英文改写成"偏易但仍是英文"而非替换成中文**;② "懂了"按钮 → 写本地 IndexedDB 零评判正向清单(只记你懂了什么);③ 渐隐式撞见高亮(见得越多越不标,反 Anki,纯被动信号,禁主动召回弹窗/禁"复习"字样);④ provider 默认 DeepSeek 国产直连 + Options 暴露 base_url/key/model + Azure OpenAI-compatible;⑤ 只做网页 + 复用 Read Frog 的 YouTube 字幕;学习者侧只有"降维""懂了"两个按钮,key/provider 配置藏在 AX 用的高级设置(AX 预配好导出 JSON 给朋友)。
- **多模型网关**:继承强化 Read Frog 的 Vercel AI SDK 架构。原生 provider 用 `@ai-sdk/openai|anthropic|google`;所有 OpenAI 兼容端点(DeepSeek/Kimi/Azure/自建)统一走 `@ai-sdk/openai-compatible` 的 `createOpenAICompatible({baseURL,apiKey,name})`(DeepSeek `api.deepseek.com/v1`、Kimi `api.moonshot.cn/v1` 墙内直连、Azure `RESOURCE.openai.azure.com/openai/v1/`)。key 存 `chrome.storage.local` 不出本地。按场景路由:fastModel(划词,便宜)vs strongModel(整段降维,需强改写)。
- **学习专属功能(超出沉浸式翻译/Language Reactor)**:整段 i-1 降维三栏(最大且唯一硬差异化)/ 渐隐撞见追踪 / "今天懂了"正向清单 / AI 安全核查按钮(v2)/ 理解优先字幕折叠听力降级(v2)/ B站字幕(v2)/ 学习者零配置模式。
- **技术栈**:WXT + React + TS;Vercel AI SDK + `@ai-sdk/openai-compatible`;`chrome.storage.local`(配置/key)+ IndexedDB(Dexie)(撞见词频/今天懂了),纯本地不建后端;降维用 generateObject + Zod。落点 `devtools/donglle/` 或姊妹仓库。**i-1 降维抽成可复用模块(供雷达/快捷指令复用),不做成独立 API。**
- **中国可访问性**:默认国产直连或 AX 的 Azure 部署(墙内可直连);Gemini/OpenAI/Claude 仅 AX 有梯子时可选,绝不设为学习者默认。**关键不确定性(写任何插件代码前必须先盲测):国产无梯模型做整段英文→i-1 简化英文的改写质量是否够格。** 隐私:降维要把原文发给第三方 API(key 本地但内容出网),UI 明示 + 提供 Ollama 本地兜底。
- **effort**:MVP=L;完整版=XL。**GPLv3 传染**:衍生作品须同样开源——自用 + 开源 skill 仓库契合,但锁定"永不闭源商业分发"。

## 其他产品(已排序,砍掉冗余)

| 产品 | effort/impact | 一句话 | 定位 |
|---|---|---|---|
| **学 AI 中文降维课程包** | M / high | Elements of AI / AI for Everyone 中文降维陪读,"学 AI 主线 + 英语副产品" | 与 coaching 互补(管"学什么");规避"中文内容当天有"证伪;做成 playbooks/english 子模块,复用降维能力 |
| **窄窗雷达 Narrow-Window Radar** | L / high | 只在真实 4 窄场景命中时给 AX 推"英语让你今天比中文圈早知道"的卡片,其余沉默 | 动机引擎的内容供给器(替代被砍的行为看板);**highest 证伪风险**(误判→动机塌),判定宁可漏报,**放最后** |
| **游戏截图→AI 降维快捷指令** | S / medium | 玩英文剧情游戏看不懂→截图一键调豆包讲解 | 嫁接游戏;诚实:增量只是"省 3 步打字"(豆包自带拍照翻译),nice-to-have |
| **「今天懂了」捕手** | S / medium | 学习者侧零摩擦的只增不减进步清单(嫁接文件传输助手习惯) | 警告:逼近"学习者端"红线;MVP 阶段先由 AX 在 skill 里手动维护,验证她愿意主动回"今天懂了"后再做端 |

## 推荐开建顺序

> **盲测 → skill 内核(keystone) → 课程包 → 插件 → 雷达**

- **第 0 步｜i-1 降维质量盲测(写任何代码前,1-2 天,零成本最高杠杆)**:3-5 段真实英文 AI 内容,分别用 Claude/GPT(梯子)和 DeepSeek/Kimi(国产无梯)+ generateObject + 词频约束做改写,人工盲评谁真达到 i-1。**这是整个系统的命门假设**;国产不达标则"学习者端无梯"与"i-1 质量"冲突,插件路线要重想。
- **第 1 步(keystone)｜coaching skill 内核 + playbooks/english MVP**:两个动作(降维器 + 话术库),纯 prompt + data/,一周可落地,目录从第一天分层。先做 skill 不做插件——skill 是 M、插件是 L/XL,且 skill 验证更上游更便宜的假设;降维 prompt 验证通过后直接搬进插件后端复用。
- **第 2 步｜学 AI 中文降维课程包**:playbooks/english 下做 Elements of AI / AI for Everyone 中文陪读,复用已验证降维能力,无新技术依赖。
- **第 3 步｜「懂了」插件 MVP**:fork Read Frog,只加"降维"+"懂了"+ 渐隐撞见高亮,默认 DeepSeek 直连,学习者侧两个按钮。只在第 0/1 步降维 prompt 验证可用后做。
- **第 4 步(最后,且只在动机引擎验证为真窄场景后)｜窄窗雷达**:ax-radar/Tavily 双语信源比对 + 保守的 4 窄场景判定。

## AX 必须拍板的决策点

1. **架构与改名(不可逆)**:coaching skill 是否从第一天就做成 domain-agnostic 内核 + `playbooks/english` 两层?(决定 `english-learning-coach/` 是否现在改名 `learning-coach/`)。**建议:从一开始就分层**(边际成本低,返工贵)。
2. **学习者端模型质量 vs 无梯红线(盲测后定)**:若国产无梯模型 i-1 质量明显弱,选 (a) 坚持国产接受打折 / (b) 学习者端也走梯子+高质量 / (c) AX 端高质量预生成再转发成品。
3. **陪伴者数据可见性红线**:是否同意系统**永不**向 AX 展示她的行为统计(撞见词频/使用频率/连续天数),哪怕正向?**建议:焊死**(防 AX 自己变监工;AX 唯一该看的是她主动发来的"今天懂了")。
4. **GPLv3 传染(fork 即锁定)**:确认将来不把"懂了"做成闭源商业产品?现在 fork Read Frog 即锁定开源路径。
5. **范围/投入**:先只验证 keystone(skill MVP,一周,M),还是已决定做完整插件(L+)?**建议:先 skill MVP**。

## 风险清单(节选)

- **i-1 降维质量=整个系统命门** → 第 0 步盲测先行 + generateObject+Zod+词频约束 + AX 转发前自检。
- **不先分层会做出四个重叠孤岛** → i-1 降维抽成一个可复用模块,**不做独立 API**(批判明确否决独立后端)。
- **监工复活的结构性风险** → 撞见词频/陪伴者看板等"她的行为"数据全删,内容供给改由窄窗雷达(外部信号)提供。
- **撞见高亮滑向温和版抽认卡** → 纯渐隐被动信号,禁主动召回弹窗/禁 Anki 默认导出/禁"复习"字样出现在学习者侧。
- **窄窗雷达假阳性=动机命门** → MVP 不做;做时判定从严宁可漏报;放最后。
- **依赖 AX 持续发力**(唯一可控点,可接受;可选 AX 端 /loop 每周自我提醒,绝不变对朋友的定时推送)。
- **隐私/数据出境**(原文发第三方 API)→ UI 明示 + Ollama 本地兜底,AX 替她拍板。
- **范围蔓延回"她直接用"的诱惑** → SKILL.md 顶部写死"学习者零接触"红线。
- **话术失真变说教** → reframe voice 指南,AX 人工过 voice。
- **Read Frog 上游 rebase 成本**(迭代快)→ 只挂 public extension point(selection toolbar/storage)。
- **模型 ID 漂移** → 写代码前用 claude-api / vercel:ai-sdk skill 或 context7 重新核实最新 ID,勿用记忆里的旧 ID。
