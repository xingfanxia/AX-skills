#!/usr/bin/env node
// Architecture boundary / purity gate. Dependency-free. Set RULES to the repo's real paths.
// Enforces: core/domain is pure; application depends on ports not adapters; transport stays thin;
// generated files are not hand-edited. Run: node tools/verify/check-boundaries.mjs (exit 1 on violation)
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx']);
const IGNORE = ['/node_modules/', '/.git/', '/generated/', '/vendor/', '/dist/', '/build/', '/.next/'];

// Each rule: files matching `file` must NOT contain any `forbidden` pattern.
// Adjust the `file` regexes to the repo's actual directory names.
const RULES = [
  {
    name: 'core/domain must be pure (no IO, framework, env, clock, random, adapters)',
    file: /\/(core|domain)\//,
    forbidden: [
      /\/adapters\//,
      /\bprocess\.env\b/, /\bDate\.now\(\)/, /\bMath\.random\(\)/,
      /from ['"](react|react-dom|next(\/|')|express|fastify|koa|@nestjs\/)/,
      /from ['"](fs|path|http|https|axios|got|node-fetch|undici)['"]/,
      /from ['"](pg|mysql2|mongoose|prisma|typeorm|sequelize|ioredis|redis|bullmq|amqplib|kafkajs)['"]/,
    ],
  },
  {
    name: 'application must depend on ports, not concrete adapters/frameworks',
    file: /\/application\//,
    forbidden: [/\/adapters\//, /from ['"](express|fastify|koa|@nestjs\/)/],
  },
  {
    name: 'transport must not touch infrastructure directly',
    file: /\/(transport|controllers|handlers)\//,
    forbidden: [/\/adapters\/(db|stripe|queue)\//, /from ['"](pg|mysql2|prisma|typeorm|sequelize|axios|got|node-fetch)['"]/],
  },
  {
    name: 'generated files must not be hand-edited',
    file: /\/generated\//,
    forbidden: [/MANUAL EDIT/i],
  },
];

let failed = false;
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const abs = path.join(dir, entry.name);
    const rel = '/' + path.relative(ROOT, abs).split(path.sep).join('/');
    if (IGNORE.some((p) => (rel + '/').includes(p))) continue;
    if (entry.isDirectory()) { walk(abs); continue; }
    if (!EXTENSIONS.has(path.extname(entry.name))) continue;
    const text = fs.readFileSync(abs, 'utf8');
    for (const rule of RULES) {
      if (!rule.file.test(rel)) continue;
      for (const pat of rule.forbidden) {
        if (pat.test(text)) {
          failed = true;
          console.error(`${rel.slice(1)}: violates "${rule.name}" (${pat})`);
        }
      }
    }
  }
}
walk(ROOT);
if (failed) process.exit(1);
console.log('check-boundaries: ok');
