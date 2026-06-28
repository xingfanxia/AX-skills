import {mono, sansZh} from '../fonts';

/** Inverted-Dune terminal palette — dark window on the paper frame. */
export const term = {
  paperBg: '#efe5d1',     // outer frame (matches showcase)
  win: '#17130c',         // terminal body
  bar: '#241d14',         // title bar
  border: '#3a3122',
  text: '#f0e6d2',        // paper-on-ink
  dim: '#9a8c72',         // comments / secondary
  faint: '#6b6048',
  accent: '#d9a441',      // prompt ❯, run spinner, done marker (warm gold)
  ok: '#9bab6f',          // ✓ success (sage)
} as const;

export const FONT = `${mono}, ${sansZh}`;
export const FS = 31;        // terminal font size (readable at video distance)
export const LH = 47;        // line height (px)
