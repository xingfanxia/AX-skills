import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, Easing} from 'remotion';
import {EASE} from '../theme';

/**
 * Full-frame scene container that fades itself in at the start and out at the
 * end of its Sequence. Children use <Reveal> for per-element staggering on the
 * same (Sequence-local) timeline.
 */
export const Scene: React.FC<{
  durationInFrames: number;
  fadeIn?: number;
  fadeOut?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({durationInFrames, fadeIn = 16, fadeOut = 18, children, style}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, fadeIn, durationInFrames - fadeOut, durationInFrames],
    [0, 1, 1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(...EASE),
    },
  );
  return (
    <AbsoluteFill
      style={{
        opacity,
        padding: '7.5% 9%',
        justifyContent: 'center',
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
