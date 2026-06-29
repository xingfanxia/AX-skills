import React from 'react';
import {Composition} from 'remotion';
import {SESSIONS} from './terminal/sessions';
import {TerminalPromo, promoDuration} from './terminal/TerminalPromo';
import {FPS} from './terminal/types';
import {REELS} from './vertical/reels';
import {VerticalPromo, reelDuration} from './vertical/VerticalPromo';

/**
 * Compositions — id === showcase slug === R2 filename throughout.
 * - Horizontal `<slug>` (1920×1080): scripted terminal session per deck'd skill.
 * - Vertical `<slug>-v` (1080×1920): short-video "skill reel" for social platforms.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {SESSIONS.map((session) => (
        <Composition
          key={session.id}
          id={session.id}
          component={TerminalPromo}
          durationInFrames={promoDuration(session)}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{session}}
        />
      ))}
      {REELS.map((reel) => (
        <Composition
          key={reel.id}
          id={reel.id}
          component={VerticalPromo}
          durationInFrames={reelDuration(reel)}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{reel}}
        />
      ))}
    </>
  );
};
