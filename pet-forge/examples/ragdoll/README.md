# Example: 胖猫 (Ragdoll)

Real pet: AX's seal-point bicolor Ragdoll with sky-blue eyes. Fluffy long coat, distinctive white inverted-V blaze on forehead, plumed tail (signature Ragdoll trait — visibly larger and fluffier than typical cartoon cat).

## Reproducing this pet

```bash
~/.claude/skills/pet-forge/generate.py \
  --description "seal point bicolor Ragdoll cat with sky-blue eyes, fluffy long coat with white inverted-V blaze on forehead, plumed fluffy tail" \
  --pet-id ragdoll \
  --display-name "胖猫"
```

Auto-detected: `--fluffy` (description contains "Ragdoll" and "long coat") → fileScales auto-bumped +0.05.
NOT auto-detected: `--green-eye` is False (sky-blue eyes — chroma defaults are fine).

## Files

- `theme.json` — fileScales bumped 0.05 over Munchkin's defaults to compensate for fluffy silhouette taking more visual space.
- `animations.json` — pet-forge batch-gen config.

## Notable bits

| Field | Munchkin | Ragdoll | Why |
|---|---|---|---|
| `idle-dozing.apng` fileScale | 1.05 | 1.10 | +0.05 fluff bump |
| `thinking.apng` fileScale | 1.20 | 1.25 | +0.05 |
| `working-typing.apng` fileScale | 1.20 | 1.25 | +0.05 |
| `notification.apng` fileScale | 1.02 | 1.07 | +0.05 |
| `error.apng` fileScale | 1.25 | 1.30 | +0.05 |
| `happy.apng` fileScale | 1.20 | 1.25 | +0.05 |

`generate.py` does the +0.05 bump automatically when `--fluffy` is on (or auto-detected from breed keywords).

## Production notes

- The white inverted-V blaze on the forehead is the **highest-risk feature** — gpt-image-2 sometimes drifts it across pose-refs. Add explicit position language to CHARACTER_PREFIX: "WHITE INVERTED-V BLAZE running down the center of the forehead between the eyes to the pink nose. The blaze position must be identical in every frame."
- Plumed tail: emphasize "noticeably bigger and fluffier than a typical cartoon cat" — without this, gpt-image-2 produces a plain tabby tail.
- Standard chroma defaults work — sky-blue eyes are far outside the green hue range.

## Total spend (this build)

| Stage | Cost | Time |
|---|---|---|
| Initial 7 refs | $0.28 | ~3 min |
| 10 Doubao animations | ~$2.00 | ~6 min |
| Mid-build retries (notification ear shape, thinking ear shape) | $0.48 | ~5 min |
| **Total** | **~$2.76** | **~14 min** |
