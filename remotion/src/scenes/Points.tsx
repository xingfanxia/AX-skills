import React from 'react';
import type {Skill} from '../skills';
import {dune} from '../theme';
import {serifEn, serifZh, mono} from '../fonts';
import {Reveal, DrawLine} from '../components/Reveal';

const PointRow: React.FC<{
  index: number;
  text: string;
  at: number;
  isLast: boolean;
}> = ({index, text, at, isLast}) => (
  <div>
    <Reveal at={at}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 34}}>
        <span
          style={{
            fontFamily: serifEn,
            fontStyle: 'italic',
            fontWeight: 500,
            fontSize: 64,
            color: dune.ink,
            opacity: 0.32,
            minWidth: 90,
          }}
        >
          {String(index).padStart(2, '0')}
        </span>
        <span
          style={{
            fontFamily: serifZh,
            fontWeight: 500,
            fontSize: 58,
            lineHeight: 1.25,
            color: dune.ink,
          }}
        >
          {text}
        </span>
      </div>
    </Reveal>
    {!isLast && (
      <DrawLine
        at={at + 6}
        color={dune.line}
        style={{marginTop: 28, marginBottom: 28, width: '100%'}}
      />
    )}
  </div>
);

export const Points: React.FC<{skill: Skill}> = ({skill}) => {
  return (
    <div style={{display: 'flex', flexDirection: 'column'}}>
      <Reveal at={4}>
        <div
          style={{
            fontFamily: mono,
            fontSize: 26,
            fontWeight: 500,
            letterSpacing: '0.3em',
            textTransform: 'uppercase',
            color: dune.ink3,
            display: 'flex',
            alignItems: 'center',
            gap: '0.8em',
            marginBottom: 48,
          }}
        >
          <span style={{width: 40, height: 1, background: dune.ink3}} aria-hidden />
          能做什么 · Capabilities
        </div>
      </Reveal>

      {skill.points.map((p, i) => (
        <PointRow
          key={i}
          index={i + 1}
          text={p}
          at={18 + i * 52}
          isLast={i === skill.points.length - 1}
        />
      ))}
    </div>
  );
};
