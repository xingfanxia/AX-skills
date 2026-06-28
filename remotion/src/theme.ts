/**
 * Dune / 沙丘 Style A tokens — kept in lockstep with the AX-skills decks
 * (docs/index.html :root). The promo videos must read as siblings of the
 * static decks, so colours and type scale are copied verbatim, not reinvented.
 */
export const dune = {
  paper: '#f0e6d2',
  paperTint: '#e6dabf',
  paperDeep: '#ddcfae',
  ink: '#1f1a14',
  ink2: '#5a4f3f',
  ink3: '#8a7c66',
  line: '#cdbf9f',
} as const;

// Easing curve used across the decks' reveals (out-expo-ish). Matches the
// `Easing.bezier(0.16, 1, 0.3, 1)` recommended by the remotion skill.
export const EASE = [0.16, 1, 0.3, 1] as const;

export const FPS = 30;
