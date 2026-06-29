import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import type {Reel} from '../types';
import {SCENES} from '../types';
import {v, mono} from '../theme';
import {EASE, clamp, fade, BRAILLE} from '../ui';

const GRID_START = 16;
const STEP = 7; // frames between cells

const Cell: React.FC<{label: string; i: number; f: number}> = ({label, i, f}) => {
  const d = GRID_START + i * STEP;
  const o = interpolate(f, [d, d + 8], [0, 1], clamp);
  const s = interpolate(f, [d, d + 12], [0.5, 1], {...clamp, easing: EASE});
  const flash = interpolate(f, [d, d + 6, d + 16], [0.9, 0.5, 0.28], clamp);
  return (
    <div
      style={{
        width: 188,
        height: 188,
        borderRadius: 16,
        border: `1px solid ${v.line}`,
        background: `linear-gradient(150deg, rgba(217,164,65,${flash}) 0%, rgba(155,171,111,0.14) 100%)`,
        opacity: o,
        scale: String(s),
        display: 'flex',
        alignItems: 'flex-end',
        padding: 14,
        boxSizing: 'border-box',
      }}
    >
      <span style={{fontFamily: mono, fontSize: 20, color: v.bg, fontWeight: 500, opacity: 0.82}}>{label}</span>
    </div>
  );
};

export const Work: React.FC<{reel: Reel}> = ({reel}) => {
  const f = useCurrentFrame();
  const op = fade(f, SCENES.work);
  const cells = reel.grid ?? [];
  const total = reel.gridTotal ?? cells.length;
  const filled = Math.max(0, Math.min(total, Math.floor((f - GRID_START) / STEP) + 1));
  const spinning = filled < total;

  return (
    <AbsoluteFill style={{opacity: op, alignItems: 'center', justifyContent: 'center', padding: '0 90px'}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 44}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 18, fontFamily: mono, fontSize: 42, color: v.dim}}>
          <span style={{color: spinning ? v.gold : v.sage, width: 36, display: 'inline-block'}}>
            {spinning ? BRAILLE[Math.floor(f / 3) % BRAILLE.length] : '✓'}
          </span>
          {reel.workCaption}
        </div>

        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 188px)', gap: 22}}>
          {cells.map((label, i) => (
            <Cell key={i} label={label} i={i} f={f} />
          ))}
        </div>

        <div style={{fontFamily: mono, display: 'flex', alignItems: 'baseline', gap: 10}}>
          <span style={{fontSize: 108, fontWeight: 600, color: v.gold, fontVariantNumeric: 'tabular-nums'}}>
            {String(filled).padStart(2, '0')}
          </span>
          <span style={{fontSize: 56, color: v.dim}}>/ {total} 张营销图</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
