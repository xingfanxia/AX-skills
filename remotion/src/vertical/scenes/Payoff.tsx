import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import type {Reel} from '../types';
import {SCENES} from '../types';
import {v, mono, serifZh} from '../theme';
import {EASE, clamp, fade, Ticker} from '../ui';

export const Payoff: React.FC<{reel: Reel}> = ({reel}) => {
  const f = useCurrentFrame();
  const op = fade(f, SCENES.payoff);
  const hero = reel.stats.find((s) => s.emphasize) ?? reel.stats[0];
  const rest = reel.stats.filter((s) => s !== hero);

  const heroScale = interpolate(f, [4, 22], [0.7, 1], {...clamp, easing: EASE});
  const heroOp = interpolate(f, [4, 18], [0, 1], clamp);
  const rowOp = interpolate(f, [30, 42], [0, 1], clamp);
  const rowY = interpolate(f, [30, 44], [26, 0], {...clamp, easing: EASE});
  const punchOp = interpolate(f, [54, 70], [0, 1], clamp);
  const punchY = interpolate(f, [54, 72], [30, 0], {...clamp, easing: EASE});

  return (
    <AbsoluteFill style={{opacity: op, alignItems: 'center', justifyContent: 'center', padding: '0 80px'}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 56, textAlign: 'center'}}>
        {/* hero stat */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, opacity: heroOp, scale: String(heroScale)}}>
          <div style={{fontFamily: mono, fontSize: 200, fontWeight: 600, color: v.gold, lineHeight: 1, fontVariantNumeric: 'tabular-nums'}}>
            {hero.value}
          </div>
          <div style={{fontFamily: mono, fontSize: 40, letterSpacing: '0.1em', color: v.dim}}>{hero.label}</div>
        </div>

        {/* secondary stats — stacked columns, no wrap */}
        <div style={{display: 'flex', alignItems: 'flex-start', gap: 70, opacity: rowOp, translate: `0 ${rowY}px`, fontFamily: mono}}>
          {rest.map((s, i) => (
            <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8}}>
              <span style={{fontSize: 92, fontWeight: 600, color: v.paper, lineHeight: 1, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}>
                {s.count != null ? <Ticker to={s.count} f={f} start={30} dur={26} /> : s.value}
              </span>
              <span style={{fontSize: 34, color: v.dim, whiteSpace: 'nowrap'}}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* punch line */}
        <div style={{maxWidth: 880, fontFamily: serifZh, fontWeight: 500, fontSize: 62, lineHeight: 1.3, color: v.paper, opacity: punchOp, translate: `0 ${punchY}px`}}>
          {reel.punch}
        </div>
      </div>
    </AbsoluteFill>
  );
};
