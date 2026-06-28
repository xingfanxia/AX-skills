/**
 * Font stacks for the Dune decks, loaded via @remotion/google-fonts so the
 * renderer blocks until glyphs are ready (no FOUT in the mp4). Mirrors the
 * deck <head> font set: Playfair Display + Source Serif 4 (latin display),
 * Noto Serif SC / Noto Sans SC (Chinese), IBM Plex Mono (kicker/meta).
 */
import {loadFont as loadPlayfair} from '@remotion/google-fonts/PlayfairDisplay';
import {loadFont as loadSourceSerif} from '@remotion/google-fonts/SourceSerif4';
import {loadFont as loadNotoSerifSC} from '@remotion/google-fonts/NotoSerifSC';
import {loadFont as loadNotoSansSC} from '@remotion/google-fonts/NotoSansSC';
import {loadFont as loadPlexMono} from '@remotion/google-fonts/IBMPlexMono';

const playfair = loadPlayfair('normal', {
  weights: ['500', '600', '700'],
  subsets: ['latin'],
});
const sourceSerif = loadSourceSerif('normal', {
  weights: ['400', '500'],
  subsets: ['latin'],
});
const notoSerifSC = loadNotoSerifSC('normal', {
  weights: ['400', '500', '700', '900'],
  subsets: ['chinese-simplified', 'latin'],
});
const notoSansSC = loadNotoSansSC('normal', {
  weights: ['300', '400', '500'],
  subsets: ['chinese-simplified', 'latin'],
});
const plexMono = loadPlexMono('normal', {
  weights: ['400', '500'],
  subsets: ['latin'],
});

// Display = Playfair for latin numerals/italics, Source Serif fallback.
export const serifEn = `${playfair.fontFamily}, ${sourceSerif.fontFamily}, Georgia, serif`;
// Chinese headings + leads.
export const serifZh = `${notoSerifSC.fontFamily}, ${serifEn}`;
// Body.
export const sansZh = `${notoSansSC.fontFamily}, "PingFang SC", sans-serif`;
// Kicker / meta / ids.
export const mono = `${plexMono.fontFamily}, ui-monospace, monospace`;
