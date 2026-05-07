#!/usr/bin/env node
/**
 * pet-forge APNG tools - image generation script
 *
 * Usage:
 *   node gen-images.js <animation-key>
 *   node gen-images.js --prompt "..." --output reference/main-ref.png
 *   node gen-images.js <animation-key> --count 3
 *   node gen-images.js --list
 *
 * Generated files are saved to output/<animation-key>/ by default.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { doubaoGenerateImage, saveImage } from './lib/api.js';
import { buildPrompt, listAnimations, ANIMATIONS } from './prompts.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── CLI args ─────────────────────────────────────────────

const args = process.argv.slice(2);

function getArg(flag, defaultVal) {
  const idx = args.indexOf(flag);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : defaultVal;
}

if (args.includes('--list') || args.includes('-l')) {
  listAnimations();
  process.exit(0);
}

if (args.length === 0) {
  console.log('用法: node gen-images.js <动画名> [选项]');
  console.log('      node gen-images.js --prompt "..." --output reference/main-ref.png');
  console.log('      node gen-images.js --list    列出所有可用动画');
  console.log('\n选项:');
  console.log('  --api doubao      选择 API（当前公开版仅保留 doubao）');
  console.log('  --count <数量>    生成几张（默认 1）');
  console.log('  --model <模型名>  覆盖默认图片模型');
  process.exit(0);
}

function assertSupportedApi(apiChoice) {
  if (apiChoice !== 'doubao') {
    throw new Error('当前公开版仅保留 --api doubao');
  }
}

async function saveFirstImageResult(result, outputPath) {
  if (result.data && Array.isArray(result.data)) {
    for (const item of result.data) {
      const imgData = item.url || item.b64_json;
      if (imgData) {
        fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });
        await saveImage(imgData, outputPath);
        return outputPath;
      }
    }
  }
  const jsonPath = outputPath.replace(/\.[^.]+$/, '') + '-raw.json';
  fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
  console.log(`  ⚠ 未找到图片数据，已保存原始响应: ${jsonPath}`);
  return jsonPath;
}

const apiChoice = getArg('--api', 'doubao');
assertSupportedApi(apiChoice);

const modelOpt = getArg('--model', null);
const directPrompt = getArg('--prompt', null);
if (directPrompt) {
  const outputPath = getArg('--output', 'reference/main-ref.png');

  console.log(`\n🎨 生成参考图: ${outputPath}`);
  console.log('   API: doubao\n');

  const result = await doubaoGenerateImage(directPrompt, {
    model: modelOpt || undefined,
  });
  const saved = await saveFirstImageResult(result, outputPath);

  console.log(`\n✅ 完成: ${saved}\n`);
  process.exit(0);
}

const animKey = args[0];
if (!ANIMATIONS[animKey]) {
  console.error(`❌ 未知动画: "${animKey}"`);
  listAnimations();
  process.exit(1);
}

const count = parseInt(getArg('--count', '1'), 10);
if (!Number.isInteger(count) || count < 1) {
  throw new Error('--count 必须是正整数');
}

// ── Output setup ─────────────────────────────────────────

const outDir = path.join(__dirname, 'output', animKey);
fs.mkdirSync(outDir, { recursive: true });

const prompt = buildPrompt(animKey);
const anim = ANIMATIONS[animKey];

console.log(`\n🎨 生成图片: ${animKey} (${anim.name})`);
console.log(`   API: doubao, 数量 ${count}`);
console.log(`   输出目录: ${outDir}\n`);

// ── Generate ─────────────────────────────────────────────

const results = [];

console.log('── Doubao / Volcengine image generation ──');
for (let i = 0; i < count; i++) {
  try {
    const tag = `doubao-${String(i + 1).padStart(2, '0')}`;
    console.log(`\n  [${tag}] 生成中...`);
    const result = await doubaoGenerateImage(prompt, {
      model: modelOpt || undefined,
    });

    if (result.data && Array.isArray(result.data)) {
      for (let j = 0; j < result.data.length; j++) {
        const item = result.data[j];
        const filename = `${tag}-${j + 1}.png`;
        const outPath = path.join(outDir, filename);
        const imgData = item.url || item.b64_json;
        if (imgData) {
          await saveImage(imgData, outPath);
          results.push(outPath);
        }
      }
    } else {
      const jsonPath = path.join(outDir, `${tag}-raw.json`);
      fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
      console.log(`  ⚠ 未找到图片数据，已保存原始响应: ${jsonPath}`);
      results.push(jsonPath);
    }
  } catch (err) {
    console.error(`  ❌ 生图失败: ${err.message}`);
  }
}

// ── Summary ──────────────────────────────────────────────

console.log(`\n${'─'.repeat(50)}`);
console.log(`✅ 完成！共生成 ${results.length} 个文件:`);
results.forEach(f => console.log(`   ${f}`));
console.log(`\n去 ${outDir} 挑选你喜欢的图片，然后用 gen-video.js 生成视频。\n`);
