# AX Skills · 展示站点 (GitHub Pages)

GitHub Pages 站点，托管各 skill 的展示 deck + 一个路由 landing page。

**🔗 Live: https://xingfanxia.github.io/AX-skills/**

发布配置：GitHub Pages → Source = `main` 分支 `/docs` 目录（legacy branch build，push 即自动重发布）。
> 仓库根 `CLAUDE.md` 是 agent 约定的唯一真源（风格 / 加新 deck 流程 / 脱敏与命名规则）。

## 结构

```
docs/                       ← Pages 站点根
├── index.html              # 路由 landing（列出所有 skill deck 的卡片网格）
├── .nojekyll               # 关掉 Jekyll，原样发布
├── banxian/                # banxian-skill 展示 deck
├── jewelry/                # jewelry-marketing 展示 deck
├── game/                   # game-script-creation 展示 deck
└── proxy-node-setup/       # proxy-node-setup 展示 deck（节点信息已脱敏）
    ├── index.html
    └── assets/             #   motion.min.js（本地兜底）
```

URL 路由：`/AX-skills/` · `/AX-skills/banxian/` · `/AX-skills/jewelry/` · `/AX-skills/game/` · `/AX-skills/proxy-node-setup/`

## Deck 一览

全部统一 **Style A 电子杂志 · 🌙 沙丘 Dune**（Playfair + Noto Serif SC，`--ink:#1f1a14` / `--paper:#f0e6d2`），均用 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) 生成，全中文。键盘 `← →` 翻页 · `B` 静态 · `ESC` 索引。

| Deck | Skill | 来源 |
|---|---|---|
| `banxian/` | [banxian-skill](../banxian-skill)（赛博半仙 · 三合一东方占卜） | [盘盘猫 panpanmao.ai](https://www.panpanmao.ai/) |
| `jewelry/` | [jewelry-marketing](../jewelry-marketing)（珠宝营销一键生成） | [识川 shichuan.ax0x.ai](https://shichuan.ax0x.ai/) |
| `game/` | [game-script-creation](../game-script-creation)（游戏剧本全流程创作） | 原创（非产品抽取） |
| `proxy-node-setup/` | [proxy-node-setup](../proxy-node-setup)（自建 sing-box 翻墙服务） | 配套 [blog.ax0x.ai runbook](https://blog.ax0x.ai/proxy-runbook-zh) |

> 历史备注：banxian/jewelry 曾是瑞士风（IKB / 柠檬黄），后统一迁到沙丘 Dune Style A —— 以当前文件为准。

## 加一个新 skill 的 deck（流程）

1. `docs/<skill>/index.html` 放一份 deck —— **照抄一份现有 deck（如 `jewelry/`）当参考做同款**（Style A 沙丘 Dune，别另起风格）；同级 `assets/motion.min.js`。
2. 在 `docs/index.html` 的 `.grid` 里复制一张 `<article class="card">`，填 `num` / `role` / `h2`+`.id` / 一句话 / `源自`或`配套`链接 / `查看 →` + `源码 ↗`。
3. commit + push，Pages 自动重发布（CDN 有缓存，新路径可能 404 / 旧内容 1–2 分钟，`?cb=` 不顶用，重试即可）。
4. **开浏览器肉眼验收** deck（grep / validator 不够）。

**红线**：公开仓库 —— 真实节点 IP / 域名 / token 一律脱敏成占位符；产品域名（panpanmao.ai 等）可保留。不要出现 "Funskills / Funskills Roadshow"（历史 bug），这些就是 **AX Skills**。

## 本地预览

直接浏览器打开 `docs/index.html`（纯 HTML/CSS，无需服务器）；deck 同理 `open docs/<skill>/index.html`。
