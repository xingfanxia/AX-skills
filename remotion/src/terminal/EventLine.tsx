import React from 'react';
import {interpolate, Easing} from 'remotion';
import type {TermEvent} from './types';
import {term, FONT, FS, LH} from './theme';

const BRAILLE = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

export const Cursor: React.FC<{frame: number; on?: boolean}> = ({frame, on = true}) => (
  <span
    style={{
      display: 'inline-block',
      width: '0.6em',
      height: '1.05em',
      marginLeft: 2,
      transform: 'translateY(0.16em)',
      background: term.accent,
      opacity: on && Math.floor(frame / 16) % 2 === 0 ? 0.95 : 0,
    }}
  />
);

const row: React.CSSProperties = {
  fontFamily: FONT,
  fontSize: FS,
  lineHeight: `${LH}px`,
  color: term.text,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
};

/**
 * Renders one session event at local frame `f` (frames since the event started).
 * `globalFrame` drives the blinking cursor. `active` = this is the latest event.
 */
export const EventLine: React.FC<{
  event: TermEvent;
  f: number;
  globalFrame: number;
  active: boolean;
}> = ({event, f, globalFrame, active}) => {
  const appear = interpolate(f, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

  if (event.k === 'in') {
    const n = Math.min(event.text.length, Math.floor(f / 1.7));
    const typing = n < event.text.length;
    return (
      <div style={{...row, marginTop: 6}}>
        <span style={{color: term.accent}}>❯ </span>
        <span>{event.text.slice(0, n)}</span>
        <Cursor frame={globalFrame} on={active && (typing || true)} />
      </div>
    );
  }

  if (event.k === 'sys') {
    return (
      <div style={{...row, color: term.dim, opacity: appear}}>{event.text}</div>
    );
  }

  if (event.k === 'run') {
    const spinFrames = Math.round((event.sec ?? 1) * 30);
    const running = f < spinFrames;
    return (
      <div style={{...row, opacity: appear}}>
        {running ? (
          <span style={{color: term.accent}}>
            {BRAILLE[Math.floor(globalFrame / 3) % BRAILLE.length]}
          </span>
        ) : (
          <span style={{color: term.ok}}>✓</span>
        )}
        <span style={{color: running ? term.dim : term.text}}> {event.text}</span>
        {running ? <span style={{color: term.dim}}>…</span> : null}
      </div>
    );
  }

  if (event.k === 'out') {
    return (
      <div>
        {event.lines.map((ln, i) => {
          const lf = f - i * 9;
          if (lf < 0) return <div key={i} style={{...row, height: LH}} />;
          const o = interpolate(lf, [0, 7], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={i}
              style={{
                ...row,
                opacity: o,
                color: event.accent ? term.text : term.text,
              }}
            >
              {ln === '' ? ' ' : ln}
            </div>
          );
        })}
      </div>
    );
  }

  // done — highlighted result banner
  const s = interpolate(f, [0, 14], [0.96, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return (
    <div
      style={{
        ...row,
        marginTop: 10,
        padding: '8px 16px',
        borderLeft: `3px solid ${term.accent}`,
        background: 'rgba(217,164,65,0.09)',
        opacity: appear,
        scale: `${s}`,
        transformOrigin: 'left center',
        fontWeight: 500,
      }}
    >
      <span style={{color: term.accent}}>◆ </span>
      {event.text}
    </div>
  );
};
