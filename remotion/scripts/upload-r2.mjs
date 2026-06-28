#!/usr/bin/env node
/**
 * Upload rendered promos to the ax-blog R2 bucket under the ax-skills/ prefix.
 * Served at https://media.ax0x.ai/ax-skills/<id>.mp4 (same bucket + custom
 * domain as the blog's media; the ax-skills/ root keeps promos namespaced).
 * Auth: wrangler (already logged in for ax-blog). Run from remotion/ dir.
 *   node scripts/upload-r2.mjs [id ...]
 */
import {execFileSync} from 'child_process';
import {existsSync} from 'fs';
import {fileURLToPath} from 'url';
import {dirname, join} from 'path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BUCKET = 'ax-blog-media';
const PREFIX = 'ax-skills';

const ALL = [
  'banxian',
  'jewelry',
  'game',
  'proxy-node-setup',
  'dr-sharp',
  'trident',
  'serenity-bottleneck-research',
  'web-novel-writing',
];

const ids = process.argv.slice(2).length ? process.argv.slice(2) : ALL;

for (const id of ids) {
  const file = join(ROOT, 'out', `${id}.mp4`);
  if (!existsSync(file)) {
    console.error(`! missing render: ${file} — run render-all.mjs first`);
    process.exit(1);
  }
  const key = `${BUCKET}/${PREFIX}/${id}.mp4`;
  console.log(`\n=== uploading ${id}.mp4 → ${key} ===`);
  execFileSync(
    'wrangler',
    [
      'r2',
      'object',
      'put',
      key,
      '--file',
      file,
      '--content-type',
      'video/mp4',
      '--remote',
    ],
    {cwd: ROOT, stdio: 'inherit'},
  );
  console.log(`  https://media.ax0x.ai/${PREFIX}/${id}.mp4`);
}
console.log(`\n✓ uploaded ${ids.length} promo(s) to R2`);
