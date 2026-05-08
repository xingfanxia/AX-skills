# neat-freak

> 洁癖 — End-of-session knowledge cleanup with OCD-level rigor. Reconciles project docs (CLAUDE.md / AGENTS.md / README.md / docs/) and agent memory against actual code so nothing rots. Cross-platform: Claude Code, OpenAI Codex, OpenCode, OpenClaw.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The skill solves a problem that's invisible until it bites you: in AI-collaborative dev, the next session of you (or the next agent on the project) reads memory + project docs to bootstrap. If those drifted from the code, every downstream decision is built on a stale prior. neat-freak is a structured editorial pass — not a record-keeper, an *editor* — that closes the gap before it bites.

## When to use

- End of a session where any non-trivial code shipped
- "Sync up" / "tidy up docs" / "clean up docs" / "/sync" / "/neat"
- "整理一下" / "同步一下" / "梳理一下" / "收尾"
- Before handing off to teammates or another agent
- After a milestone where doc / memory drift is likely

The skill is **idempotent** — no-ops cleanly when nothing drifted. Cheap to run, expensive to skip.

## When NOT to use

- Single-character typo fixes — nothing to reconcile
- Throwaway exploratory work the user explicitly framed as such
- Docs-only changes that didn't touch any API / route / env-var / schema / public interface

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/neat-freak ~/.claude/skills/neat-freak
```

## Cross-platform agent paths

The skill ships with [`references/agent-paths.md`](./references/agent-paths.md) — a quick lookup for where each platform stores agent memory and config:

| Platform | Memory | Project config |
|---|---|---|
| Claude Code | `~/.claude/projects/<...>/memory/` | `CLAUDE.md` |
| OpenAI Codex | `AGENTS.md` | `AGENTS.md` |
| OpenCode | `.opencode/` | `AGENTS.md` (reads both) |
| OpenClaw | `~/.openclaw/` | project markdown |

## The three-audience model (the key insight)

Most "doc sync" skills reconcile one surface and call it done. neat-freak reconciles three, because they have **different audiences**:

1. **Agent memory** — for the agent itself across sessions (personal preferences, project facts, cross-project refs)
2. **Project root markdown** (CLAUDE.md / AGENTS.md) — for the AI in *this* project next session
3. **Project docs/** + README — for **other people** (human teammates, downstream devs, the next AI inheriting it)

The first is internal-to-AI. The second is project-AI. The third is *external* — and it's the one that costs the most when it drifts (a downstream team integrating against stale docs is far worse than your own next session forgetting a small fact).

See [SKILL.md](./SKILL.md) for the full 5-step protocol (inventory → identify changes → modify → self-check → summary) and [`references/sync-matrix.md`](./references/sync-matrix.md) for the change-type → docs-to-update mapping.

## Credit / Attribution

This skill originated in **数字生命卡兹克 (Khazix)**'s open-sourced [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) collection (MIT). The 5-step protocol, three-audience model, and cross-platform agent-paths reference are all his work.

This is a **modified version** — packaged into the AX-skills ecosystem with light edits for install paths and cross-references. **Not maintained by the original author** — for the canonical version, follow upstream.
