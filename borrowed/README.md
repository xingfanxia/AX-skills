# Borrowed skills（借来的）

External skills adopted into AX's working setup **mostly as-is** — vendored snapshots with
light AX adaptation (a rewritten `SKILL.md` entry doc, invocation-tier notes), full upstream
attribution, and the upstream `LICENSE` preserved in each copy.

Distinct from the root-level **"Adapted methods and prompts"** section (`context-infrastructure`,
`trident`, `dr-sharp`): those are AX **rewrites** of an idea; entries here are the upstream
author's **code**, kept close to upstream so `git pull` on the live clone stays cheap.

## Rules

1. **License-gated copying.** Only permissively-licensed upstreams get vendored here (this repo
   is public, MIT). Unlicensed upstreams get a pointer row below — installed privately under
   `~/.claude/skills/`, never republished.
2. **Live copy ≠ this snapshot.** The working install is a git clone in `~/.claude/skills/<name>`
   (upstream remote intact). Snapshots here are refreshed manually, same as the rest of AX-skills.
3. **Attribution stays.** Upstream URL + license noted per entry and inside each `SKILL.md`.
4. These are **ineligible for the "AX-original" showcase sections** — 只蒸原创 still governs the
   rest of the repo; this dir is the explicit exception lane.

## Vendored here

| Skill | Upstream | License | Local invocation tier | What it does |
|---|---|---|---|---|
| [`tavily-skill`](./tavily-skill/) | [grapeot/tavily-skill](https://github.com/grapeot/tavily-skill) | MIT | CLI-for-subagents (`disable-model-invocation`) | Tavily search/extract CLI with file-mode output — ~125-token status lines instead of ~25K-token MCP payloads; the research-session workhorse. |
| [`process-launcher`](./process-launcher/) | [grapeot/process-launcher](https://github.com/grapeot/process-launcher) | MIT | `user-invocable-only` | Localhost process/job service whose core value is macOS TCC bridging — background jobs it spawns inherit mic/camera/screen-recording grants that cron/launchd jobs never get. Durable delayed jobs + YAML always-on services. |
| [`apple-photos`](./apple-photos/) | [grapeot/apple-photos-skill](https://github.com/grapeot/apple-photos-skill) | MIT | `user-invocable-only` | Structured Apple Photos CLI — read-only search/filter/backup via osxphotos is usable today; PhotoKit mutations are upstream-flagged **live-unverified alpha** (never on a production library). The delete-authorization protocol (pixel evidence + frozen manifest + single-use HMAC + human phrase) is a reusable template for any irreversible bulk operation. |
| [`human-writing`](./human-writing/) | [KKKKhazix/human-writing](https://github.com/KKKKhazix/human-writing) | MIT | registered (auto-trigger) | 中文创作与改稿 skill —— 活人感、反机构腔/模型腔，成稿硬约束（禁冒号/破折号/翻案句）。v1.0.0 unpatched. |

## Pointer-only (no license — private install, not redistributable)

| Skill | Upstream | Local invocation tier | What it does |
|---|---|---|---|
| ai-session-export | [grapeot/ai_session_export](https://github.com/grapeot/ai_session_export) | registered (auto-trigger) | Export Claude Code / Codex / OpenCode / Antigravity session transcripts into a unified Markdown archive (`~/.local/share/ai-session-export/`). Matters because `cleanupPeriodDays=90` deletes local transcripts — the archive is the durable copy. |
| imessage | [grapeot/imessage_skill](https://github.com/grapeot/imessage_skill) | `user-invocable-only` | Send-only iMessage CLI via Messages.app (dry-run default, `--confirm-send` gated). |
| App Store Connect CLI runbook | [grapeot/context-infrastructure](https://github.com/grapeot/context-infrastructure) `rules/skills/deployment_app_store_connect_cli.md` | doc, stored beside the Apple signing kit in `~/creds/apple/` | Apple-official-tools-only iOS ship pipeline (xcodebuild archive → export → upload), incl. the cloud-managed-signing pitfalls. |

## Evaluated and declined (2026-08-06 sweep)

A 48-item sweep of the grapeot skill ecosystem produced these 5 adoptions; the other 43 were
declined as duplicates of the existing roster (20), low-value for this profile (14), or
borderline-判负 (9). Decision matrix lives in the `~/.claude` session records; headline reasons:
`semantic-search-skill` / `ai_usage_dashboard` / `presentation_skill` / `image-generation-skill` /
`design_skill` / `writing-skill` / `playwright-test-skill` duplicate existing or deliberately
archived capabilities; `gdocs-skill`'s Docs surface is covered by the generic `gws` API CLI;
`smtp/resend/kit/smart-home/health/eink` presume accounts or hardware AX doesn't run.
