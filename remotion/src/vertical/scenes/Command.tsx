import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import type {Reel} from '../types';
import {SCENES} from '../types';
import {v, mono} from '../theme';
import {EASE, clamp, fade, Bar, Cursor} from '../ui';

export const Command: React.FC<{reel: Reel}> = ({reel}) => {
  const f = useCurrentFrame();
  const op = fade(f, SCENES.command);
  const cardOp = interpolate(f, [0, 12], [0, 1], clamp);
  const cardY = interpolate(f, [0, 16], [70, 0], {...clamp, easing: EASE});

  const typeStart = 16;
  const n = Math.max(0, Math.min(reel.command.length, Math.floor((f - typeStart) / 1.5)));
  const typed = reel.command.slice(0, n);
  const fired = f > typeStart + reel.command.length * 1.5 + 8;

  return (
    <AbsoluteFill style={{opacity: op, alignItems: 'center', justifyContent: 'center', padding: '0 70px'}}>
      <div
        style={{
          width: 940,
          background: v.card,
          border: `1px solid ${v.line}`,
          borderRadius: 20,
          overflow: 'hidden',
          opacity: cardOp,
          translate: `0 ${cardY}px`,
          boxShadow: '0 50px 130px rgba(0,0,0,0.55)',
        }}
      >
        <Bar title="claude — jewelry-marketing" />
        <div style={{padding: '46px 46px 52px', fontFamily: mono, fontSize: 46, lineHeight: 1.5, color: v.paper}}>
          <div>
            <span style={{color: v.gold}}>❯ </span>
            {typed}
            <Cursor f={f} />
          </div>
          {fired && (
            <div style={{marginTop: 30, color: v.sage, fontSize: 40, opacity: interpolate(f - (typeStart + reel.command.length * 1.5 + 8), [0, 8], [0, 1], clamp)}}>
              ▸ 运行中…
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
