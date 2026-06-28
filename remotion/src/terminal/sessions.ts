import type {Session} from './types';

/**
 * Scripted Claude Code sessions — one per deck'd skill. Each shows the skill
 * actually being used, GROUNDED IN ITS REAL SKILL.md (invocation, workflow
 * phases, output structure, persona) — not a marketing recap. Kept ≤16 visible
 * lines (the window height) so no scroll is needed, and to font-safe glyphs
 * only (IBM Plex Mono + Noto Sans SC — no Yijing hexagram chars / emoji, which
 * render as tofu). Genericized per repo rules. id === deck slug === R2 filename.
 */
export const SESSIONS: Session[] = [
  {
    id: 'banxian',
    title: 'banxian-skill',
    caption: '赛博半仙 · 三合一东方占卜 · 守规矩的卜筮',
    events: [
      {k: 'sys', text: '~/oracle · claude code'},
      {k: 'in', text: '半仙，这周适不适合跟老板提涨薪？'},
      {k: 'run', text: '判断问题属性 · 自动选占法（六爻 / 小六壬 / 梅花）', sec: 0.9},
      {k: 'out', lines: [
        '此事关乎前路，贫道为你起一卦六爻。',
        '心里把「提薪」默念三遍，告诉我「开始」。',
      ]},
      {k: 'in', text: '开始'},
      {k: 'run', text: '调用 Python 六爻引擎 · 摇钱模拟天机', sec: 1.3},
      {k: 'out', lines: [
        '六爻 · 坎为水 → 泽水困  （本卦 → 变卦）',
        '世爻 戊午火 · 应爻 戊子水 · 动爻 六三',
      ]},
      {k: 'run', text: '按 knowledge_pointers 加载 data/ 卦辞', sec: 0.8},
      {k: 'out', lines: [
        '卦落坎为水——重险之象，变爻在三化「困」。',
        '提薪若强行，如逆水行舟；宜守、宜蓄势，',
        '待来月阳生再启齿不迟。',
      ]},
      {k: 'run', text: 'render_html.py 渲染古卷卦签 · 自动开浏览器', sec: 1.0},
      {k: 'out', lines: ['卦签已挂上墙 → ./banxian_results/liuyao_坎.html']},
      {k: 'done', text: '一事一占 · 医不问卦 · 天机泄三分，余下七分施主自悟'},
    ],
  },
  {
    id: 'jewelry',
    title: 'jewelry-marketing',
    caption: '珠宝营销 · 一张商品照 → 小红书一套素材',
    events: [
      {k: 'sys', text: '~/shop · claude code'},
      {k: 'in', text: '~/.claude/skills/jewelry-marketing/generate.py 翡翠平安环.jpg'},
      {k: 'run', text: '检测商品类型 · Gemini Vision', sec: 1.0},
      {k: 'out', lines: ['  类型  finished_product · 翡翠平安扣 · 飘花糯冰种']},
      {k: 'run', text: '自动路由 → marketing pipeline', sec: 0.5},
      {k: 'run', text: 'Gemini 商品分析 · 提炼卖点 → analysis.json', sec: 1.2},
      {k: 'out', lines: ['  ✓ analysis.json  材质 / 色彩 / 工艺 / 受众 / 场景']},
      {k: 'run', text: '并行生成 12 张营销图 · gpt-image-2 (concurrency=4)', sec: 2.6},
      {k: 'out', lines: ['  ✓ hero ✓ wristNeck ✓ gemCutDetail ✓ giftScene … 共 12 张']},
      {k: 'run', text: '撰写 6 种小红书文案 → copy.md', sec: 1.1},
      {k: 'out', lines: ['  闺蜜种草 · 专业测评 · 情绪叙事 · 穿搭攻略 · 文化叙事 · 送礼仪式感']},
      {k: 'done', text: '完成 → jewelry_bundle/<时间戳>/ · 成本 $0.48 · 用时 4m52s'},
    ],
  },
  {
    id: 'game',
    title: 'game-script-creation',
    caption: '游戏剧本 · 从灵感到脚本的全流程陪伴',
    events: [
      {k: 'sys', text: '~/game · claude code'},
      {k: 'in', text: '我想做个「赛博修仙」的游戏剧本，但只有这一句话…'},
      {k: 'run', text: 'S0 校准 · 判断创作水平与工作模式', sec: 1.2},
      {k: 'out', lines: [
        '你脑子里最清楚的是哪个——那个世界？还是一个角色？',
        '以前写过故事吗（哪怕同人、小时候）？',
      ]},
      {k: 'in', text: '一个画面：修者指尖点虚空刻阵… 没怎么写过'},
      {k: 'out', lines: ['判定 L1（有想法没技巧）· Pantser · 工作模式 C（给推荐 + 理由）']},
      {k: 'run', text: 'S1 种子定调 → S2 世界观 6 字段画布 → S3 主题句', sec: 1.5},
      {k: 'out', lines: [
        '核心前提 · 灵气被数据化，修真即海量算力',
        '紧张态势 · 旧派修者 vs 新派算法师，争夺「道源」',
        '主题 · 道心因拒绝被量化，在代码与传统碰撞中被守住',
      ]},
      {k: 'run', text: 'S4 主线 · S5 人物 · S6 首场景脚本（交付文档）', sec: 1.5},
      {k: 'out', lines: [
        '✓ main-story-outline.md（三幕 + 伏笔账本）',
        '✓ character-sheet.md（伤口-谎言-渴望-需要）',
        '✓ scene-script.md（序章对白 + 演出层）· Canon 已锁',
      ]},
      {k: 'done', text: '垂直切片完成 · 世界观+主题+主角+首场景 · 可继续迭代'},
    ],
  },
  {
    id: 'proxy-node-setup',
    title: 'proxy-node-setup',
    caption: '翻墙节点 · 从零自建，一套可复现',
    events: [
      {k: 'sys', text: '~/ops · claude code'},
      {k: 'in', text: '我想用 sing-box 搭个翻墙节点，从零开始，要手把手'},
      {k: 'run', text: '启动 proxy-node-setup · 采集必要参数', sec: 1.2},
      {k: 'out', lines: [
        '  需要  域名 · CF_TOKEN · 区域名 · 新主机IP · SSH端口',
        '  ! CF token 别用 /user/tokens/verify 验（会假负）',
      ]},
      {k: 'run', text: '建 DNS 记录（先灰云）· 确认解析', sec: 1.0},
      {k: 'run', text: '选择路径：从零装(sb.sh) vs 克隆参考节点', sec: 0.9},
      {k: 'sys', text: '已选：克隆模式（参考节点已存在）'},
      {k: 'run', text: '拉取参考配置 · 重写 IP + instance_id', sec: 1.3},
      {k: 'out', lines: ['  ✓ /etc/s-box 克隆完成 · sing-box check → CONFIG_OK']},
      {k: 'run', text: 'acme.sh 签 TLS · nginx 订阅分发 + 流量统计', sec: 1.4},
      {k: 'run', text: '端到端验证：外网端口可达 + 真实流量出境', sec: 1.1},
      {k: 'done', text: '配套 blog.ax0x.ai runbook · 验证走外网，别只信 systemctl'},
    ],
  },
  {
    id: 'dr-sharp',
    title: 'dr-sharp',
    caption: '犀利博士 · 诚实高于善意的深度自审',
    events: [
      {k: 'sys', text: '~/ · claude code'},
      {k: 'in', text: '为什么我总在快成功时自己搞砸？'},
      {k: 'run', text: '检测危机信号 · 安全底线', sec: 0.7},
      {k: 'run', text: 'Phase 1 · 深度诊断', sec: 1.3},
      {k: 'out', lines: [
        '  这看起来像一个矛盾：你想成功，但你的结构在维护失败。',
        '  隐藏叙事  「成功 = 被看见」伪装成「我要求太高」',
        '  根本驱动  恐惧暴露 ↔ 渴望成就',
      ]},
      {k: 'run', text: 'Phase 2 · 可行策略', sec: 1.2},
      {k: 'out', lines: [
        '  毒性循环  临界 → 焦虑升高 → 自我破坏 → 退回安全区',
        '  帕累托 80/20  做：定标清单 · 周四体感检点 ｜ 停：完美主义 · 隐性对抗',
      ]},
      {k: 'run', text: 'Phase 3 · 镜中自我', sec: 1.1},
      {k: 'out', lines: [
        '  阴影  「我是那个怕你成功后无处可藏的小孩」',
        '  未来  「成功不是失去保护，而是选择被看见」',
      ]},
      {k: 'done', text: '以上是假设不是判决 · 对不上的地方，恰是你比我更懂你自己'},
    ],
  },
  {
    id: 'trident',
    title: 'trident',
    caption: '三重心智 · 一篇文章读出三个视角',
    events: [
      {k: 'sys', text: '~/ · claude code'},
      {k: 'in', text: '帮我读透这篇《注意力是稀缺资产》，多角度分析'},
      {k: 'run', text: '三重心智 · 建构 / 挑战 / 实践（单次同时输出）', sec: 1.8},
      {k: 'out', lines: [
        '一句话：注意力投向哪里，决定了人生回报的形状。',
        '',
        '【建构者 · 优化「把握 + 延伸」】',
        '  注意力 = 不可再生资本，深度专注才有复利；浏览型时代必然衰减。',
        '【挑战者 · 优化「证伪」】',
        '  最强版本成立，但稀缺的其实是「深度」，不是注意力本身。',
        '【实践者 · 优化「落地」】',
        '  本周可做 ① 单线程时段 ② 输入砍 3 个 ③ 注意力预算表',
        '',
        '综合：稀缺的是 30 天不被打扰的空间——既是限制，也是护城河。',
      ]},
      {k: 'done', text: '三视角各有交付物 · 锋利、具体、不发散'},
    ],
  },
  {
    id: 'serenity-bottleneck-research',
    title: 'serenity-bottleneck-research',
    caption: '瓶颈研究 · 把叙事拆成可证伪的结构',
    events: [
      {k: 'sys', text: '~/research · claude code'},
      {k: 'in', text: '高端 GPU 先进封装是瓶颈论——帮我用 serenity 分析这叙事'},
      {k: 'run', text: '框架化 · 需求波 → 架构变化 → 价值链', sec: 1.2},
      {k: 'out', lines: [
        'AI 算力扩张 → 高功率密度芯片 → 先进封装卡点',
        '研究问题：谁控制封装与基板？市场为何还没定价？',
      ]},
      {k: 'run', text: '分类候选 · Beneficiary / Bottleneck / Chokepoint', sec: 1.3},
      {k: 'out', lines: [
        '高端基板供应  Chokepoint  扩产 5+ 年   证据 L3（财报+客户指引）',
        '封装设备商    Bottleneck  专利+认证壁垒  证据 L2（行业访谈）',
      ]},
      {k: 'run', text: '定价缺口 · 反身性检查', sec: 1.0},
      {k: 'out', lines: [
        '缺口：会计滞后（新收入还藏在通用业务里）',
        '状态：pre-diffusion · 机构覆盖不足',
      ]},
      {k: 'run', text: '证伪框架 + 研究等级', sec: 1.0},
      {k: 'out', lines: [
        '最快推翻：基板良率突破 / 替代工艺出现',
        '评级 B · 架构清晰但缺 L4 财务转化 → 深挖 primary sources',
      ]},
      {k: 'done', text: '蒸馏流程不蒸馏持仓 · 输出可验证假设 + 证伪清单 · 非买卖建议'},
    ],
  },
  {
    id: 'web-novel-writing',
    title: 'web-novel-writing',
    caption: '网文流水线 · 人类当导演，AI 当受约束子程序',
    events: [
      {k: 'sys', text: '~/mybook · claude code'},
      {k: 'in', text: '我用 AI 写玄幻，写到第 5 章人设就漂、伏笔忘填，怎么救？'},
      {k: 'run', text: 'degeneration_check.py 扫崩点 · 划「可信前缀 / 崩坏起点」', sec: 1.0},
      {k: 'out', lines: ['崩坏起点：第 5 章（复读 + 战力越级）· 可信前缀 1-4 章']},
      {k: 'run', text: '反向提取 → typed 状态层（Canon 五态 + 按卷可见）', sec: 1.3},
      {k: 'out', lines: [
        'state-world.yaml        力量阶位表 · 设定打 Inferred 待确认',
        'state-characters.yaml   主角行为锚点 + 认知边界',
        'foreshadow-ledger.yaml  伏笔 3 处 + 补 planned_payoff_ch',
      ]},
      {k: 'run', text: 'compile_prompt.py · 指令/正文分离 + 末尾硬后缀防泄漏', sec: 1.2},
      {k: 'out', lines: ['第 5 章短 prompt：最小 context · 设定包进 strict 块「仅供参考」']},
      {k: 'run', text: 'writer 生成（关 thinking）→ 独立子 agent 审校', sec: 1.5},
      {k: 'out', lines: [
        'continuity-checker  时间线 / 人设 / canon → 0 违规',
        'reviewer  rubric 加权 84 - AI味 penalty 5 = 79（差一点）',
      ]},
      {k: 'run', text: '定向改稿 1 轮 → 去 AI 味独立 pass → state_apply 回写', sec: 1.3},
      {k: 'out', lines: ['final 82 ≥ 80 · 硬门全清 · 第 5 章定稿，状态增量回写']},
      {k: 'done', text: '人类定结构 / AI 填细节 · 一致性靠架构强制，不靠 AI 自觉'},
    ],
  },
];

export const SESSION_IDS = SESSIONS.map((s) => s.id);
