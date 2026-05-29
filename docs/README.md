# AX Skills · 路演站点 (GitHub Pages)

GitHub Pages 站点，托管各 skill 的路演 deck + 一个路由 landing page。

**🔗 Live: https://xingfanxia.github.io/AX-skills/**

发布配置：GitHub Pages → Source = `main` 分支 `/docs` 目录。

## 结构

```
docs/                       ← Pages 站点根
├── index.html              # 路由 landing（瑞士风，纯 HTML/CSS，列出所有 skill deck）
├── .nojekyll               # 关掉 Jekyll，原样发布
├── banxian/                # banxian-skill 路演 deck
│   ├── index.html          #   IKB 克莱因蓝 · 11 页
│   ├── banxian-roadshow.pdf
│   └── images/             #   真实古卷卦签截图
└── jewelry/                # jewelry-marketing 路演 deck
    ├── index.html          #   柠檬黄 · 11 页
    ├── jewelry-roadshow.pdf
    └── images/             #   真实 skill 输出图
```

URL 路由：
- Landing：`/AX-skills/`
- 半仙：`/AX-skills/banxian/`
- 珠宝：`/AX-skills/jewelry/`

## 两份 deck

| Deck | Skill | 来源产品 | 主题色 |
|---|---|---|---|
| `banxian/` | [banxian-skill](../banxian-skill)（赛博半仙 · 三合一东方占卜） | [盘盘猫 panpanmao.ai](https://www.panpanmao.ai/) | 🔵 克莱因蓝 IKB |
| `jewelry/` | [jewelry-marketing](../jewelry-marketing)（珠宝营销一键生成） | [识川 shichuan.ax0x.ai](https://shichuan.ax0x.ai/) | 🟡 柠檬黄 |

用 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) 瑞士国际主义风生成，每份 11 页全中文。键盘 `← →` 翻页 · `B` 静态 · `ESC` 索引。所有卦象 / 营销图均为真实素材。

## 加一个新 skill 的 deck

1. 在 `docs/<skill-name>/` 放一份 deck（`index.html` + `images/`，可选 PDF）。
2. 在 `docs/index.html` 的 `.grid` 里复制一张 `<article class="card">`，填名称、一句话、来源产品、`--c` 主题色、链接。
3. commit + push，Pages 自动重新发布。

## 本地预览

直接浏览器打开 `docs/index.html`（landing 是纯 HTML/CSS，无需服务器）。deck 同理 `open docs/banxian/index.html`。
