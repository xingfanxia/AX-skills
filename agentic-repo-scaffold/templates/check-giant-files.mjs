#!/usr/bin/env node
// Giant-file gate. Dependency-free (no fast-glob). Adapt LIMITS/EXTENSIONS/IGNORE to the repo.
// Run: node tools/verify/check-giant-files.mjs   (exit 1 on violation)
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.java', '.kt', '.rs', '.rb', '.php', '.cs', '.sql']);
const IGNORE = ['/node_modules/', '/.git/', '/generated/', '/vendor/', '/dist/', '/build/', '/.next/', '/__snapshots__/'];

// First matching rule wins; order specific → general.
const LIMITS = [
  { test: (f) => /\/app\/.*\/page\.tsx$/.test(f), max: 80, name: 'route page' },
  { test: (f) => /\/app\/.*\/(layout|route)\.[tj]sx?$/.test(f), max: 100, name: 'route layout/handler' },
  { test: (f) => /\/(transport|controllers|handlers)\//.test(f), max: 100, name: 'transport' },
  { test: (f) => /\/(public|index)\.[tj]sx?$/.test(f), max: 100, name: 'public entry' },
  { test: (f) => /\/(core|domain)\//.test(f), max: 250, name: 'core/domain' },
  { test: (f) => /\/application\//.test(f), max: 250, name: 'application' },
  { test: (f) => /\/adapters\//.test(f), max: 250, name: 'adapter' },
  { test: (f) => /\/migrations\/.*\.sql$/.test(f), max: 300, name: 'migration' },
  { test: (f) => f.endsWith('.tsx'), max: 200, name: 'component' },
  { test: (f) => /\.(test|spec)\.[tj]sx?$/.test(f), max: 400, name: 'test' },
  { test: () => true, max: 300, name: 'default' },
];
const HARD_CAP = 500;

// owner, reason, expiry per entry — review on expiry.
const ALLOWLIST = new Set([
  // 'src/legacy/bigfile.ts', // @owner reason expiry=2026-12-31
]);

let failed = false;
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const abs = path.join(dir, entry.name);
    const rel = '/' + path.relative(ROOT, abs).split(path.sep).join('/');
    if (IGNORE.some((p) => (rel + '/').includes(p))) continue;
    if (entry.isDirectory()) { walk(abs); continue; }
    if (!EXTENSIONS.has(path.extname(entry.name))) continue;
    const relNoLead = rel.slice(1);
    if (ALLOWLIST.has(relNoLead)) continue;
    const loc = fs.readFileSync(abs, 'utf8').split('\n').length;
    const rule = LIMITS.find((r) => r.test(rel));
    if (loc > HARD_CAP || loc > rule.max) {
      failed = true;
      console.error(`${relNoLead}: ${loc} LOC > ${Math.min(rule.max, HARD_CAP)} (${rule.name}). Split it or add an expiring allowlist entry.`);
    }
  }
}
walk(ROOT);
if (failed) process.exit(1);
console.log('check-giant-files: ok');
