# Example: 小肥 (Munchkin)

Real pet: AX's golden tabby British Shorthair Munchkin with jade-green eyes. Short legs, chubby body, distinctive medium-tabby markings.

## Reproducing this pet

```bash
~/.claude/skills/pet-forge/generate.py \
  --description "chubby gold tabby British Shorthair Munchkin with jade-green eyes, short legs, round body" \
  --pet-id munchkin \
  --display-name "小肥"
```

`--green-eye` is auto-detected from "jade-green" in the description. No `--fluffy` (Munchkin is short-coat).

## Files

- `theme.json` — exact theme.json shipping in clawd-on-desk for 小肥. Uses default fileScales (no fluffy bump).
- `animations.json` — pet-forge batch-gen config that produced the 10 mp4s.

## Notable bits

- `eyeTracking.enabled: false` — eye-tracking layers depend on per-element SVG IDs we don't have for AI-generated APNGs.
- `miniMode.supported: false` — no mini-mode APNGs generated.
- `idle/yawning/dozing` all alias to single `idle-dozing.apng`.
- `collapseDuration: 800` and `wakeDuration: 1500` — shorter than Calico's because state APNGs are 4s clips, not multi-segment.
- Required chroma flags: `--sat-min 85 --despill-sat-min 70` — without these, jade-green eyes get gray-hollowed by chroma_key.

## Total spend (this build)

| Stage | Cost | Time |
|---|---|---|
| Initial 7 refs (gpt-image-2) | $0.28 | ~3 min |
| 10 Doubao animations | ~$2.00 | ~6 min |
| Mid-build retries (1 ref + 1 video for ear shape) | $0.24 | ~3 min |
| Chroma re-tuning iterations (local) | $0 | ~5 min iteration time |
| **Total** | **~$2.52** | **~20 min** |

The retries were tuition: ear-shape pose-ref needed regeneration (lesson 1), and chroma flags needed two rounds to fully preserve jade eyes (lesson 5).
