# AX Skills · 展示站点 (GitHub Pages)

GitHub Pages 站点，托管各 skill 的展示 deck + 一个路由 landing page，每个 deck 还配一支动画宣传片（Remotion 生成，源码在仓库根 `remotion/`；mp4 托管在 R2，不进仓库）。

**🔗 Live: https://xingfanxia.github.io/AX-skills/**

发布配置：GitHub Pages → Source = `main` 分支 `/docs` 目录（legacy branch build，push 即自动重发布）。
> 仓库根 `CLAUDE.md` 是 agent 约定的唯一真源（风格 / 加新 deck 流程 / 脱敏与命名规则）。

## 结构

```
docs/                       ← Pages 站点根
├── index.html              # 路由 landing（卡片网格；每卡有「▶ 影片」灯箱，视频从 R2 流式播放）
├── .nojekyll               # 关掉 Jekyll，原样发布
├── banxian/                # banxian-skill 展示 deck
├── jewelry/                # jewelry-marketing 展示 deck
├── game/                   # game-script-creation 展示 deck
├── proxy-node-setup/       # proxy-node-setup 展示 deck（节点信息已脱敏）
│   ├── index.html
│   └── assets/             #   motion.min.js（本地兜底）
├── dr-sharp/               # dr-sharp 展示 deck
├── trident/                # trident 展示 deck
└── serenity-bottleneck-research/  # serenity-bottleneck-research 展示 deck
```
> 每个 deck 在 `#home-link` 之后都注入了一段共享的 `#promo-link` 灯箱片段，slug 取自 `location.pathname`，播放 `https://media.ax0x.ai/ax-skills/<slug>.mp4`。

URL 路由：`/AX-skills/` · `/AX-skills/banxian/` · `/AX-skills/jewelry/` · `/AX-skills/game/` · `/AX-skills/proxy-node-setup/` · `/AX-skills/dr-sharp/` · `/AX-skills/trident/` · `/AX-skills/serenity-bottleneck-research/`

## Deck 一览

全部统一 **Style A 电子杂志 · 🌙 沙丘 / Dune**（Playfair + Noto Serif SC，`--ink:#1f1a14` / `--paper:#f0e6d2`），均用 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) 生成，全中文。键盘 `← →` 翻页 · `B` 静态 · `ESC` 索引。

| Deck | Skill | 来源 |
|---|---|---|
| `banxian/` | [banxian-skill](../banxian-skill)（赛博半仙 · 三合一东方占卜） | [盘盘猫 panpanmao.ai](https://www.panpanmao.ai/) |
| `jewelry/` | [jewelry-marketing](../jewelry-marketing)（珠宝营销一键生成） | [识川 shichuan.ax0x.ai](https://shichuan.ax0x.ai/) |
| `game/` | [game-script-creation](../game-script-creation)（游戏剧本全流程创作） | 原创（非产品抽取） |
| `proxy-node-setup/` | [proxy-node-setup](../proxy-node-setup)（自建 sing-box 翻墙服务） | 配套 [blog.ax0x.ai runbook](https://blog.ax0x.ai/proxy-runbook-zh) |
| `dr-sharp/` | [dr-sharp](../dr-sharp)（诚实高于善意 · 深度自审协议） | 改进自 [秒秒Guo · Dr. Sharp](https://mmguo.dev/prompts/dr-sharp/) |
| `trident/` | [trident](../trident)（深度阅读 · 三重视角） | 改进自 [秒秒Guo · 三重心智](https://mmguo.dev/prompts/trident/) |
| `serenity-bottleneck-research/` | [serenity-bottleneck-research](../serenity-bottleneck-research)（投资研究 · 瓶颈拆解） | 配套 [blog.ax0x.ai](https://blog.ax0x.ai/distilling-serenity-zh) |

> 历史备注：banxian/jewelry 曾是瑞士风（IKB / 柠檬黄），后统一迁到沙丘 / Dune Style A —— 以当前文件为准。

## 宣传片（Remotion → R2）

每个 deck 配一支 ~20s 1920×1080 的动画宣传片，与 deck 同款沙丘 / Dune Style A。源码在仓库根 [`remotion/`](../remotion)（`src/skills.ts` 是文案唯一真源，与 landing 卡片文案对齐）。渲染 + 托管：`cd remotion && node scripts/render-all.mjs && node scripts/upload-r2.mjs`，上传到 R2 桶 `ax-blog-media` 的 `ax-skills/` 前缀，经 `https://media.ax0x.ai/ax-skills/<slug>.mp4` 提供（支持 range 请求 → 可拖动）。composition id === deck slug === R2 文件名，全程一致。mp4 不进仓库。

## 加一个新 skill 的 deck（流程）

1. `docs/<skill>/index.html` 放一份 deck —— **照抄一份现有 deck（如 `jewelry/`）当参考做同款**（Style A 沙丘 / Dune，别另起风格）；同级 `assets/motion.min.js`。
2. 在 `docs/index.html` 的 `.grid` 里复制一张 `<article class="card">`，填 `num` / `role` / `h2`+`.id` / 一句话 / `源自`或`配套`链接 / `查看 →` + `源码 ↗`。「▶ 影片」按钮由 landing 的脚本按 slug 自动注入，无需手写。
3. （宣传片，可选）把 skill 追加到 `remotion/src/skills.ts` 和 `remotion/scripts/*.mjs` 的 id 列表，跑 `node scripts/render-all.mjs <slug> && node scripts/upload-r2.mjs <slug>`。新 deck 复制现有 deck 时已带 `#promo-link` 片段，会自动播放对应视频。
4. commit + push，Pages 自动重发布（CDN 有缓存，新路径可能 404 / 旧内容 1–2 分钟，`?cb=` 不顶用，重试即可）。
5. **开浏览器肉眼验收** deck + 宣传片灯箱（grep / validator 不够）。

**红线**：公开仓库 —— 真实节点 IP / 域名 / token 一律脱敏成占位符；产品域名（panpanmao.ai 等）可保留。不要出现 "Funskills / Funskills Roadshow"（历史 bug），这些就是 **AX Skills**。

## 本地预览

直接浏览器打开 `docs/index.html`（纯 HTML/CSS，无需服务器）；deck 同理 `open docs/<skill>/index.html`。
