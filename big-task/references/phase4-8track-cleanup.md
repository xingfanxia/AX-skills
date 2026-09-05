# Optional cleanup checks

This legacy filename is retained for existing links. There is no automatic
“Phase 4” or fixed eight-agent sweep. Read this only for requested cleanup.

Consider relevant concerns, not a mandatory track roster:

| Concern | Evidence before changing it |
|---|---|
| Duplicate logic or shared types | Demonstrate harmful drift; preserve distinct contracts. |
| Unused code | Confirm tool findings against dynamic loading, registration, hooks, reflection, configuration, and code generation. |
| Circular dependencies | Establish the concrete initialization or maintenance problem. |
| Broad types | Narrow from actual invariants; retain legitimate unknown values at boundaries. |
| Error handling | Preserve recovery, logging, cleanup, and user-facing boundary handling. |
| Compatibility or fallback paths | Check active users, migrations, configuration, and external consumers. |
| Stubs or generated narration | Distinguish placeholders from intentional seams and explanatory comments. |

Keep changes within the requested cleanup and preserve public behavior unless
a behavior change is authorized. A high-impact discovery needs evidence and
existing authorization assessed, not an automatic rewrite or blanket approval
pause. Resolve uncertain ownership before moving or deleting material.

Run the checks that exercise affected behavior and required project contracts.
Report exact changes, why they are supported, verification, and any remaining
uncertainty. Follow project commit conventions when commits are in scope.
