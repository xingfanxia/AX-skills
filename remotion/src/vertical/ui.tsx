import React from 'react';
import {AbsoluteFill, interpolate, Easing, useCurrentFrame} from 'remotion';
import {v, mono} from './theme';

export const EASE = Easing.bezier(0.16, 1, 0.3, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const BRAILLE = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

/** Per-scene fade: quick in, quick out — snappy cuts, never a hard pop. */
export const fade = (f: number, dur: number, inF = 8, outF = 9) =>
  interpolate(f, [0, inF, dur - outF, dur], [0, 1, 1, 0], clamp);

/** Continuous Dune background — drifting dot-grid + dual warm glow + vignette. */
export const Bg: React.FC = () => {
  const f = useCurrentFrame();
  const drift = interpolate(f, [0, 410], [0, 30], clamp);
  return (
    <AbsoluteFill style={{backgroundColor: v.bg}}>
      <AbsoluteFill
        style={{
          backgroundImage: 'radial-gradient(#f0e6d2 1.3px, transparent 1.6px)',
          backgroundSize: '38px 38px',
          backgroundPosition: `0px ${drift}px`,
          opacity: 0.05,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(42% 30% at 26% 22%, rgba(217,164,65,0.16) 0%, rgba(23,19,12,0) 60%), radial-gradient(46% 34% at 78% 82%, rgba(155,171,111,0.12) 0%, rgba(23,19,12,0) 64%)',
        }}
      />
      <AbsoluteFill
        style={{boxShadow: 'inset 0 0 320px 80px rgba(10,8,4,0.7)'}}
      />
    </AbsoluteFill>
  );
};

/** Top kicker — the brand stamp. */
export const Kicker: React.FC<{f: number}> = ({f}) => {
  const o = interpolate(f, [0, 12], [0, 0.7], clamp);
  return (
    <div
      style={{
        position: 'absolute',
        top: 120,
        left: 0,
        right: 0,
        textAlign: 'center',
        fontFamily: mono,
        fontSize: 30,
        letterSpacing: '0.42em',
        textTransform: 'uppercase',
        color: v.dim,
        opacity: o,
      }}
    >
      AX · Agent Skills
    </div>
  );
};

/** Corner ticks — magazine chrome. */
export const BrandCorners: React.FC = () => {
  const c: React.CSSProperties = {position: 'absolute', width: 46, height: 46, borderColor: v.line, borderStyle: 'solid'};
  return (
    <>
      <div style={{...c, top: 64, left: 64, borderWidth: '2px 0 0 2px'}} />
      <div style={{...c, top: 64, right: 64, borderWidth: '2px 2px 0 0'}} />
      <div style={{...c, bottom: 64, left: 64, borderWidth: '0 0 2px 2px'}} />
      <div style={{...c, bottom: 64, right: 64, borderWidth: '0 2px 2px 0'}} />
    </>
  );
};

/** Terminal title bar with traffic lights. */
export const Bar: React.FC<{title: string}> = ({title}) => {
  const dot = (c: string) => (
    <span style={{width: 16, height: 16, borderRadius: '50%', background: c, display: 'inline-block'}} />
  );
  return (
    <div
      style={{
        height: 64,
        background: '#1c160e',
        borderBottom: `1px solid ${v.line}`,
        display: 'flex',
        alignItems: 'center',
        padding: '0 26px',
        gap: 12,
      }}
    >
      {dot('#c96a52')}
      {dot('#d6a64a')}
      {dot('#8a9a6b')}
      <div style={{flex: 1, textAlign: 'center', fontFamily: mono, fontSize: 24, color: v.dim, letterSpacing: '0.05em'}}>
        {title}
      </div>
      <div style={{width: 60}} />
    </div>
  );
};

export const Cursor: React.FC<{f: number}> = ({f}) => (
  <span
    style={{
      display: 'inline-block',
      width: '0.55em',
      height: '1.05em',
      marginLeft: 4,
      transform: 'translateY(0.16em)',
      background: v.gold,
      opacity: Math.floor(f / 15) % 2 === 0 ? 0.95 : 0,
    }}
  />
);

/** Count-up number. */
export const Ticker: React.FC<{to: number; f: number; start: number; dur: number; style?: React.CSSProperties}> = ({
  to,
  f,
  start,
  dur,
  style,
}) => {
  const val = Math.round(interpolate(f, [start, start + dur], [0, to], {...clamp, easing: EASE}));
  return <span style={style}>{val}</span>;
};
