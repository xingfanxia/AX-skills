# Funskills 路演 PPT

两份 Funskills 参赛 skill 的路演 deck，用 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)（瑞士国际主义风）生成，单文件 HTML、横向翻页。

| Deck | Skill | 来源产品 | 主题色 |
|---|---|---|---|
| `banxian/` | [banxian-skill](../banxian-skill)（赛博半仙 · 三合一东方占卜） | [盘盘猫 panpanmao.ai](https://www.panpanmao.ai/) | 🔵 克莱因蓝 IKB |
| `jewelry/` | [jewelry-marketing](../jewelry-marketing)（珠宝营销一键生成） | [识川 shichuan.ax0x.ai](https://shichuan.ax0x.ai/) | 🟡 柠檬黄 |

每份 11 页，约 15 分钟路演节奏，全中文。

## 怎么看（重要）

这是**带内联 `<style>` + `<script>` 的单文件 HTML**，必须在**真正的浏览器**里打开：

```bash
open banxian/index.html
open jewelry/index.html
```

- ⌨️ `← →` 翻页 · `B` 静态/动态 · `ESC` 缩略图索引 · 鼠标滚轮 / 触屏滑动
- ⚠️ **不要**用 GitHub 网页预览、Markdown 预览、VS Code 预览、聊天窗口等打开 —— 这些会把 `<style>`/`<script>` 过滤掉，页面会变成无样式的竖排文字（不是 bug，是预览器的限制）。
- 需要随手分享、对方不方便开浏览器时，用同目录的 `*-roadshow.pdf`（每页一张，静态）。

## 结构

```
funskills-roadshow/
├── banxian/
│   ├── index.html              # 主 deck（IKB 克莱因蓝）
│   ├── banxian-roadshow.pdf    # 静态 PDF 备份（11 页）
│   └── images/                 # 真实古卷卦签截图（小六壬/梅花/六爻）
└── jewelry/
    ├── index.html              # 主 deck（柠檬黄）
    ├── jewelry-roadshow.pdf    # 静态 PDF 备份（11 页）
    └── images/                 # 真实 skill 输出（6 张营销图 + 4 张原石设计图）
```

## 说明

- 所有数据、卦象、营销图都是**真实素材**：半仙的 ASCII 卦象由 `banxian-skill` 的 py 引擎实跑（六爻 益→既济），珠宝图来自 `jewelry-marketing` 的真实 bundle 输出。
- 改内容：直接编辑 `index.html` 里 `<!-- SLIDES_HERE -->` 之后的 `<section class="slide" data-layout="Sxx">` 块；校验用 `node ~/.claude/skills/guizang-ppt-skill/scripts/validate-swiss-deck.mjs <file>`。
