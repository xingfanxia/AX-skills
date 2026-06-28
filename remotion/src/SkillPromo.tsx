import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import type {Skill} from './skills';
import {SKILLS} from './skills';
import {Background} from './components/Background';
import {Scene} from './components/Scene';
import {Title} from './scenes/Title';
import {Points} from './scenes/Points';
import {Outro} from './scenes/Outro';

export const PROMO_DURATION = 600; // 20s @ 30fps

const TITLE = {from: 0, dur: 185};
const POINTS = {from: 180, dur: 250};
const OUTRO = {from: 425, dur: 175};

export const SkillPromo: React.FC<{skill: Skill}> = ({skill}) => {
  const total = SKILLS.length;
  return (
    <AbsoluteFill>
      <Background
        idLabel={skill.id}
        foot={`${skill.num} / ${String(total).padStart(2, '0')} · AX Skills`}
      />

      <Sequence from={TITLE.from} durationInFrames={TITLE.dur}>
        <Scene durationInFrames={TITLE.dur}>
          <Title skill={skill} />
        </Scene>
      </Sequence>

      <Sequence from={POINTS.from} durationInFrames={POINTS.dur}>
        <Scene durationInFrames={POINTS.dur}>
          <Points skill={skill} />
        </Scene>
      </Sequence>

      <Sequence from={OUTRO.from} durationInFrames={OUTRO.dur}>
        <Scene durationInFrames={OUTRO.dur}>
          <Outro skill={skill} />
        </Scene>
      </Sequence>
    </AbsoluteFill>
  );
};
