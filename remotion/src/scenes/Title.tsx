import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {Skill} from '../skills';
import {dune} from '../theme';
import {serifEn, serifZh, mono} from '../fonts';
import {Reveal, DrawLine} from '../components/Reveal';

export const Title: React.FC<{skill: Skill}> = ({skill}) => {
  return (
    <>
      {/* oversized faint index — deliberate right-edge bleed, watermark style */}
      <AbsoluteFill
        style={{
          alignItems: 'flex-end',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        <Reveal at={4} dur={40} dy={0}>
          <div
            style={{
              fontFamily: serifEn,
              fontStyle: 'italic',
              fontWeight: 500,
              fontSize: 460,
              lineHeight: 0.8,
              color: dune.ink,
              opacity: 0.06,
              translate: '14% 0px',
            }}
          >
            {skill.num}
          </div>
        </Reveal>
      </AbsoluteFill>

      <div style={{display: 'flex', flexDirection: 'column', gap: 0}}>
        <Reveal at={6}>
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
            }}
          >
            <span
              style={{width: 40, height: 1, background: dune.ink3}}
              aria-hidden
            />
            {skill.role}
          </div>
        </Reveal>

        <Reveal at={16} style={{marginTop: 30}}>
          <div
            style={{
              fontFamily: serifZh,
              fontWeight: 900,
              fontSize: 200,
              lineHeight: 1.0,
              letterSpacing: '-0.01em',
              color: dune.ink,
            }}
          >
            {skill.name}
          </div>
        </Reveal>

        <Reveal at={30} style={{marginTop: 14}}>
          <div
            style={{
              fontFamily: mono,
              fontSize: 30,
              fontWeight: 500,
              letterSpacing: '0.04em',
              color: dune.ink3,
            }}
          >
            {skill.id}
          </div>
        </Reveal>

        <DrawLine
          at={40}
          color={dune.line}
          style={{marginTop: 40, width: '56%', maxWidth: 900}}
        />

        <Reveal at={54} style={{marginTop: 34}}>
          <div
            style={{
              fontFamily: serifZh,
              fontWeight: 500,
              fontSize: 66,
              lineHeight: 1.4,
              color: dune.ink2,
              maxWidth: 1300,
            }}
          >
            {skill.tagline}
          </div>
        </Reveal>
      </div>
    </>
  );
};
