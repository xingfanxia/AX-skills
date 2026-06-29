import type {Reel} from './types';

/**
 * 9:16 skill reels. Numbers/labels grounded in each skill's real SKILL.md.
 * id === composition id === R2 filename (<slug>-v.mp4). Currently jewelry only
 * (proof of the format); other skills get reels once the aesthetic is locked.
 */
export const REELS: Reel[] = [
  {
    id: 'jewelry-v',
    skill: 'jewelry-marketing',
    hookTop: '一张商品照',
    hookMain: '一整套带货素材',
    command: '/jewelry-marketing 翡翠.jpg',
    workCaption: '并行生成 · gpt-image-2',
    grid: [
      'hero', 'wristNeck', 'gemCut', 'sceneWear',
      'flatLay', 'moodboard', 'wearGrid', 'giftScene',
      'priceAnchor', 'meaning', 'knowhow', 'starTest',
    ],
    stats: [
      {value: '12', label: '营销图', count: 12},
      {value: '6', label: '文案', count: 6},
      {value: '$0.48', label: '总成本', emphasize: true},
      {value: '4:52', label: '用时'},
    ],
    punch: '把摄影棚 + 文案团队，压进一条命令。',
    caption: '珠宝营销 · 一张照片，一整套素材',
  },
];
