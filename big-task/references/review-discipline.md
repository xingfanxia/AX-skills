# Review discipline

Use review to resolve a named correctness, regression, data, or contract risk.
Ordinary bounded implementation does not require an independent reviewer as a
completion ritual.

Ground findings in the relevant diff, source, callers, and behavior. Include
the trigger, impact, location, and evidence. Distinguish supported defects from
preferences and speculative redesigns. Keep review-only work read-only; fix
supported in-scope findings when fixes are requested.

For a consequential risk, an independent reviewer can add confidence by
checking a different failure mode. Give that reviewer a bounded question and
the raw evidence. Do not run duplicate generic passes or impose fixed model
names or reviewer counts.

Verify fixes at the failure boundary and run required project checks. Recheck
the affected contracts when fixes could regress them. Reuse passing evidence
until the relevant changes or unresolved risk justify another check.

If findings recur without new evidence, improve reproduction or revisit the
assumption instead of repeating the same review. Complete authorized work;
raise only the missing consequential decision or authority after preparing a
concrete result and continuing independent tasks.

Report what the evidence supports. A green test is evidence for its assertions,
not proof of every behavior. User silence is not acceptance or approval.
