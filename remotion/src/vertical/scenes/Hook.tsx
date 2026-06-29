import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import type {Reel} from '../types';
import {SCENES} from '../types';
import {v, mono, serifZh} from '../theme';
import {EASE, clamp, fade, Kicker} from '../ui';

export const Hook: React.FC<{reel: Reel}> = ({reel}) => {
  const f = useCurrentFrame();
  const op = fade(f, SCENES.hook);
  const ap = (d: number) => interpolate(f, [d, d + 12], [0, 1], clamp);
  const rise = (d: number) => interpolate(f, [d, d + 14], [44, 0], {...clamp, easing: EASE});

  return (
    <AbsoluteFill style={{opacity: op, alignItems: 'center', justifyContent: 'center', padding: '0 90px'}}>
      <Kicker f={f} />
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22, textAlign: 'center'}}>
        <div style={{fontFamily: mono, fontSize: 50, letterSpacing: '0.04em', color: v.dim, opacity: ap(6), translate: `0 ${rise(6)}px`}}>
          {reel.hookTop}
        </div>
        <div style={{fontFamily: mono, fontSize: 64, color: v.gold, opacity: ap(16), translate: `0 ${rise(16)}px`}}>↓</div>
        <div
          style={{
            fontFamily: serifZh,
            fontWeight: 700,
            fontSize: 124,
            lineHeight: 1.04,
            color: v.paper,
            opacity: ap(26),
            translate: `0 ${rise(26)}px`,
          }}
        >
          {reel.hookMain}
        </div>
      </div>
    </AbsoluteFill>
  );
};
