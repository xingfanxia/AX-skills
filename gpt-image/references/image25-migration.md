# GPT Image 2.5 migration acceptance — 2026-09-11

Default policy: Sunburst for finished artwork, jewelry product images and pet identity references; Flare for explicit previews. The other variant is the HTTP 429 fallback. Quota and user-input errors surface without retry. These matched application trials use the same prompt and parameters within each pair; no artificial rate limits were generated on the live service.

| Application | Operation / quality / size / format | Sunburst seconds (mean; min–max) | Flare seconds (mean; min–max) | Difference / ratio | Success |
|---|---|---|---|---|---|
| ax-blog-dark-illustration | generate / auto (omitted) / 1792x1024 / jpeg | 30.50; 29.06–31.59 | 20.44; 17.99–23.55 | +10.05s / 1.49× | 3/3, 3/3 |
| codex-imagegen-final-poster | generate / medium / auto / png | 24.21; 22.57–25.74 | 15.70; 14.63–16.54 | +8.51s / 1.54× | 3/3, 3/3 |
| gpt-image-final-poster | generate / auto (omitted) / 1024x1536 / jpeg | 21.45; 20.29–22.30 | 15.43; 14.82–15.98 | +6.02s / 1.39× | 3/3, 3/3 |
| jewelry-marketing-medium-edit | edit / medium / 1024x1536 / jpeg | 24.49; 23.85–25.71 | 20.50; 15.82–24.50 | +3.99s / 1.19× | 3/3, 3/3 |
| pet-forge-main-reference | generate / auto (omitted) / 1024x1024 / png | 24.56; 22.85–27.77 | 17.41; 14.80–19.77 | +7.15s / 1.41× | 3/3, 3/3 |

All 30 matched application requests succeeded. No HTTP 429 occurred in these measured samples. The jewelry trials used the actual NewAPI runner payload (`medium`, JPEG compression 85) and public sample product photo; other trials used Azure. Shared CLI and pet intentionally omit quality (`auto`); the Codex adapter retains its previous `medium` default. A preliminary jewelry run omitted quality and is excluded above.

Three samples per model are a small operational comparison, not a stable service-level guarantee. Network, queueing and output complexity affect latency. The Sunburst quality preference comes from the owner’s application priorities, not a statistically established visual-quality ranking. Spot checks found readable poster/blog text and usable pet/product images on both models. Product fidelity and labels still need review per asset.

Validation: actual Azure Sunburst/Flare generation and edit all returned images; NewAPI jewelry edits returned images on both models. Offline tests verify both directions of 429 fallback, intact edit inputs, nonretryable quota/bad-request failures, and Codex mask/image rewind. Shared adapter symlinks resolve correctly. No secrets were found in scoped staged diffs.

The built-in image_gen tool is service-managed; this release updates the maintained CLI fallback and shared skills only. Historical demo videos/cost examples are retained as historical evidence, not relabeled as new-model results.

Detailed matched request parameters and latency samples: [image25-latency.json](image25-latency.json).
