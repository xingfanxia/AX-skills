# 四方调研交叉验证总结(产品设计的事实地基)

> 四份独立调研:① AX dynamic workflow(见 `01-ax-workflow-plan.md`);② Claude/compass(见 `external/02-claude-compass-research.md`);③ ChatGPT(见 `external/03-chatgpt-research.md`,补充约束后的 Part 2);④ 本文件=交叉验证。
> 跨三个不同模型/调研路径独立收敛 → 高置信。任何产品(skill / 浏览器插件 / 其他)都应建立在以下事实地基上。

## 一、四方独立收敛的共识(当定论)

1. **不能移植"朋友式"方法**(现成兴趣 + 词根建模 + 上下文推断)。
2. **是动机 / affective filter 问题,不是智力** → 降焦虑优先于一切内容。
3. 理论底座一致:**Krashen 情感过滤 + 可理解输入 + SDT 三需求(自主/胜任/归属)+ Fogg B=MAP / Tiny Habits / habit stacking + Lally「漏一天无碍」**。
4. **删掉死记硬背**,词汇靠语境高频复现自然习得(incidental)。
5. **嫁接到抖音 + 游戏**(且只切剧情/文本密集型游戏)。
6. **AI 是杀手工具**:把英文内容**降维成可理解输入** + 当**零评判私教** + 把"学 AI"和"学英语"合并(instrumental motivation 工具型动机)。
7. **理解优先,口语/输出后置**。
8. **低负荷、长期、起点极小**。
9. **朋友 = 陪伴者/系统设计师,不是老师/监工/纠错机**。
10. **窄输入/领域聚焦(AI 词汇)是捷径而非难点**。

## 二、外部两份补充的、值得吸收的具体资产

1. **更硬的"为何朋友方法不能移植"证据(Claude 份)**:Hu & Nation (2000,2023 复现)——文本覆盖率 80% 时阅读理解「几乎不可能」,靠上下文猜词需 **95–98% 覆盖率**。这是朋友"上下文推断法"对她在认知上跑不起来的硬原因。配套 Nation & Waring:最高频 ~2000 词覆盖 80%+ 文本,根本不用背几万词。
2. **「AI-English Lite」具体抓手(ChatGPT 份)**:50 个最高价值词(AI 操作词 explain/summarize/translate/generate… + AI 概念词 model/prompt/agent/hallucination… + 游戏界面词 settings/weapon/upgrade…)+ 10 个 prompt 模板。
   - ⚠️ **必须换框架用**:不是"50 词表让她背",而是她每天操作 AI 时自然反复用到的操作词,**用中眼熟(incidental)**。这是给朋友的种子库,不是给她的背诵任务。
3. **"学 AI"本身的课程线(ChatGPT 份)**:Elements of AI / Andrew Ng「AI for Everyone」/ Google AI Essentials(面向非技术人群,有中文/可 AI 翻译);**明确不要**从 ML/Python/Kaggle/HF Agents 开始(过载=新失败体验)。
4. **AI 安全/核查观(ChatGPT 份)**:hallucination 意识 + `What is your source? Is this recent?`——她拿 AI 当信息源,第一天就要建立。

## 三、AX workflow 比外部两份更严谨之处(产品要坚持的)

1. **国产无梯子纪律(最大分歧,AX 对)**:外部两份大量推荐 ChatGPT/Claude/YouTube/Language Reactor/Dreaming English——**全需梯子**,对零动机者第一步就翻墙=致命摩擦。坚持国产主路径,做等价替换:
   | 外部推荐(需梯子) | 换成(国产直连) |
   |---|---|
   | ChatGPT / Claude | 豆包 / DeepSeek |
   | Language Reactor | 沉浸式翻译(引擎 DeepSeek) |
   | YouTube CI 频道 / Dreaming English | B站慢速 up 主 + 双语字幕 AI 科普 |
   | 官方 AI blog | 中文镜像(openai.xiniushu.com / aidoczh.com) |
2. **"2026 年英语信息边际收益很窄"(只有 AX 查漏抓到)**:中文 AI 内容 90% 当天就有,"英语让我多知道"只在 4 窄场景成立(发布滞后/小众工具/个人英文博客/避二手失真)。第一次"领先体验"必须安排在真场景,否则被证伪→动机塌。**这是动机引擎的命门。**
3. **i-1 而非 i+1**(低信心者留存率>学习速率)。
4. **听力降级不计分;跳过正式 phonics 模块 + CEFR 测试**(ChatGPT Part 1 的结构化课元素)。她目标是"读懂",读不需要会发音;phonics=学习任务可能复活失败感;CEFR=温和版考试踩应试创伤。发音将来真想说时随内容自然吸收。
5. ChatGPT 的 **Part 1**(phonics/CEFR/词块卡/British Council A1 结构化 12 周课)基本被其**自己的 Part 2** 推翻——拿到"抖音+游戏+学AI+低负荷"约束后也转向"用 AI 打开信息世界、英语只是插件"。Part 1 当参考,非主线。

## 四、合流后的最终立场(任何产品的需求来源)

**骨架与纪律取 AX**(国产无梯 + 2026 边际收益诚实 + i-1 + 听力降级 + 陪伴者设计)**⊕ 吸收三样外部资产**(Hu&Nation 硬证据 + AI-English Lite 操作词/prompt 种子库 + Elements of AI/AI for Everyone 课程线 + AI 安全观)。

对原 AX 方案的两处实质升级:
1. 第 3 阶段(读 AI 资讯)具体化为:配 Elements of AI / AI for Everyone(中文)当"学 AI"主线,英语作为副产品被动吸收。
2. 给朋友一份 AI-English 操作词 + prompt 种子库当降维工具箱——**用,不背**。
