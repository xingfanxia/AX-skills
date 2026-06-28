import React from 'react';
import {interpolate, useCurrentFrame, Easing} from 'remotion';
import {EASE} from '../theme';

/**
 * Fade + slide-up reveal, the single entrance motion used across the decks.
 * `at` is the local frame to start (relative to the enclosing Sequence),
 * `dur` the reveal length in frames, `dy` the travel distance.
 */
export const Reveal: React.FC<{
  at?: number;
  dur?: number;
  dy?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({at = 0, dur = 22, dy = 26, children, style}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [at, at + dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(...EASE),
  });
  const translateY = interpolate(frame, [at, at + dur], [dy, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(...EASE),
  });
  return (
    <div style={{opacity, translate: `0px ${translateY}px`, ...style}}>
      {children}
    </div>
  );
};

/** A horizontal hairline that draws itself left→right. */
export const DrawLine: React.FC<{
  at?: number;
  dur?: number;
  color: string;
  height?: number;
  style?: React.CSSProperties;
}> = ({at = 0, dur = 26, color, height = 1, style}) => {
  const frame = useCurrentFrame();
  const scaleX = interpolate(frame, [at, at + dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(...EASE),
  });
  return (
    <div
      style={{
        height,
        background: color,
        transformOrigin: 'left center',
        scale: `${scaleX} 1`,
        ...style,
      }}
    />
  );
};
