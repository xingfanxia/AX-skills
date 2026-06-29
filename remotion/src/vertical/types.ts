/** Data model for a 9:16 short-video "skill reel" — one per skill. */
export const FPS = 30;

export type Stat = {value: string; label: string; emphasize?: boolean; count?: number};

export type Reel = {
  id: string; // composition id === R2 filename (e.g. 'jewelry-v')
  skill: string; // skill dir name, shown on the end card
  hookTop: string; // small line above the headline
  hookMain: string; // the big headline (the promise)
  command: string; // the invocation typed in the terminal card
  workCaption: string; // caption above the work visual
  grid?: string[]; // if set, Work shows a filling grid (e.g. 12 image labels)
  gridTotal?: number; // grid count for the counter (defaults to grid.length)
  steps?: string[]; // fallback Work visual when no grid
  stats: Stat[]; // payoff numbers
  punch: string; // one-line payoff statement
  caption: string; // end-card tagline
};

/** Per-scene durations (frames @ 30fps). */
export const SCENES = {hook: 70, command: 64, work: 116, payoff: 96, end: 64} as const;
export const REEL_TOTAL = Object.values(SCENES).reduce((a, b) => a + b, 0); // 410f ≈ 13.7s
