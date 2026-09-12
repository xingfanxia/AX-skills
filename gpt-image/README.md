# gpt-image

Generate and edit images with GPT Image 2.5 through Azure or NewAPI.
Sunburst is the quality default for finished artwork; `--variant flare` favors
fast drafts. A rate limit automatically tries the other variant, including edits.

```bash
./generate.py "editorial product photo" --variant sunburst
./generate.py "quick composition preview" --variant flare
./generate.py "replace the background" --edit product.png
```

For AX's local harnesses, the canonical source is `~/.agents/skills/gpt-image`;
Codex and Claude both link to it. This public directory is its portable release.
Do not replace working shared links when updating the public repository.
Credentials and CLI details: [SKILL.md](SKILL.md).

Adapted from staruhub/ClaudeSkills (MIT).
