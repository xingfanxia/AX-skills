/**
 * Promo-video copy registry. Source of truth is docs/index.html card copy —
 * keep the name / role / id / source strings in sync with the showcase cards.
 * Genericized per repo rules: no real infra IPs / tokens; product + blog
 * domains are allowed.
 */
export type Skill = {
  /** composition id + showcase dir slug */
  id: string;
  /** card index, e.g. "01" */
  num: string;
  /** Chinese display name (big serif) */
  name: string;
  /** role line (mono kicker), may contain a · separator */
  role: string;
  /** one-line hook shown large after the title */
  tagline: string;
  /** exactly three capability points */
  points: [string, string, string];
  /** attribution: 源自 / 配套 / 改进自 / 原创 */
  source: string;
};

export const SKILLS: Skill[] = [
  {
    id: 'banxian',
    num: '01',
    name: '半仙',
    role: '三合一东方占卜 · 赛博半仙',
    tagline: '一句话描述事情，智能起卦',
    points: [
      '智能起卦 · 一句话描述 → 自动布局',
      '真算法引擎 · 64 卦 / 26 单测',
      '守规矩的解读 · 不跑偏、不胡说',
    ],
    source: '源自 盘盘猫 · panpanmao.ai',
  },
  {
    id: 'jewelry',
    num: '02',
    name: '珠宝营销',
    role: '珠宝营销 · 一键生成',
    tagline: '一张商品照，一套小红书素材',
    points: [
      '12 张小红书营销图',
      '6 种风格文案 + 商品分析',
      '约 $0.48 · 5 分钟出片',
    ],
    source: '源自 识川 · shichuan.ax0x.ai',
  },
  {
    id: 'game',
    num: '03',
    name: '游戏剧本',
    role: '游戏剧本创作 · 全流程陪跑',
    tagline: '从一个模糊灵感，到完整剧本',
    points: [
      '世界观 / 主题 / 主线成型',
      '人物 / 场景剧本逐步落地',
      '陪非职业创作者一步步写出来',
    ],
    source: '原创 · 适配所有游戏类型 · 中文为主',
  },
  {
    id: 'proxy-node-setup',
    num: '04',
    name: '翻墙节点',
    role: '自建翻墙服务 · sing-box 多协议',
    tagline: '从零装，或克隆一台节点',
    points: [
      'sing-box 五协议 + Reality 伪装',
      'nginx 订阅分发',
      '端到端 · 一套可复现流程',
    ],
    source: '配套 blog.ax0x.ai · runbook',
  },
  {
    id: 'dr-sharp',
    num: '05',
    name: '犀利博士',
    role: '诚实高于善意 · 深度自审协议',
    tagline: '把 LLM 变成一把心理手术刀',
    points: [
      '揭示隐藏叙事 / 根本矛盾',
      '照见反复掉进的毒性循环',
      '对模式锋利 · 对人不残忍',
    ],
    source: '改进自 秒秒Guo · Dr. Sharp',
  },
  {
    id: 'trident',
    num: '06',
    name: '三重心智',
    role: '深度阅读 · 三重视角',
    tagline: '一篇文章，读出三个视角',
    points: [
      '建构者 · 抽出核心框架',
      '挑战者 · 找最强反驳',
      '实践者 · 落到自己的行动',
    ],
    source: '改进自 秒秒Guo · 三重心智',
  },
  {
    id: 'serenity-bottleneck-research',
    num: '07',
    name: '瓶颈研究',
    role: '投资研究 · 瓶颈拆解',
    tagline: '把产业叙事，拆成可证伪的结构',
    points: [
      '约束 + 证据分级 L0–L4',
      '反身性过滤 + 证伪条件',
      '蒸馏方法 · 不蒸馏持仓',
    ],
    source: '配套 blog.ax0x.ai',
  },
];

export const SKILL_BY_ID = Object.fromEntries(SKILLS.map((s) => [s.id, s]));
