#!/usr/bin/env node
/**
 * Render every skill promo to out/<id>.mp4.
 * Composition ids: horizontal `<slug>` (terminal) + vertical `<slug>-v` (reel) —
 * see src/Root.tsx (src/terminal/sessions.ts + src/vertical/reels.ts).
 * Run from the remotion/ dir:  node scripts/render-all.mjs [id ...]
 * With no args, renders all. Pass ids to render a subset.
 */
import {execFileSync} from 'child_process';
import {mkdirSync} from 'fs';
import {fileURLToPath} from 'url';
import {dirname, join} from 'path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

// Keep in sync with src/Root.tsx (SESSIONS[].id + REELS[].id).
const HORIZONTAL = [
  'banxian',
  'jewelry',
  'game',
  'proxy-node-setup',
  'dr-sharp',
  'trident',
  'serenity-bottleneck-research',
  'web-novel-writing',
];
const VERTICAL = ['jewelry-v'];
const ALL = [...HORIZONTAL, ...VERTICAL];

const ids = process.argv.slice(2).length ? process.argv.slice(2) : ALL;
mkdirSync(join(ROOT, 'out'), {recursive: true});

for (const id of ids) {
  if (!ALL.includes(id)) {
    console.error(`! unknown composition id: ${id}`);
    process.exit(1);
  }
  console.log(`\n=== rendering ${id} ===`);
  execFileSync(
    'npx',
    ['remotion', 'render', 'src/index.ts', id, `out/${id}.mp4`, '--log=error'],
    {cwd: ROOT, stdio: 'inherit'},
  );
}
console.log(`\n✓ rendered ${ids.length} promo(s) → out/`);
