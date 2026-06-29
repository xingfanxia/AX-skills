import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import type {Reel} from './types';
import {SCENES, REEL_TOTAL} from './types';
import {Bg} from './ui';
import {Hook} from './scenes/Hook';
import {Command} from './scenes/Command';
import {Work} from './scenes/Work';
import {Payoff} from './scenes/Payoff';
import {EndCard} from './scenes/EndCard';

export const reelDuration = (_reel?: Reel) => REEL_TOTAL;

/** 9:16 short-video skill reel: hook → command → work → payoff → end. */
export const VerticalPromo: React.FC<{reel: Reel}> = ({reel}) => {
  let at = 0;
  const seq = (dur: number) => {
    const from = at;
    at += dur;
    return {from, durationInFrames: dur, layout: 'none' as const};
  };
  return (
    <AbsoluteFill>
      <Bg />
      <Sequence {...seq(SCENES.hook)}>
        <Hook reel={reel} />
      </Sequence>
      <Sequence {...seq(SCENES.command)}>
        <Command reel={reel} />
      </Sequence>
      <Sequence {...seq(SCENES.work)}>
        <Work reel={reel} />
      </Sequence>
      <Sequence {...seq(SCENES.payoff)}>
        <Payoff reel={reel} />
      </Sequence>
      <Sequence {...seq(SCENES.end)}>
        <EndCard reel={reel} />
      </Sequence>
    </AbsoluteFill>
  );
};
