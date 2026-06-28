import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {dune} from '../theme';
import {mono} from '../fonts';

/**
 * Persistent Dune backdrop + magazine chrome, shared by every scene.
 * Approximates the decks' WebGL dual-bg with two slow-drifting warm radial
 * glows over the paper base + the fixed dot-grid texture, plus the corner
 * chrome / running foot that ties the video to its deck.
 */
export const Background: React.FC<{idLabel: string; foot: string}> = ({
  idLabel,
  foot,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames, width} = useVideoConfig();
  const t = frame / durationInFrames; // 0..1 across the whole clip

  const gx = interpolate(t, [0, 1], [22, 38]);
  const gy = interpolate(t, [0, 1], [28, 18]);
  const gx2 = interpolate(t, [0, 1], [82, 66]);
  const gy2 = interpolate(t, [0, 1], [72, 84]);

  const pad = Math.round(width * 0.052);
  const chrome: React.CSSProperties = {
    position: 'absolute',
    fontFamily: mono,
    fontSize: Math.round(width * 0.0118),
    letterSpacing: '0.22em',
    textTransform: 'uppercase',
    color: dune.ink3,
  };

  return (
    <AbsoluteFill style={{backgroundColor: dune.paper}}>
      {/* drifting warm glows */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(40% 46% at ${gx}% ${gy}%, ${dune.paperTint} 0%, rgba(240,230,210,0) 60%), radial-gradient(46% 50% at ${gx2}% ${gy2}%, ${dune.paperDeep} 0%, rgba(240,230,210,0) 62%)`,
          opacity: 0.85,
        }}
      />
      {/* dot grid */}
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(${dune.ink} 1.3px, transparent 1.6px)`,
          backgroundSize: '30px 30px',
          opacity: 0.055,
        }}
      />
      {/* vignette */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(120% 120% at 50% 50%, rgba(31,26,20,0) 62%, rgba(31,26,20,0.10) 100%)',
        }}
      />

      {/* magazine chrome */}
      <div style={{...chrome, top: pad, left: pad}}>AX · Agent Skills</div>
      <div style={{...chrome, top: pad, right: pad}}>{idLabel}</div>
      <div style={{...chrome, bottom: pad, left: pad}}>{foot}</div>
      <div style={{...chrome, bottom: pad, right: pad}}>
        电子杂志 · 沙丘 / Dune
      </div>
    </AbsoluteFill>
  );
};
