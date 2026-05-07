#!/usr/bin/env node
/**
 * pet-forge APNG tools - video generation script
 *
 * Usage:
 *   node gen-video.js <animation-key> --image reference/main-ref.png
 *   node gen-video.js <animation-key> --image selected.png --last-frame selected.png --api doubao
 *
 * Generated videos are saved to output/<animation-key>/.
 * Use chroma_key.py to convert downloaded videos into APNG files.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { doubaoGenerateVideo, downloadBuffer } from './lib/api.js';
import { ANIMATIONS, buildPrompt } from './prompts.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── CLI args ─────────────────────────────────────────────

const args = process.argv.slice(2);

if (args.length === 0) {
  console.log('用法: node gen-video.js <动画名> --image <首帧图片路径> [选项]');
  console.log('\n选项:');
  console.log('  --image <路径>      首帧参考图片（必填，除非用 --no-first-frame）');
  console.log('  --last-frame <路径> 尾帧参考图片（循环/回归型通常同 --image）');
  console.log('  --api doubao        选择 API（当前公开版仅保留 doubao）');
  console.log('  --model <模型名>    覆盖默认视频模型');
  console.log('  --ref-mode          图片作为角色参考，不锚定首帧');
  console.log('  --no-first-frame    不设首帧，只设尾帧');
  console.log('  --no-chroma         跳过 chroma_key 后处理');
  process.exit(0);
}

function getArg(flag, defaultVal) {
  const idx = args.indexOf(flag);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : defaultVal;
}

const animKey = args[0];
const imagePath = getArg('--image', null);
const apiChoice = getArg('--api', 'doubao');
const modelOpt = getArg('--model', null);
const lastFramePath = getArg('--last-frame', null);
const refMode = args.includes('--ref-mode');
const noFirstFrame = args.includes('--no-first-frame');
const skipChroma = args.includes('--no-chroma');

if (apiChoice !== 'doubao') {
  throw new Error('当前公开版仅保留 --api doubao');
}

if (!ANIMATIONS[animKey]) {
  console.error(`❌ 未知动画: "${animKey}"`);
  process.exit(1);
}
if (!noFirstFrame && (!imagePath || !fs.existsSync(imagePath))) {
  console.error('❌ 请用 --image 指定首帧图片路径，或用 --no-first-frame 跳过');
  process.exit(1);
}
if (lastFramePath && !fs.existsSync(lastFramePath)) {
  console.error(`❌ 尾帧图片不存在: ${lastFramePath}`);
  process.exit(1);
}

const anim = ANIMATIONS[animKey];
const prompt = buildPrompt(animKey);

// ── Output setup ─────────────────────────────────────────

const outDir = path.join(__dirname, 'output', animKey);
fs.mkdirSync(outDir, { recursive: true });

console.log(`\n🎬 生成视频: ${animKey} (${anim.name})`);
console.log(`   首帧图片: ${imagePath || '(none)'}`);
console.log('   API: doubao');
console.log(`   输出目录: ${outDir}\n`);

// ── Generate video ───────────────────────────────────────

const results = [];

console.log('── Doubao / Volcengine video generation ──\n');
try {
  let dataUri = null;
  if (imagePath) {
    const imgBuf = fs.readFileSync(imagePath);
    const b64 = imgBuf.toString('base64');
    const ext = path.extname(imagePath).slice(1) || 'png';
    dataUri = `data:image/${ext};base64,${b64}`;
  }

  let videoPrompt = prompt;
  let lastFrameUri = null;

  if (noFirstFrame) {
    dataUri = null;
    if (lastFramePath) {
      const lastBuf = fs.readFileSync(lastFramePath);
      const lastB64 = lastBuf.toString('base64');
      const lastExt = path.extname(lastFramePath).slice(1) || 'png';
      lastFrameUri = `data:image/${lastExt};base64,${lastB64}`;
      console.log(`  模式: 仅尾帧锚定 → ${lastFramePath}`);
    }
  } else if (refMode) {
    videoPrompt = `[图1]是角色参考图。${prompt}`;
    console.log('  模式: 参考图（不锚定首帧）');
  } else {
    const lastSrc = lastFramePath || (anim.loop ? imagePath : null);
    if (lastSrc) {
      const lastBuf = fs.readFileSync(lastSrc);
      const lastB64 = lastBuf.toString('base64');
      const lastExt = path.extname(lastSrc).slice(1) || 'png';
      lastFrameUri = `data:image/${lastExt};base64,${lastB64}`;
      console.log(`  首尾帧锚定: ${lastSrc === imagePath ? '首尾帧相同' : lastSrc}`);
    }
  }

  const result = await doubaoGenerateVideo(videoPrompt, dataUri, {
    model: modelOpt || undefined,
    lastFrameUrl: lastFrameUri,
    asReference: refMode,
  });

  let videoUrl = null;
  if (result.video_url) {
    videoUrl = result.video_url;
  } else if (result.content && result.content.video_url) {
    videoUrl = result.content.video_url;
  } else if (result.content && Array.isArray(result.content)) {
    const videoItem = result.content.find(c => c.type === 'video_url' || c.type === 'video');
    if (videoItem) videoUrl = videoItem.video_url?.url || videoItem.url;
  } else if (result.data && result.data.video_url) {
    videoUrl = result.data.video_url;
  }

  if (videoUrl) {
    const videoPath = path.join(outDir, 'doubao-video.mp4');
    const buf = await downloadBuffer(videoUrl);
    fs.writeFileSync(videoPath, buf);
    console.log(`  ✓ 视频已下载: ${videoPath}`);
    results.push(videoPath);
  } else {
    const jsonPath = path.join(outDir, 'doubao-video-raw.json');
    fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2));
    console.log(`  ⚠ 未找到视频 URL，已保存原始响应: ${jsonPath}`);
  }
} catch (err) {
  console.error(`  ❌ 视频生成失败: ${err.message}`);
}

// ── Chroma-key post-processing ───────────────────────────

if (!skipChroma && results.length > 0) {
  console.log('\n── chroma_key 后处理 ──\n');
  const chromaScript = path.join(__dirname, 'chroma_key.py');

  if (!fs.existsSync(chromaScript)) {
    console.log('  ⚠ chroma_key.py 未找到，跳过后处理');
    console.log('  手动运行: python chroma_key.py <视频路径> <输出.apng>');
  } else {
    const { execSync } = await import('child_process');
    for (const videoPath of results) {
      const apngPath = videoPath.replace('.mp4', '.apng');
      try {
        console.log(`  处理: ${videoPath}`);
        execSync(`python "${chromaScript}" "${videoPath}" "${apngPath}"`, {
          stdio: 'inherit',
          cwd: __dirname,
        });
        console.log(`  ✓ APNG: ${apngPath}`);
      } catch (err) {
        console.error(`  ❌ chroma_key 失败: ${err.message}`);
        console.log(`  手动运行: python "${chromaScript}" "${videoPath}" "${apngPath}"`);
      }
    }
  }
}

// ── Summary ──────────────────────────────────────────────

console.log(`\n${'─'.repeat(50)}`);
console.log(`✅ 完成！共生成 ${results.length} 个视频`);
results.forEach(f => console.log(`   ${f}`));
console.log('');
