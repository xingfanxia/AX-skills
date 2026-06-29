import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import type {Reel} from '../types';
import {SCENES} from '../types';
import {v, mono, serifZh} from '../theme';
import {EASE, clamp, fade, BrandCorners} from '../ui';

export const EndCard: React.FC<{reel: Reel}> = ({reel}) => {
  const f = useCurrentFrame();
  const op = fade(f, SCENES.end, 10, 8);
  const ap = (d: number) => interpolate(f, [d, d + 14], [0, 1], clamp);
  const rise = (d: number) => interpolate(f, [d, d + 16], [30, 0], {...clamp, easing: EASE});
  const lineW = interpolate(f, [10, 30], [0, 220], {...clamp, easing: EASE});

  return (
    <AbsoluteFill style={{opacity: op, alignItems: 'center', justifyContent: 'center'}}>
      <BrandCorners />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30, textAlign: 'center'}}>
        <div style={{fontFamily: mono, fontSize: 40, letterSpacing: '0.12em', color: v.gold, opacity: ap(4), translate: `0 ${rise(4)}px`}}>
          /{reel.skill}
        </div>
        <div style={{width: lineW, height: 2, background: v.line}} />
        <div style={{fontFamily: serifZh, fontWeight: 600, fontSize: 96, color: v.paper, opacity: ap(14), translate: `0 ${rise(14)}px`}}>
          AX · Agent Skills
        </div>
        <div style={{fontFamily: mono, fontSize: 42, letterSpacing: '0.08em', color: v.dim, opacity: ap(24)}}>
          在 Claude Code 里直接跑
        </div>
        <div style={{marginTop: 26, fontFamily: mono, fontSize: 30, color: v.faint, opacity: ap(34)}}>
          github.com/xingfanxia/AX-skills
        </div>
      </div>
    </AbsoluteFill>
  );
};
