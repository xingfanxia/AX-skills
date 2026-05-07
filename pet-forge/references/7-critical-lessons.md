# 7 critical lessons — how to avoid the 12-hour debug spiral

Distilled from the production session that built 小肥 (Munchkin) and 胖猫 (Ragdoll) for clawd-on-desk on 2026-05-06.

Each lesson here cost real time and real API spend. Read all 7 before tweaking the pipeline.

---

## 1. State-pose refs are THE liveliness unlock

**Symptom**: All 10 states look like the same sitting cat with minor face wiggles. No real motion.

**Cause**: Doubao Seedance won't morph far from its first-frame pose in a 4-second clip. If every state's `image` and `lastFrame` is `main-ref.png` (a neutral 3/4 sit), then `working-typing` ends up as "sitting cat with paws on imaginary keyboard," and `thinking` is "sitting cat with vague paw flicker."

**Fix**: Generate a **state-specific pose ref** for each "active" state. The cat is already in the action pose (lying belly-down at a laptop for working-typing, paw to chin for thinking, alert sit for notification). Pass that pose-ref as BOTH `image` and `lastFrame`. The motion prompt then says "stay in this pose, animate within it" and Doubao actually animates.

**Cost of getting it wrong**: ~$2 in retries before realizing it's an architectural issue, not a prompt-tuning issue.

---

## 2. No blush

**Symptom**: gpt-image-2 adds pink/red blush to the cat's cheeks. Looks anime, kills photorealism for tabby/calico breeds. Worse: it's inconsistent across pose-refs (some blush, some don't), so character consistency breaks.

**Cause**: gpt-image-2 has a strong "kawaii style" prior that defaults blush in. Especially triggers on prompts containing "cute," "chibi," "kawaii."

**Fix**: Always add explicit negative phrasing to CHARACTER_PREFIX:
> NO pink cheek blush, NO red cheek circles, clean cheeks matching the body fur color.

Bake it in once at the prefix level, not per-prompt.

---

## 3. Sleep-ref needs two waves

**Symptom**: `collapse-sleep` and `wake` (transition states) animate to a DIFFERENT cat than the active states. Character drift between sleeping/awake variants.

**Cause**: If you generate `sleep-final-ref.png` independently of `main-ref.png`, gpt-image-2 has too much creative freedom and the sleeping cat drifts from the awake cat.

**Fix**: Two-wave generation:

1. **Wave 1**: Generate `main-ref.png` from prompt.
2. **Wave 2**: Generate `sleep-final-ref.png` via gpt-image-2 `--edit` mode chained on `main-ref.png`. Prompt: "same cat, now curled up sleeping with eyes closed."

Then for `collapse-sleep` (transition): `image=main-ref` + `lastFrame=sleep-final-ref`. For `wake`: `image=sleep-final-ref` + `lastFrame=main-ref`.

Same character through the full sleep cycle.

---

## 4. Doubao image+lastFrame anchoring

**Symptom**: APNG loops have a visible jump-cut at the loop boundary — frame 0 ≠ frame N.

**Cause**: Doubao Seedance generates each clip independently from the `image` prompt. Without a `lastFrame` anchor, the final frame can drift several pose-degrees from the first.

**Fix**: For all "loop forever" states (idle-dozing, working-typing, thinking, happy, notification, sleeping):
- `image` = state-pose-ref (the action pose)
- `lastFrame` = SAME state-pose-ref

This forces Doubao to bring the animation back to the start pose at the end. With `--plays 0` (infinite loop) on chroma_key, the boundary is invisible.

For one-shot states (`error`, `react-poke`, `wake`, `collapse-sleep`): `image` and `lastFrame` may differ (start pose vs end pose).

---

## 5. Green-eyed pets need chroma tuning

**Symptom**: After chroma-key, the pet's eye centers look hollow / desaturated / gray. Sometimes there's a translucent halo where the iris should be.

**Cause**: Default `chroma_key.py` HSV mask catches:
- Hue 80-160 (any green-ish color)
- Saturation ≥ 40 (any moderately-saturated green)
- Brightness ≥ 30

Jade-green eyes have hue ~100-120, sat ~50-65%, val ~45-55% — they fall **inside** the green-removal zone. Plus, the despill step pulls "too green" surviving pixels toward gray, finishing the damage.

**Fix**: Use the patched `chroma_key.py` with two flags:

```bash
python3 chroma_key.py input.mp4 output.apng --plays 0 \
  --sat-min 85 \                  # only catch sat≥85% greens (chroma BG is sat=100)
  --despill-sat-min 70             # skip despill on sat<70 (preserves jade pixels)
```

Defaults preserve original behavior (40 / 0). Set both for any pet with green features.

The `is_semi_green` soft-edge mask is also gated by `sat_min` in the patched version — so the edge alpha-reduction won't catch iris pixels either.

**Cost of getting it wrong**: We hit this twice. First fix only handled the full-removal mask; the soft-edge mask still translucent'd the iris to 30% alpha. Second patch (gating `green_ratio` test by `sat >= sat_min`) was the complete fix.

---

## 6. Chinese display names work, directory IDs stay ASCII

**Symptom**: You want the theme picker to show "小肥" / "胖猫" instead of "Munchkin" / "Ragdoll."

**Solution**: Two separate fields:

- `theme.json`'s `name` field → display label, fully Unicode-safe (Electron renders it natively).
- Directory name → stays ASCII for filesystem safety, becomes the theme `id`.

So:
```
themes/munchkin/theme.json    →    "name": "小肥"
themes/ragdoll/theme.json     →    "name": "胖猫"
```

Picker shows "小肥" / "胖猫"; theme-loader uses `munchkin` / `ragdoll` as the stable ID.

---

## 7. Long-coat breeds need fileScales bumped ~5%

**Symptom**: Ragdoll (or any fluffy breed) looks visually smaller than Munchkin (or any short-coat breed) at the same scale. The fluff is taking visual space but the bounding box ratio is unchanged.

**Cause**: clawd-on-desk's `objectScale.fileScales` controls per-state pixel scaling. The default ratios (e.g., `1.05` for idle, `1.20` for thinking) were tuned for short-coat breeds.

**Fix**: For long-coat / fluffy breeds, bump every `fileScales` entry by ~0.05:

```json
// Munchkin (short-coat)
"munchkin-idle-dozing.apng": 1.05,
"munchkin-thinking.apng": 1.20,

// Ragdoll (long-coat) — bump by 0.05
"ragdoll-idle-dozing.apng": 1.10,
"ragdoll-thinking.apng": 1.25,
```

`generate.py` does this automatically when `--breed` mentions Ragdoll/Persian/Maine Coon/Norwegian Forest. Manual override via `--fluffy` flag.

---

## Bonus — rough cost map

| Mistake | Spend to recover |
|---|---|
| Anchoring all states on main-ref (lesson 1) | ~$2 in re-Doubao runs before realizing |
| Forgetting `--sat-min` for green eyes (lesson 5) | $0 (re-chroma is local) but ~3 hours of debugging |
| Generating sleep-ref independently (lesson 3) | ~$0.30 to regenerate if you catch it early |
| One bad pose-ref (looks fox-eared / blush / wrong color) | ~$0.04 ref + $0.20 video = $0.24 retry |

Total avoidance value: **~$15-20 per first-time pet build**, and many hours.
