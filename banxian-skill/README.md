# banxian-skill 🔮

> 一句话描述事情 → 赛博半仙智能起卦 + 真实算法引擎 + 专业知识库解读 → 守规矩的占卜体验。
> 三合一东方占卜（小六壬 / 梅花易数 / 六爻），算法 + 知识库源自 [panpanmao](https://panpanmao.com) 玄学平台真实业务代码。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple)](https://docs.claude.com/en/docs/claude-code)
[![赛道](https://img.shields.io/badge/繁星计划-邪修脑洞-9b59b6)](https://atomclub.cn)

## 它做什么

打开任意 agent（Claude Code / Codex / OpenClaw），加载本 skill，跟半仙说一句你的事，半仙就给你算一卦：

```
用户问 → ① 边界检测（敏感/模糊/重复） → ② 半仙挑起卦法
       → ③ 收集起卦输入 → ④ 调 py 引擎拿真卦
       → ⑤ 加载相关 knowledge → ⑥ 半仙化解读
       → ⑦ 多轮追问 / 一事一占
```

**底层硬核**：三套算法从 panpanmao TypeScript 移植成纯 Python（≤500 行）。64 卦完整数据、纳甲、六亲、世应、动爻、变卦还原。
**外层邪修**：会用 KPI / 房贷 / 相亲 / 裁员等当代词汇接住你问题的 AI 半仙人设（70% 玄学 + 25% 当代穿插 + 5% 专业骨气）。
**守规矩**：「一事一占」「医不问卦」「问凶不问吉」，敏感话题半仙式软处理含心理援助热线 400-161-9995（强制）。

## 三种方法 · 自动路由

| 方法 | 适用 | 起卦 | 半仙台词 |
|---|---|---|---|
| **小六壬** | 当下小事 / 急事（午饭吃啥、钱包丢哪） | 报数 + 时辰 | 「近事易决，给我随便报个数。」 |
| **梅花易数** | 一念之事 / 随机起念（突然想到 / 抽签） | 报三数 | 「心动起念便是天意。报三个数。」 |
| **六爻** | 重大决策（婚姻 / 跳槽 / 买房 / 官司） | 摇钱 6 次 | 「此事重，须摇钱六遍。心里默念三遍。」 |

半仙根据问题措辞自动挑方法，用户主动指定优先。

## 安装

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
mkdir -p ~/.claude/skills
ln -sf ~/AX-skills/banxian-skill ~/.claude/skills/banxian-skill
pip install -r ~/AX-skills/banxian-skill/requirements.txt
```

唯一依赖：`lunardate`（农历转换）。

## 调用示例

### Agent 自然语言（推荐）

```
> 半仙，我下个月该不该跟现在这家公司续约？
> 半仙看看，暗恋的人到底喜不喜欢我？
> 算一卦，钱包丢哪了？
```

### 手动调 py 引擎

```bash
# 小六壬（报数 7）
echo '{"method":"number","params":{"numbers":[7]},"datetime":"2026-05-06T15:30:00+08:00"}' \
  | python3 scripts/liuren.py

# 梅花（三数 3,7,11）
echo '{"method":"triple_number","params":{"numbers":[3,7,11]},"datetime":"2026-05-06T15:30:00+08:00"}' \
  | python3 scripts/meihua.py

# 六爻（摇钱 6 次：7,8,6,9,7,8）
echo '{"method":"coin","params":{"tosses":[7,8,6,9,7,8]},"datetime":"2026-05-06T15:30:00+08:00"}' \
  | python3 scripts/liuyao.py
```

返回结构化 JSON：

```json
{
  "method": "...",
  "timing": {"datetime_iso": "...", "lunar": "...", "shichen": "..."},
  "result": {
    "primary_keyword": "...",
    "ascii_chart": "...",
    "structured": {...}
  },
  "knowledge_pointers": ["data/liuyao/hexagrams-2.md#益", "..."]
}
```

`knowledge_pointers` 指引 LLM 按需读 `data/` 章节做解读。

## Demo

见 [`examples/`](./examples/)：

- [`01-career-liuyao.md`](./examples/01-career-liuyao.md) — 跳槽问题（六爻 益→既济，含多轮追问）
- [`02-love-liuren.md`](./examples/02-love-liuren.md) — 暗恋（小六壬 小吉，凶吉吉 pattern）
- [`03-lost-meihua.md`](./examples/03-lost-meihua.md) — 丢钱包（梅花 益→家人，体用比和）

所有卦象都是实际跑 py 引擎得到的真实输出。

## 验证算法正确性

```bash
pip install pytest
pytest tests/ -v
```

26 个 pytest 全过，含 panpanmao 算例对账：

- **小六壬**：报数 7 → 月留连 / 日小吉 / 时小吉（panpanmao divineByNumber 算法对账）
- **梅花**：壬申年四月十一日巳时 → 地水师卦上爻动（panpanmao validateTimeQiGua 算例）
- **六爻**：乾为天 / 坤为地 / 老阳动 / 老阴动 / 6 爻 metadata 完整

## 文件结构

```
banxian-skill/
├── SKILL.md                  # 主控（半仙人设 + 7 步流程，含 frontmatter）
├── README.md                 # 本文件（GitHub-facing）
├── requirements.txt          # lunardate 单依赖
├── 商业价值说明书.md          # 200 字（繁星计划用）
├── demo_script.md            # 3 分钟视频脚本
├── package.sh                # 打 submission ZIP 用
├── scripts/
│   ├── _common.py            # 农历 + 八卦 + 五行 + JSON IO
│   ├── liuren.py / meihua.py / liuyao.py
│   └── _lookup/              # 8 卦 / 64 卦 / 纳甲 / 六亲 / 6 神 / 12 时辰 JSON
├── data/
│   ├── _shared/              # voice-style + edge-cases + method-router
│   ├── liuren/               # 6 神 + 时辰 + 五行 + 三宫组合 + 场景
│   ├── meihua/               # 八卦类象 + 64 卦索引 + 体用互变
│   └── liuyao/               # 64 卦详解 (3-part) + 六亲 + 世应
├── examples/                 # 3 个真实卦象 demo 对话
└── tests/                    # 26 个 pytest 单测
```

## 评委 audit 路径（5 分钟看完）

1. **30s** — README.md（本文件）：干嘛 / 怎么用 / demo
2. **1min** — SKILL.md：半仙人设 + 7 步流程
3. **1min** — scripts/：真有算法引擎，不是 prompt 装的
4. **2min** — data/ + _lookup/：真有专业知识，从 panpanmao 移植
5. **30s** — 跑 examples/01：实际效果

## 致谢

底层算法、64 卦数据、纳甲表、六亲规则、6 神知识、玄学风格指南、不占事项规则全部来自 [panpanmao](https://panpanmao.com) 玄学平台真实业务代码。

## 许可

MIT — see [LICENSE](../LICENSE)
