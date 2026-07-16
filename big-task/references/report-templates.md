# Report templates

(Extracted from SKILL.md. Exact formats for autonomous-mode status lines, the final report, the PR description, and the exit block.)

### Status updates while autonomous

While running autonomously, emit ONE short progress line per phase boundary (≤ 80 chars):

```
▸ Phase 2b · parallel-worktree (4 tasks) · running
✓ Phase 2b · 4/4 green · committed (a1b2c3d) · → Phase 2c
✓ Phase 2c · review clean · → Phase 2g
✓ Phase 2g · 6/6 PASS · → Phase 6a
```

NOT a multi-paragraph essay per phase. The user will read commits + PR description for detail; mid-flight chatter steals their attention without informing them.

### Final report (at PR-opened or PR-merged)

ONE summary block (per existing Exit section, augmented):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 /big-task ▸ COMPLETE  (autonomous run)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phases shipped: N
 Commits: N      LOC: +A / -B
 Tests: unit X / integ Y / e2e Z
 Autonomous decisions made:
   • <decision 1 — what was silently picked and why>
   • <decision 2 — ...>
 Critical-decision pauses: N (none / list)
 Deferred follow-ups (FLAG batch): N (linked from PR)
 PR: <url>
```

The `## Autonomous decisions` log is non-optional — it's the receipt the user needs to audit autonomy after-the-fact.

---

## PR description template

PR description template (enforce):

```markdown
## Summary
- [3-5 bullets: what changed and why]

## Phases shipped
[list from ROADMAP, or single-phase description]

## Tests added
- Unit: N
- Integration (real APIs): N
- E2E: N

## Risks / follow-ups
- [Track 4 deferred items]
- [Any MEDIUM-severity findings not addressed]

## Test plan
- [ ] [specific manual checks]
- [ ] CI green

@claude please review.
```

## Exit block

When PR merges OR user says "done" / "stop":

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 /big-task ▸ COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phases shipped: N
 Commits: N
 Tests added: unit X / integ Y / e2e Z
 LOC: +A / -B
 Tracks cleaned: 8
 Deferred follow-ups: N
 PR: <url>
```

Delete cron monitor. Suggest memory append if cross-project learnings emerged.

---

