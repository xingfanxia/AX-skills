import type {Session} from './types';

/**
 * Scripted Claude Code sessions — one per deck'd skill. Each shows the skill
 * actually being invoked and doing its work, not a recap of its deck.
 * Genericized per repo rules (proxy uses placeholders; product domains are fine).
 * id === deck slug === R2 filename. web-novel-writing is intentionally omitted
 * (WIP, no deck yet).
 */
export const SESSIONS: Session[] = [
  {
    id: 'banxian',
    title: 'banxian-skill',
    caption: '半仙 · 三合一东方占卜 · 装上即用',
    events: [
      {k: 'sys', text: '~/fortune · claude code'},
      {k: 'in', text: '帮我起一卦：这周适不适合跟老板提涨薪？'},
      {k: 'run', text: '调用 banxian 引擎 · 自动选占法', sec: 1.1},
      {k: 'sys', text: '占法：六爻（决策类 · 需变爻）'},
      {k: 'run', text: '摇钱起卦 · 六轮', sec: 1.4},
      {k: 'out', lines: [
        '  本卦  坎为水  （坎上坎下）  →  变卦  泽水困',
        '  世爻 戊午火 · 应爻 戊子水 · 动爻 六三',
      ]},
      {k: 'run', text: '校验卦象数据 · 64 卦 / 26 单测', sec: 0.9},
      {k: 'out', lines: [
        '',
        '【半仙解读】',
        '坎中实，重险也——提薪如临深渊，时机未到，',
        '强求则陷「困」。六三动：宜守、宜蓄势，',
        '待下月初一阳生，再开口不迟。',
      ]},
      {k: 'done', text: '一事一占 · 医不问卦 · 仅供参考，命由己造'},
    ],
  },
  {
    id: 'jewelry',
    title: 'jewelry-marketing',
    caption: '珠宝营销 · 一张商品照 → 一套素材',
    events: [
      {k: 'sys', text: '~/shop · claude code'},
      {k: 'in', text: '/jewelry-marketing 翡翠平安环.jpg --platform xhs'},
      {k: 'run', text: '识别商品 · 翡翠平安环（飘花 · 糯冰种）', sec: 1.1},
      {k: 'run', text: '商品分析 + 卖点提炼', sec: 1.0},
      {k: 'out', lines: ['  类目 翡翠/平安扣 · 受众 25–40 女性 · 中高端']},
      {k: 'run', text: '出图 · 12 张小红书营销图', sec: 2.0},
      {k: 'out', lines: [
        '  ✓ 封面 ×3   ✓ 场景 ×4',
        '  ✓ 微距 ×3   ✓ 对比 ×2',
      ]},
      {k: 'run', text: '撰写 6 种风格文案', sec: 1.2},
      {k: 'out', lines: ['  种草 · 干货 · 情绪 · 测评 · 故事 · 高级感']},
      {k: 'done', text: '12 图 + 6 文案 + 分析 · 用时 4m52s · 成本 $0.48'},
    ],
  },
  {
    id: 'game',
    title: 'game-script-creation',
    caption: '游戏剧本 · 从一句灵感陪你写完',
    events: [
      {k: 'sys', text: '~/game · claude code'},
      {k: 'in', text: '我想做个「赛博修仙」的游戏，但只有这一句话…'},
      {k: 'run', text: '校准创作者水平 · 轻问答', sec: 1.0},
      {k: 'sys', text: '已定位：非职业 · 偏叙事驱动 · 中文'},
      {k: 'run', text: '共创世界观 · 锁主题锚点', sec: 1.4},
      {k: 'out', lines: [
        '  世界观 灵气被数字化的近未来，修真即算力',
        '  主题   在被量化的命运里，何为「道心」',
      ]},
      {k: 'run', text: '铺主线 · 立人物 · 写场景脚本', sec: 1.6},
      {k: 'out', lines: [
        '  主线 7 幕 · 主角/反派/引路人 3 卡 · 首场景脚本',
        '  Canon 状态已记账 → 人设不漂移、伏笔不丢',
      ]},
      {k: 'done', text: '从一句话 → 可开写的剧本骨架 · 全程陪跑'},
    ],
  },
  {
    id: 'proxy-node-setup',
    title: 'proxy-node-setup',
    caption: '翻墙节点 · 从零自建，一套可复现',
    events: [
      {k: 'sys', text: '~/ops · claude code'},
      {k: 'in', text: '帮我从零搭一台翻墙节点，要抗封锁'},
      {k: 'run', text: '检测系统 · 安装 sing-box', sec: 1.2},
      {k: 'run', text: '配置五协议 · VLESS-Reality 伪装', sec: 1.6},
      {k: 'out', lines: [
        '  ✓ VLESS-Reality   ✓ Hysteria2   ✓ TUIC',
        '  ✓ Trojan          ✓ Shadowsocks',
        '  Reality SNI 伪装 → tw.example.com（脱敏）',
      ]},
      {k: 'run', text: 'nginx 订阅分发 + TLS 证书', sec: 1.2},
      {k: 'out', lines: ['  订阅地址  https://<你的域名>/sub/<token>']},
      {k: 'done', text: '端到端可复现 · 配套 blog.ax0x.ai runbook'},
    ],
  },
  {
    id: 'dr-sharp',
    title: 'dr-sharp',
    caption: '犀利博士 · 诚实高于善意的自审',
    events: [
      {k: 'sys', text: '~/ · claude code'},
      {k: 'in', text: '/dr-sharp 我总在快成功时自己搞砸，为什么？'},
      {k: 'sys', text: '已进入深度自审 · 诚实高于善意'},
      {k: 'run', text: '检测危机信号 · 安全底线', sec: 0.8},
      {k: 'run', text: '解构隐藏叙事 + 根本矛盾', sec: 1.6},
      {k: 'out', lines: [
        '  隐藏叙事  「我不配赢」伪装成「我要求高」',
        '  根本矛盾  渴望被看见 ↔ 恐惧被审视',
        '  毒性循环  临门一脚 → 自我破坏 → 印证「果然」',
      ]},
      {k: 'run', text: '荣格镜像 · 阴影对话', sec: 1.2},
      {k: 'out', lines: ['  阴影  那个怕你成功后、无处可藏的小孩']},
      {k: 'done', text: '对模式锋利，对人不残忍 · 这是假设，拿经验去验'},
    ],
  },
  {
    id: 'trident',
    title: 'trident',
    caption: '三重心智 · 一篇文章读出三个视角',
    events: [
      {k: 'sys', text: '~/read · claude code'},
      {k: 'in', text: '/trident 这篇《注意力是稀缺资产》帮我读透'},
      {k: 'run', text: '建构者 · 抽核心框架', sec: 1.2},
      {k: 'out', lines: ['  框架  注意力 = 不可再生资本，复利或破产']},
      {k: 'run', text: '挑战者 · 找最强反驳', sec: 1.2},
      {k: 'out', lines: ['  反驳  稀缺的是「深度」，不是注意力本身']},
      {k: 'run', text: '实践者 · 落到自己的行动', sec: 1.2},
      {k: 'out', lines: ['  行动  ① 单线程时段  ② 输入断舍离  ③ 注意力预算']},
      {k: 'done', text: '三个视角各有交付物 · 不发散成空话'},
    ],
  },
  {
    id: 'serenity-bottleneck-research',
    title: 'serenity-bottleneck-research',
    caption: '瓶颈研究 · 把叙事拆成可证伪的结构',
    events: [
      {k: 'sys', text: '~/research · claude code'},
      {k: 'in', text: '/serenity 把「液冷是 AI 算力刚需」这个叙事拆开'},
      {k: 'run', text: '提取约束 · 物理 / 成本 / 供应', sec: 1.3},
      {k: 'out', lines: ['  约束  单机柜功率密度 > 风冷上限 ≈ 30kW']},
      {k: 'run', text: '证据分级 L0–L4 + 反身性过滤', sec: 1.5},
      {k: 'out', lines: [
        '  L4 财报实证 ×2 · L2 行业访谈 ×3 · L0 卖方研报（降权）',
        '  反身性  这套叙事已经被定价多少了？',
      ]},
      {k: 'run', text: '生成证伪条件', sec: 1.0},
      {k: 'out', lines: ['  证伪  若风冷密度突破 / 浸没成本不降 → 推翻']},
      {k: 'done', text: '蒸馏方法不蒸馏持仓 · 输出待验证假设，非买卖建议'},
    ],
  },
];

export const SESSION_IDS = SESSIONS.map((s) => s.id);
