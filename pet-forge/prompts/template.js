/**
 * pet-forge APNG 路线 —— 通用 Prompt 模板（25 个交付状态）
 * ─────────────────────────────────────────────────────────────
 * 这是模板，不是成品。用户必须改 CHARACTER_PREFIX 适配自己的角色。
 *
 * 状态库结构来自 APNG 桌宠实战模板（24 个 prompt 条目）
 * + PROGRESS.md 的 25 个锁定交付状态（mini-peek 来自剪辑产物）。
 * 抽掉了角色专属描述，留下通用骨架 + 实战验证过的 loop / 首尾帧关系。
 *
 * ─────────────────────────────────────────────────────────────
 * ⚠️ 首尾帧关系（影响 gen-video.js 命令选项），3 类：
 *
 *   A. 循环 (loop: true)
 *      首 = 尾 (同一张参考图, 通常是主参考)
 *      → <动画名> --image X --last-frame X
 *
 *   B. 一次性·回归型 (loop: false, anchor: 'same')
 *      做完动作回到中性姿势, 首尾帧相同
 *      → <动画名> --image X --last-frame X
 *
 *   C. 一次性·过渡型 (loop: false, anchor: 'different')
 *      状态间过渡, 首尾帧是不同姿态
 *      → <动画名> --image X --last-frame Y  (X != Y)
 *
 * 详细决策树见 routes/apng/conventions/loop-and-anchoring.md
 * ─────────────────────────────────────────────────────────────
 */

// ── 1. 角色外观描述（用户必须改这里） ────────────────────────
//
// 重要：这段描述是所有状态共享的，决定了角色一致性。
// 写得越具体，AI 生成的多状态越像同一只角色。
//
// 应该包含 6 个维度：
// - 物种 / 类别（cat / robot / cloud creature ...）
// - 风格定位（chibi / kawaii / pixel-art / realistic ...）
// - 颜色 / 花纹（cream body with orange patches / metallic gray ...）
// - 主要识别特征（big round eyes with white highlights / small triangle ears ...）
// - 描边 / 渲染风格（thick dark outlines / cell-shaded / NO 3D rendering ...）
// - 背景要求（plain solid green #00B140 background）
//
export const CHARACTER_PREFIX = `A cute chibi/kawaii style seal point bicolor Ragdoll cat in 3/4 sitting view.

Coat: white body with dark seal-brown color points on the EARS, FACE MASK, and TAIL TIP. Long fluffy semi-long fur — visible fluffy ruff around the neck, large plumed fluffy tail (signature Ragdoll trait — tail is noticeably bigger and fluffier than a typical cartoon cat).

Face mask: dark seal-brown around the eyes covering cheeks and forehead, with a clear WHITE INVERTED-V BLAZE running down the center of the forehead between the eyes to the pink nose. White chin and bib. The blaze position must be identical in every frame.

Body: plump and rounded chibi proportions (≈55% head/body ratio), with white "mitten" socks on all four paws (legs of normal cat length, NOT super-short like a Munchkin).

Ears: triangle, seal-brown outer with pink inner.

Eyes: large round bright SKY-BLUE with one white sparkle highlight — the distinctive Ragdoll blue.

Face: tiny pink triangle nose. Small black smile mouth. 3 thin black whisker lines per side. NO cheek blush — face has only eyes, nose, mouth, and whiskers (do NOT add pink circular blush dots).

Art style: clean kawaii vector cartoon with thick (3-4px) dark warm-brown outlines, flat color fills, with the fluffy fur edge suggested by a slightly wavy silhouette and a few small fur tufts at the ruff and tail base. NO pixel art, NO realistic rendering, NO 3D, NO airbrush.

Background: plain solid green (#00B140) chroma-key.

Consistency contract: every frame must show the SAME blue-eyed seal-point bicolor Ragdoll — same fluffy silhouette, same face mask, same white blaze in the same position, same white mittens, no cheek blush.`;

// ── 2. 绿幕背景强调（一般不用改） ────────────────────────────
export const BG_SUFFIX = `The background must remain a uniform solid green (#00B140) throughout the entire video. No shadows, no objects, no gradients on the background.`;

// ── 3. 完整状态库（25 个交付状态，按通用 state-mapping 分类） ────
//
// 字段说明：
//   loop      —— 是否循环 (true / false)
//   anchor    —— 'same' (首=尾) / 'different' (首≠尾, 仅一次性过渡型)
//   duration  —— 参考时长 (秒)
//   refKey    —— 推荐使用哪张参考图（main = 主参考图 / 自定义 key）
//   lastKey   —— 一次性过渡型的尾帧参考图 key
//   prompt    —— 动作描述（不含 CHARACTER_PREFIX 和 BG_SUFFIX，拼接时自动加）
//   notes     —— 质检要点
//
// ▼ 25 个交付状态，按用途分组 ▼
//
export const ANIMATIONS = {

  // ─── core states (核心循环, 桌宠主体感来自这一组) ─────────
  // 这一组都是 A 类: loop=true, 首=尾

  'idle-dozing': {
    name: '待机呼吸 (sleepy)',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'main',
    prompt: `The cat is in its drowsy sleepy pose (matching the input reference image — lying belly-down or sitting slumped with eyes mostly closed as drowsy heavy lids, body relaxed and droopy). The cat STAYS in this signature drowsy pose throughout the loop — does NOT sit up alert. Animations within the pose: (1) eyes droop further closed almost fully shut as flat dashes, hold a beat, then reopen part-way to drowsy half-lids again, in a slow drowsy rhythm — clear visible eyelid motion; (2) body breathes slowly and visibly with rise-and-fall; (3) head occasionally nods downward as if dozing off then jerks back gently with a tiny startled wobble; (4) tail tip flicks lazily once or twice; (5) one ear occasionally twitches; (6) small "Zzz" or Z bubbles float up from above the head and drift away gently — repeat 1-2 times during the loop. Cozy drowsy mood, very cute. Seamless loop animation.`,
    notes: '困倦灵动 v5: 保持droopy pose+眼皮重闭+点头+尾尖+Zzz',
  },

  'idle-living': {
    name: '空闲小动作',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'main',
    prompt: `The character is in standard pose, casually doing a small grooming/idle motion (适配你的角色: 舔爪 / 整理触角 / 擦镜头), then pauses with content expression, then repeats. Relaxed and cozy throughout. Seamless loop — the last frame connects perfectly back to the first frame. Body stays in place.`,
    notes: '小动作循环, 不要太复杂动作免得首尾对不齐',
  },

  'thinking': {
    name: '思考',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'main',
    prompt: `The cat is in its thoughtful pondering pose (matching the input reference image — body tilted to one side or lying on belly, one front paw raised toward chin/cheek, head tilted thoughtfully, with a yellow ? mark visible). The cat STAYS in this signature thinking pose throughout the loop. Animations within the pose: (1) the QUESTION MARK '?' floats above the head, gently bobbing up-and-down or slowly rotating in place — clearly visible and animated throughout; (2) head tilts slowly side-to-side in a thoughtful rhythm (small angle changes, ~10-15 degrees); (3) eyes blink occasionally and look upward at the imagined ? as if reading it; (4) the raised paw occasionally taps the cheek/chin softly; (5) tail tip flicks slowly side-to-side; (6) ears occasionally twitch one at a time. Cute thoughtful curious mood. Seamless loop.`,
    notes: '思考灵动 v5: 保持paw-to-chin pose+?号飘/转+头微倾+尾尖',
  },

  'working-typing': {
    name: '工作-打字',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'main',
    prompt: `The cat is in its hardworking-at-laptop pose (matching the input reference image — lying belly-down on a small wood surface with a chibi laptop in front of it, both front paws on the keyboard, focused intent expression). The cat STAYS in this signature working-at-laptop pose throughout the loop. Animations within the pose: (1) BOTH front paws tap rapidly up-and-down on the keyboard in a clearly visible alternating left-right typing rhythm — fast and obvious motion; (2) head bobs slightly forward-back with the typing rhythm; (3) eyes are focused on the screen, occasionally darting left-right as if reading code, with one quick blink; (4) eyebrows slightly furrowed in concentration; (5) tail extended behind sways back-and-forth determinedly; (6) one ear occasionally twitches alert; (7) optional: tiny "*" sparkles or briefly visible "<>" characters float near the laptop screen. Hardworking focused mood, cat is REALLY into it. Laptop and small props (phone if visible) stay in the same position. Seamless loop.`,
    notes: '打字灵动 v5: 保持笔记本pose+爪子节奏+头晃+眼神扫+尾巴',
  },

  'working-building': {
    name: '工作-建造/拧螺丝',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'building',
    prompt: `The character is operating a tool (screwdriver / hammer / your character's tool) on a workpiece. Performs the operation with focused, determined expression, then repositions, then repeats. Tail sways slightly. Seamless loop animation. Body stays in place. NO hands, NO fingers visible (use your character's natural manipulators).`,
    notes: '拿工具+认真表情+循环衔接',
  },

  'working-juggling': {
    name: '工作-玩耍/抛接',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'juggling',
    prompt: `The character holds a small object (yarn ball / orb / your character's prop) with its hands/paws. Plays with it (bats / juggles / spins), maybe falls back briefly, then returns to the EXACT starting pose holding the object. Seamless loop animation — the last frame connects perfectly back to the first frame.`,
    notes: '动作要回到起始抱物体姿态, 才能无缝循环',
  },

  'working-conducting': {
    name: '工作-指挥',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'main',
    prompt: `The character has a proud, smug expression. Its tail/baton/extending part raised high and sways rhythmically left-right-left like a conductor's baton, keeping a steady tempo. Small musical notes float nearby. Head bobs slightly in rhythm. Seamless loop — the last frame connects perfectly back to the first frame. Body stays in place, only the extending part sways.`,
    notes: '尾巴/触角左右摆作指挥棒, 傲娇表情',
  },

  'working-sweeping': {
    name: '工作-擦/扫',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'sweeping',
    prompt: `The character is using one hand/paw to wipe a surface (table / floor / cloth), moving left and right in a steady wiping motion. Cheerful, diligent expression. Tail sways gently. Seamless loop — the last frame connects perfectly back to the first frame. The character stays in place, only the wiping part moves.`,
    notes: '左右擦动+开心表情+循环',
  },

  'working-carrying': {
    name: '工作-搬运',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'carrying',
    prompt: `The character is carrying a small object (fish / box / your character's item) walking proudly. Walks left a few steps, turns around, walks right a few steps, returns to starting position. Happy, proud expression with squinted eyes throughout. Tail raised high, sways as it walks. Seamless loop — the last frame connects perfectly back to the first frame.`,
    notes: '叼/抱物左右走+得意表情+循环',
  },

  // ─── reaction states (用户交互触发) ──────────────────────

  'react-drag': {
    name: '被拖动',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'react-drag',
    prompt: `The character is floating in the air as if being dragged by an invisible force. NO hands visible. Looks thrilled and excited — eyes wide and sparkling, big happy grin, ears/extensions perked forward. Limbs spread out like airplane wings. Tail streams behind like a flag. Body sways and bounces slightly as if riding a rollercoaster. Seamless loop animation. Fun and energetic. DO NOT draw any hands or fingers.`,
    notes: '无手, 角色悬浮兴奋飞行姿态, 循环',
  },

  'react-poke': {
    name: '被戳反应 (一次性·回归型)',
    loop: false,
    anchor: 'same',
    duration: 2.5,
    refKey: 'main',
    prompt: `The character flinches and leans to one side with a surprised expression — eyes wide, ears perked. Raises one hand/paw as if startled. Then settles back to the EXACT original pose. 2.5 seconds, cute and slightly startled. NO hands, NO fingers visible — character reacts as if touched by an invisible force. The ending pose must match the starting pose EXACTLY.`,
    notes: '惊讶歪身+抬手→回原姿势, 首尾帧严格一致',
  },

  // ─── notification / completion (一次性·回归型) ────────────

  'happy': {
    name: '任务完成',
    loop: false,
    anchor: 'same',
    duration: 4,
    refKey: 'main',
    prompt: `The cat is celebrating with PURE OVER-THE-TOP JOY. Multiple energetic animations together: (1) eyes squinted into HUGE happy crescent shapes (^^ ^^) — closed-curve upturned smile-eyes, very expressive — these stay throughout the loop; (2) tail standing straight up wagging enthusiastically left-right RAPIDLY (clear visible wagging motion); (3) body wiggling/bouncing slightly with joy — small bounce up and down or shake; (4) MULTIPLE sparkle ✨, small flower petals 🌸, hearts ♥, and stars ⭐ float and pop up around the cat in multiple positions — at least 4-5 particles visible at any time, drifting gently outward and disappearing then more spawning, throughout the loop; (5) maybe a tiny hop or excited little jump in place; (6) ears perked up alert. PURE JOY mood — over-the-top cute celebration with lots of motion and particles. Seamless loop.`,
    notes: '开心灵动: 眯眼+尾巴狂摇+身体抖+花花星星飘+小跳',
  },

  'notification': {
    name: '通知/警觉',
    loop: false,
    anchor: 'same',
    duration: 2.5,
    refKey: 'main',
    prompt: `The cat is in its alert notification pose (matching the input reference image — sitting attentive with ears straight up, eyes wide with surprise, and a BIG BOLD red EXCLAMATION MARK '!' floating prominently to one side at head level). The cat STAYS in this signature alert pose throughout the animation. Animations within the pose: (1) the EXCLAMATION MARK '!' bounces up-and-down rhythmically or vibrates with attention-grabbing motion — clearly visible throughout, this is the signature element; (2) ears stay perked up and rotate slightly forward; (3) eyes stay wide-open bright and may briefly sparkle; (4) tail puffs up slightly or stays alert; (5) body remains in the alert pose (sit/lean) without morphing; (6) head holds at a slight upward alert angle. Sharp clean motion, NO ghosting, NO doubled frames, body stays in same alert position. The ! mark IS prominent and OBVIOUS. Seamless loop animation.`,
    notes: '通知灵动 v5: 保持alert pose+!号弹跳显眼+耳朵竖+睁大眼',
  },

  'error': {
    name: 'XX眼晕倒',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'error',
    prompt: `CRITICAL POSE: the cat is LYING DOWN ON ITS SIDE OR BACK, body fully horizontal (matching the input error reference image exactly — knocked-out flat-on-the-ground pose with X-shaped eyes, tongue lolling, puff cloud and sparkle stars above). The cat STAYS in this lying knockout pose throughout the loop. DO NOT change to sitting up, DO NOT animate body to a different pose. Multiple subtle animations within the lying pose: (1) body breathes slowly with visible rise-and-fall while lying; (2) the puff cloud above the head slowly drifts in position and shifts shape; (3) the sparkle stars circle slowly around the head, twinkling; (4) the tongue tip wiggles or twitches slightly; (5) one paw twitches weakly occasionally; (6) whiskers occasionally twitch. Eyes STAY drawn as X-shapes (× ×) the entire time. Comedic dazed mood, cat is OUT. Seamless loop, body remains horizontal lying down throughout.`,
    notes: '晕倒灵动 v5: 保持侧躺XX眼+呼吸+星星绕头+舌头抖+爪子抖',
  },

  // ─── idle 装饰类 (一次性·回归型, 长时间空闲触发) ─────────

  'idle-yawn': {
    name: '打哈欠 (装饰)',
    loop: false,
    anchor: 'same',
    duration: 3,
    refKey: 'main',
    prompt: `The character is in standard pose. Slowly opens its mouth very wide in a big yawn — tongue curling, eyes squeezing shut. Then closes mouth, does a small head shake, returns to original pose with eyes open. Smooth animation, 3 seconds total. Stays in place, only head and mouth move significantly. Body breathes gently. Return to the EXACT starting pose at the end.`,
    notes: '装饰动画, 长时间空闲触发, 首尾严格一致',
  },

  'idle-look': {
    name: '四处张望 (装饰)',
    loop: false,
    anchor: 'same',
    duration: 6.5,
    refKey: 'main',
    prompt: `The character looks around curiously. Head turns slowly to the left, pauses, then turns to the right, pauses, then returns to center facing forward. Body stays in place, only head moves. Ears twitch occasionally. Curious and calm expression. 6.5 seconds total.`,
    notes: '头左转→停→右转→停→回正, 身体不动, 装饰动画',
  },

  // ─── sleeping 链 (混合 A/B/C 三类) ──────────────────────

  'sleeping': {
    name: '睡觉循环',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'sleep-final',
    prompt: `The cat is curled up in its peaceful sleeping pose (matching the input sleep-final reference image — curled tight or lying on side with eyes closed as flat horizontal dashes). Stays in this curled sleeping pose throughout. Multiple gentle peaceful animations: (1) body breathes slowly and visibly with clear rise-and-fall on the side; (2) tail tip occasionally flicks lazily as if dreaming; (3) one paw or whisker twitches subtly once or twice (dream twitch); (4) "Zzz" text or Z bubbles drift up from above the head — at least 2 separate Z bubbles during the loop, staggered in time, drifting up and fading out; (5) corner of mouth occasionally relaxes into a tiny content micro-smile. Eyes STAY completely closed. Seamless loop, cozy peaceful mood.`,
    notes: '睡眠灵动 v5: 蜷成球+呼吸+尾巴抖+做梦微抖+Zzz飘',
  },

  'collapse-sleep': {
    name: '快速倒下入睡 (一次性·过渡型)',
    loop: false,
    anchor: 'different',
    duration: 0.8,
    refKey: 'main',
    lastKey: 'sleep-final',
    prompt: `The cat transitions from upright sitting (input first-frame matches main reference) to curled-up sleeping (last frame matches sleep-final reference). Smooth expressive comedic falling-asleep transition over 0.8 seconds: (1) eyes start drooping then close fully into flat horizontal lines; (2) body slowly tilts to one side losing balance with a comedic small wobble; (3) cat tumbles gently sideways with a tiny "thud" feel; (4) curls up into a loaf shape on the ground; (5) tail wraps around alongside body; (6) ends in the peaceful sleeping curled pose. End pose MUST match the sleep-final reference image exactly. Smooth fluid motion with personality.`,
    notes: '倒下入睡灵动 v5: 闭眼+歪倒+小晕+蜷起, 结尾对齐sleep-final',
  },

  'wake': {
    name: '醒来伸懒腰 (一次性·过渡型)',
    loop: false,
    anchor: 'different',
    duration: 1.5,
    refKey: 'sleep-final',
    lastKey: 'main',
    prompt: `The cat transitions from curled-up sleeping (input first-frame matches sleep-final reference) to upright sitting alert (last frame matches main reference). Expressive lively wake animation over 1.5 seconds: (1) body uncurls with both front paws stretching forward in a long satisfying cat-stretch; (2) back arches up high in a deep stretch; (3) ONE BIG WIDE YAWN — mouth opens very wide showing tiny pink tongue, eyes squeezing tightly shut, head tilted back slightly; (4) yawn closes, head shakes briefly side-to-side as if shaking off sleep; (5) eyes open wide and bright, alert and ready; (6) cat sits upright in the standard alert sitting pose. Lots of personality, smooth fluid expressive motion. End pose MUST match the main reference image exactly.`,
    notes: '醒来灵动 v5: 伸懒腰+弓背+大哈欠+甩头+睁大眼+坐起, 结尾对齐main',
  },

  // ─── mini mode (dock/tray 缩放模式, 6 状态) ─────────────

  'mini-idle': {
    name: 'mini 待机',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'mini',
    prompt: `The character is in a relaxed lying / sideways / curled pose (DIFFERENT from main idle, this is the mini-mode pose). Calm and content expression. Gentle breathing — body slowly rises and falls. Slow blinks. Slightly turns head to look to one side, then slowly back to center. Very gentle movement. Seamless loop, very calm. DO NOT change pose. Body stays in same lying position throughout.`,
    notes: 'mini 模式 ≠ 缩小版 idle, 是不同姿态',
  },

  'mini-enter': {
    name: 'mini 入场 (一次性·过渡型)',
    loop: false,
    anchor: 'different',
    duration: 3,
    refKey: 'offscreen-left',
    lastKey: 'mini',
    prompt: `The character runs playfully from off-screen, then flops down and rolls into the mini-idle pose. Quick and energetic run, then a cute tumble onto the mini pose. Happy and playful expression throughout.`,
    notes: '从场外跑→躺倒到 mini-idle 位置, 首≠尾',
  },

  'mini-peek': {
    name: 'mini 探头 (剪辑或独立)',
    loop: false,
    anchor: 'same',
    duration: 2,
    refKey: 'mini',
    prompt: `The character (in mini pose) peeks out and waves briefly, then settles back to mini-idle pose. Cute brief reaction. End pose matches mini-idle EXACTLY.`,
    notes: '可以从其他动画剪辑出来, 也可以独立生成',
  },

  'mini-alert': {
    name: 'mini 通知',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'mini',
    prompt: `The character is in mini pose. A red exclamation mark (!) pops up beside, bouncing and flashing. Eyes widen with surprised expression, ears perk. Body stays in same mini pose, only eyes react and exclamation animates. Seamless loop animation.`,
    notes: 'mini 姿态+弹出感叹号+惊讶, 循环',
  },

  'mini-happy': {
    name: 'mini 完成庆祝',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'mini',
    prompt: `The character is in mini pose. Small sparkles, stars and flower petals float and pop around. Very happy expression — eyes squinted into happy crescents (^^), content and proud. Body stays in same mini pose, only sparkle effects animate and tail wags slightly. Seamless loop animation.`,
    notes: 'mini 姿态+花花星星飘+眯眼笑, 循环',
  },

  'mini-sleep': {
    name: 'mini 休眠',
    loop: true,
    anchor: 'same',
    duration: 5,
    refKey: 'mini',
    prompt: `The character is in mini pose, eyes CLOSED, sleeping deeply. Eyes must stay CLOSED entire time. The only movement is very gentle breathing — body slowly rises and falls. Small "Zzz" text floats up and fades, repeating in loop. Very calm and cozy. Seamless loop. DO NOT open eyes. DO NOT change camera angle.`,
    notes: 'mini 闭眼睡+呼吸+Zzz, 极简循环',
  },

  'walk-across': {
    name: '横穿屏幕 - 软糯版',
    loop: true,
    anchor: 'same',
    duration: 3,
    refKey: 'walk-across',
    prompt: `胖猫（the seal-point Ragdoll with sky-blue eyes and long fluffy white-and-cream coat）walks across the frame from LEFT EDGE to RIGHT EDGE with a slow lumbering soft gait. The long fluffy fur creates visible motion blur and the body sways with each step. 4 paw cycles. Tail thick and slowly swishing behind. Walks a bit lazily but determined. Body translates continuously left-to-right within the frame. Calm, content expression. Eyes half-lidded and pleased.`,
    notes: 'Ragdoll长毛慢悠悠步伐, 长毛随风摆动有motion blur',
  },
};

// ── 4. 拼接函数（生成最终 prompt 给 API） ────────────────────
export function buildFullPrompt(animationKey) {
  const anim = ANIMATIONS[animationKey];
  if (!anim) {
    const keys = Object.keys(ANIMATIONS).join(', ');
    throw new Error(`未知动画: "${animationKey}"。可选: ${keys}`);
  }
  return `${CHARACTER_PREFIX}\n\n${anim.prompt}\n\n${BG_SUFFIX}`;
}

// ── 5. 列出所有动画（按首尾帧关系分组） ──────────────────────
export function listAnimations() {
  console.log('\n════════ 状态库 (共 ' + Object.keys(ANIMATIONS).length + ' 个交付状态) ════════\n');

  const groupA = []; // 循环
  const groupB = []; // 一次性·回归型
  const groupC = []; // 一次性·过渡型

  for (const [key, anim] of Object.entries(ANIMATIONS)) {
    const line = `  ${key.padEnd(20)} ${anim.name.padEnd(20)} ${anim.duration}s`;
    if (anim.loop) groupA.push(line);
    else if (anim.anchor === 'same') groupB.push(line);
    else groupC.push(line);
  }

  console.log('─── A. 循环动画 (loop:true, 首=尾) ───');
  groupA.forEach(l => console.log(l));
  console.log(`\n─── B. 一次性·回归型 (loop:false, 首=尾) ───`);
  groupB.forEach(l => console.log(l));
  console.log(`\n─── C. 一次性·过渡型 (loop:false, 首≠尾) ───`);
  groupC.forEach(l => console.log(l));
  console.log('');
}

// ── 6. 生成 gen-video.js 命令（按 anchor 类型自动选项） ─────
export function buildGenVideoCommand(animationKey, refImagePaths) {
  const anim = ANIMATIONS[animationKey];
  if (!anim) throw new Error(`未知动画: ${animationKey}`);

  const refPath = refImagePaths[anim.refKey];
  if (!refPath) throw new Error(`refKey "${anim.refKey}" 没有对应路径`);

  const parts = [
    'node gen-video.js',
    animationKey,
    `--image ${refPath}`,
    '--api doubao',
  ];

  // 关键：根据 anchor 决定 --last-frame 用什么
  if (anim.anchor === 'same') {
    // A 类(循环) + B 类(回归型) 都是首=尾
    parts.push(`--last-frame ${refPath}`);
  } else {
    // C 类(过渡型) 首≠尾, 用 lastKey 指定的尾帧
    const lastPath = refImagePaths[anim.lastKey];
    if (!lastPath) throw new Error(`lastKey "${anim.lastKey}" 没有对应路径`);
    parts.push(`--last-frame ${lastPath}`);
  }

  parts.push(`--no-chroma`);
  return parts.join(' \\\n  ');
}
