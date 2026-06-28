import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate, Easing} from 'remotion';
import type {Session} from './types';
import {layout} from './types';
import {term, FONT, FS, LH} from './theme';
import {EventLine, Cursor} from './EventLine';

const WIN_W = 1560;
const WIN_H = 884;
const BAR_H = 58;
const PAD = 34;
const BODY_H = WIN_H - BAR_H - PAD * 2;
const VIEWPORT_LINES = Math.floor(BODY_H / LH); // ~16

export const TAIL = 52; // hold frames after the last event

export const promoDuration = (s: Session) => layout(s.events).total + TAIL;

const Dot: React.FC<{c: string}> = ({c}) => (
  <span style={{width: 14, height: 14, borderRadius: '50%', background: c, display: 'inline-block'}} />
);

export const TerminalPromo: React.FC<{session: Session}> = ({session}) => {
  const frame = useCurrentFrame();
  const {timed, total} = layout(session.events);

  // intro: terminal window fades + lifts in
  const intro = interpolate(frame, [0, 16], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const started = timed.filter((t) => t.start <= frame);
  const activeIdx = started.length - 1;
  const allDone = frame >= total;

  // how many lines have appeared (fractional → smooth autoscroll)
  let appeared = 0;
  if (activeIdx >= 0) {
    const a = timed[activeIdx];
    let inActive = 1;
    if (a.e.k === 'out') inActive = Math.min(a.e.lines.length, (frame - a.start) / 9);
    appeared = a.lineStart + inActive;
  }
  if (allDone) appeared += 1; // trailing idle prompt
  const scroll = Math.max(0, appeared - VIEWPORT_LINES + 0.4) * LH;

  return (
    <AbsoluteFill style={{backgroundColor: term.paperBg}}>
      {/* paper-frame texture so the clip still reads as part of the showcase */}
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(#1f1a14 1.2px, transparent 1.5px)`,
          backgroundSize: '30px 30px',
          opacity: 0.05,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(45% 50% at 28% 26%, #e6dabf 0%, rgba(239,229,209,0) 60%), radial-gradient(48% 52% at 78% 80%, #ddcfae 0%, rgba(239,229,209,0) 62%)',
          opacity: 0.8,
        }}
      />

      {/* brand chrome on the paper */}
      <div style={{position: 'absolute', top: 46, left: 56, fontFamily: FONT, fontSize: 21, letterSpacing: '0.22em', textTransform: 'uppercase', color: '#8a7c66'}}>
        AX · Agent Skills
      </div>
      <div style={{position: 'absolute', top: 46, right: 56, fontFamily: FONT, fontSize: 21, letterSpacing: '0.22em', textTransform: 'uppercase', color: '#8a7c66'}}>
        在 Claude Code 里
      </div>

      {/* terminal window */}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div
          style={{
            width: WIN_W,
            height: WIN_H,
            background: term.win,
            border: `1px solid ${term.border}`,
            borderRadius: 12,
            boxShadow: '0 40px 110px rgba(31,26,20,0.45)',
            overflow: 'hidden',
            opacity: intro,
            translate: `0px ${interpolate(intro, [0, 1], [28, 0])}px`,
          }}
        >
          {/* title bar */}
          <div
            style={{
              height: BAR_H,
              background: term.bar,
              borderBottom: `1px solid ${term.border}`,
              display: 'flex',
              alignItems: 'center',
              padding: '0 20px',
              gap: 10,
            }}
          >
            <Dot c="#c96a52" />
            <Dot c="#d6a64a" />
            <Dot c="#8a9a6b" />
            <div style={{flex: 1, textAlign: 'center', fontFamily: FONT, fontSize: 19, color: term.dim, letterSpacing: '0.04em'}}>
              claude — {session.title}
            </div>
            <div style={{width: 56}} />
          </div>

          {/* body (clipped, scrolling) */}
          <div style={{height: BODY_H, padding: `${PAD}px ${PAD + 8}px`, overflow: 'hidden', position: 'relative'}}>
            <div style={{translate: `0px ${-scroll}px`}}>
              {started.map((t, i) => (
                <EventLine
                  key={i}
                  event={t.e}
                  f={frame - t.start}
                  globalFrame={frame}
                  active={i === activeIdx}
                />
              ))}
              {allDone && (
                <div style={{fontFamily: FONT, fontSize: FS, lineHeight: `${LH}px`, color: term.text, marginTop: 6}}>
                  <span style={{color: term.accent}}>❯ </span>
                  <Cursor frame={frame} />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* caption under the window */}
        <div style={{marginTop: 24, fontFamily: FONT, fontSize: 22, letterSpacing: '0.06em', color: '#5a4f3f', opacity: intro}}>
          {session.caption}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
