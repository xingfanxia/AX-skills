# scripts/ —— 可选硬化层（把不变式 code 化）

这些脚本是 **可选** 的。`web-novel-writing` 默认能在 "Agent 驱动 mode" 下零搭建运行——让 Codex/Claude Code 按 `SKILL.md` 亲自当 driver。但**书越长，"靠 agent 自律"越靠不住**（agent 本身就是会漂移的那一环），这时把确定性步骤交给脚本强制，是对抗"伪约束"（把硬约束写进 prompt 当成已执行）的关键。

> 头号反模式提醒：任何 MUST-hold 不变量（伏笔到期 / Canon 枚举 / 境界单调 / AI 味 / 可见性过滤 / 状态合并）**必须由 code/schema/lint 强制，不能写进 prompt 当已执行**。这就是这些脚本的存在理由。

## 依赖

```bash
pip install pyyaml      # 唯一依赖；compile_prompt/state_check/state_apply/output_check 用到；antislop_lint/degeneration_check 无依赖
```

无 SQLite / 无向量库 / 无网络 / 无模型调用——纯函数式确定性工具。`python3 + PyYAML` 足够。

## 六个脚本

### `compile_prompt.py` —— 防泄漏的单章 prompt 编译器（最高价值）
从状态文件 + 章纲确定性地编译单章 prompt：按 `visible_from_volume`/`valid_until_chapter` **过滤剧透与过期事实**、选择性注入、指令/正文三区分离、末尾硬拼"只输出正文"后缀 + **反编造 hard_rule**（不得新增设定/猜测隐藏真相）。
```bash
python3 compile_prompt.py <book_dir> <chapter-outline.json> --current-volume 1 --current-chapter 12
```

### `output_check.py` —— 章节正文输出侧机械门
对【章节正文本身】做纯 code 硬门：字数区间 / **残留指令符号·工程词泄漏**(`no_prompt_leak`) / **标点纪律**(正文禁破折号 ——) / **`must_not_absent`**(禁现具名词) / **`no_future_spoiler_out`**(剧透-出闸，与 compile 的剧透-入构成双闸) + 启发式 advisory(POV·解释腔 Gate G / must_happen 必要非充分 / 章末钩子落尾 / 开篇阈值)。
```bash
python3 output_check.py 正文.txt --contract <book>/contract.yaml --outline ch.json --chapter 12 [--whitelist <book>/.deslop-whitelist]
```

### `degeneration_check.py` —— 模型退化检测（移植自 oh-story-claudecode/story-deslop, MIT）
抓"退化的模型自己报不出来"的指纹：**复读/打转**(长句重复≥3次/紧邻整行重复) / **截断**(末尾无收尾标点) / **占位符·拒绝语**(作为AI/我无法继续/乱码) / **工程词泄漏**(细纲/卷纲/情节点 tier1) / **字节地板**(<200字节疑似 Write 静默失败)。对话/弹幕/排比豁免。**blocking=去AI味改不掉，回去重新生成那段。**
```bash
python3 degeneration_check.py 正文.txt --fail-on=blocking
```

### `antislop_lint.py` —— 反 AI 味·词句层（桶1）机械探测
看密度不看单次：机械连接词/论文体/翻译腔/表情心理模板/判断虚词 + **鲁棒「不是A而是B」检测**(★★★★★最毒，排除 是不是/只是/可是/不是A就是B/…是吗) + **弱化副词密度**(微微/淡淡>3千字) + 碎句号/长段落/节奏匀速。词表/检测逻辑借鉴 oh-story banned-words.md。
```bash
python3 antislop_lint.py 正文.txt [--whitelist <book>/.deslop-whitelist]  # 退出 1=AI 味偏重；--json 出 penalty(0-20)
```

### `state_check.py` —— 状态层不变式校验器（每卷边界/发布前体检）
机检：Canon 枚举 / 可见性 / 境界在阶位表 / **伏笔逾期·临近·密度** / **情绪债久未释放·释放不解气** / **未决连续性冲突(cursor.pending_conflicts)** / glossary 别名冲突。
```bash
python3 state_check.py <book_dir>          # 退出 0=无 error；1=有 error
```

### `state_apply.py` —— 定稿后确定性合并 delta 进 canon（关掉 state-mutation 侧伪约束）
合并代数骨架借鉴 WebNovelOps，字段绑定适配本 skill schema：**canon_status:Inferred 代码盖戳**(Canon 晋升仍人确认) / **章级幂等**(同章重跑整体 no-op，护数值 delta) / **只失效不删**(world_fact invalidate) / **阶位单调** / **字段白名单**(拒写人设/Canon 字段) / **audit-pass 提交闸**(坏章不污染 canon) / **人类门** / **checkpoint** / **收尾跑 state_check 自校验**(破则非零退出)。
```bash
python3 state_apply.py <book_dir> delta.yaml --final 定稿.txt --audit-passed   # 见 templates/state-delta-template.yaml
python3 state_apply.py --self-test                                            # 内置 golden fixture
```

### `test_lint_fixtures.sh` —— 检测器 golden-fixture 回归（把脚本调到"敢用"）
正样本必命中、负样本（弹幕道歉×3/排比/either-or/句尾吗/连词尾/纯对话短句）**必静默**——直击"工具误伤多"痛点。
```bash
bash test_lint_fixtures.sh   # 退出 0=无回归
```

## 在循环里怎么接

```
outliner → chapter-outline.json
  └─ compile_prompt.py ──► 单章 prompt ──► writer(关thinking) ──► 草稿正文
       ├─ output_check.py ──► 正文硬门(字数/泄漏/标点/must_not/剧透-出)
       ├─ degeneration_check.py ──► 退化 blocking ? 回去重生成那段 : 继续
       ├─ antislop_lint.py --json ──► penalty(0-20)
       └─ continuity-checker(独立子agent,吃canon) + reviewer(独立子agent,rubric)
            └─ final = LLM加权分 − penalty；final≥80 且硬门全清 ? 定稿 : 定向改稿(≤3轮)
       定稿 ──► 抽 delta ──► state_apply.py --audit-passed(确定性合并,审校没过拒绝提交) ──► 每卷跑 state_check.py
```

## 硬化纪律 + 满配参考

- **共享检测逻辑只住一处（脚本）**：若以后想加 hook 自动触发，hook 只 **subprocess 调用这些脚本**，**绝不把正则手抄进 hook**。这样永远不需要"多副本同步/parity CI"那套膨胀（那正是某些重型工具的分发税）。一条铁律换掉一整套 CI 守卫。
- **满配可执行 CLI 参考**：想要"provider 抽象 + 整树 schema 校验 + init/run-chapter/status 5 命令"的满配硬化实现，见 `docs/research/external-webnovelops-deliverable/`（另一 agent 独立交付的 WebNovelOps，可 pip 装 + pytest 全绿）。**本 skill 的 6 脚本是其最小子集**——默认 agent 驱动够用，书越长越值得上 state_apply。
- **去 AI 味满配参考** + 原始词表/检测器：`docs/research/external-ohstory-deslop/`（oh-story-claudecode/story-deslop, MIT）。

脚本只做"确定性可判"的部分；语义级一致性、文学质量、爽点是否真兑现，仍由独立 LLM reviewer 判。**确定性 oracle 兜底 + LLM 软判**。
