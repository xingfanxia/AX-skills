import React from 'react';
import type {Skill} from '../skills';
import {dune} from '../theme';
import {serifZh, mono} from '../fonts';
import {Reveal, DrawLine} from '../components/Reveal';

export const Outro: React.FC<{skill: Skill}> = ({skill}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        gap: 0,
      }}
    >
      <Reveal at={6}>
        <div
          style={{
            fontFamily: serifZh,
            fontWeight: 700,
            fontSize: 96,
            lineHeight: 1.05,
            color: dune.ink,
          }}
        >
          {skill.name}
        </div>
      </Reveal>

      <Reveal at={16} style={{marginTop: 22}}>
        <div
          style={{
            fontFamily: mono,
            fontSize: 28,
            letterSpacing: '0.06em',
            color: dune.ink3,
            display: 'flex',
            alignItems: 'center',
            gap: '0.7em',
          }}
        >
          <span
            style={{width: 9, height: 9, background: dune.ink, opacity: 0.55}}
            aria-hidden
          />
          {skill.source}
        </div>
      </Reveal>

      <DrawLine
        at={26}
        color={dune.line}
        style={{marginTop: 44, marginBottom: 44, width: 360}}
      />

      <Reveal at={36}>
        <div
          style={{
            fontFamily: serifZh,
            fontWeight: 600,
            fontSize: 84,
            color: dune.ink,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4em',
          }}
        >
          查看完整 deck
          <span style={{fontFamily: 'Georgia, serif'}}>→</span>
        </div>
      </Reveal>

      <Reveal at={48} style={{marginTop: 26}}>
        <div
          style={{
            fontFamily: mono,
            fontSize: 32,
            letterSpacing: '0.04em',
            color: dune.ink2,
          }}
        >
          xingfanxia.github.io/AX-skills
        </div>
      </Reveal>
    </div>
  );
};
