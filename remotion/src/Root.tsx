import React from 'react';
import {Composition} from 'remotion';
import {SKILLS} from './skills';
import {SkillPromo, PROMO_DURATION} from './SkillPromo';
import {FPS} from './theme';

/**
 * One composition per deck'd skill — id === showcase slug, so
 * `remotion render <slug>` maps 1:1 to docs/<slug>/ and the R2 key
 * ax-skills/<slug>.mp4.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {SKILLS.map((skill) => (
        <Composition
          key={skill.id}
          id={skill.id}
          component={SkillPromo}
          durationInFrames={PROMO_DURATION}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{skill}}
        />
      ))}
    </>
  );
};
