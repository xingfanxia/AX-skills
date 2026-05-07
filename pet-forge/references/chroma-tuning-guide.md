# Chroma tuning guide — when to use `--sat-min` and `--despill-sat-min`

The vendored `tools/chroma_key.py` ships with two flags not in upstream pet-forge:

| Flag | Default | Set when |
|---|---|---|
| `--sat-min N` | 40 | Pet has green features (eyes, plants, accessories). Use 85 to exclude jade greens from the chroma-removal mask. |
| `--despill-sat-min N` | 0 | Pet has green features. Use 70 to skip despill on mid-saturation greens (jade eyes, sat ~50-65%). |

## Quick decision flow

```
Does the pet have GREEN as a feature color (eyes, leaf accessory, plant prop)?
│
├── NO ──▶ Use defaults. `python3 chroma_key.py input.mp4 output.apng --plays 0`
│
└── YES ─▶ Pass both: `--sat-min 85 --despill-sat-min 70`
```

Blue eyes, amber eyes, gold eyes, brown eyes → defaults are fine.
Jade green, emerald green, olive green, leaf green → tune both.

## Why two flags

The chroma pipeline has 3 mask gates and 1 despill step:

1. **`is_hsv_green`**: catches HSV-green pixels with `sat >= sat_min`
2. **`is_key_color`**: catches RGB-distance-near-key pixels (independent of sat)
3. **`is_semi_green`** (soft edge): catches green-dominant pixels with `sat >= sat_min * 0.5`
4. **Despill**: pulls "too green" surviving pixels toward gray (skipped when `sat < despill_sat_min`)

| Scenario | sat_min effect | despill_sat_min effect |
|---|---|---|
| sat_min=40 (default), iris sat=55 | iris caught by gate 1 → fully removed | despill applied → iris grayed |
| sat_min=85, iris sat=55, despill=0 | iris not caught by gate 1 ✓; **but caught by gate 3** (soft edge) → 30% alpha → translucent gray | despill applied → iris grayed |
| sat_min=85, iris sat=55, despill=70 | iris not caught by gate 1 ✓; gate 3 also gated by sat_min ✓ | despill skipped → iris preserved |

So both flags are needed. `--sat-min` alone leaves a soft-edge translucent halo. `--despill-sat-min` alone doesn't help if the iris is already alpha-zeroed by the HSV mask.

## Bonus: edge halo tradeoff

Tightening the chroma mask (sat_min=85) means anti-alias edges with sat 60-80 may not get fully chroma'd, leaving a faint cyan halo around the silhouette. This is visible at ≥3× zoom but imperceptible at clawd-on-desk's default 200px height render.

If the halo bothers you at desktop size:
- Run `tools/fix_gray_bleed.py` after chroma_key — cleans cool-gray edge bleed.
- Lower `sat_min` to 75 instead of 85 (slightly less protective for iris but tighter edges).

## Verifying the result

After chroma_key:

```bash
ffmpeg -y -i output.apng -vf "select='eq(n\,15)',scale=800:-1" \
  -frames:v 1 -q:v 1 /tmp/check.jpg
open /tmp/check.jpg
```

Check at frame 15 (mid-animation when eyes are typically open). The iris should be the same color as the source mp4. Not gray. Not translucent. Not a hollow socket.

## When the issue is in the SOURCE not chroma

If the source mp4 itself has weird eye colors (gray, missing pupils, asymmetric), the issue is upstream — Doubao misinterpreted the pose-ref. Re-generate the pose-ref with stronger eye-color emphasis in the prompt, then re-Doubao.

Don't try to fix source-quality issues in chroma. That way lies madness.
