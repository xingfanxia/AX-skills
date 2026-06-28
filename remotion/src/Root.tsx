import React from 'react';
import {Composition} from 'remotion';
import {SESSIONS} from './terminal/sessions';
import {TerminalPromo, promoDuration} from './terminal/TerminalPromo';
import {FPS} from './terminal/types';

/**
 * One composition per deck'd skill — id === showcase slug === R2 filename.
 * Each promo is a scripted terminal session showing the skill in use.
 * Duration is derived from the session's events.
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
    </>
  );
};
