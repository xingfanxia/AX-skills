# Reporting examples

Use the repository's required format when one exists. Otherwise scale reporting
to the actual result; omit empty sections and routine process statistics.

A progress update states the finding, remaining uncertainty, and next useful
action. It does not pause an authorized phase.

A completion report covers:

- The requested behavior or artifact delivered.
- Focused verification and required checks, with relevant evidence.
- Material limitations or unresolved acceptance criteria.
- Links to changed artifacts or the PR when it exists.

For an authorized PR, lead with the concrete problem and resulting behavior.
Describe implementation details only where they help review, then validation
and remaining risk. Do not append bot mentions or review requests unless
explicitly authorized and configured for the repository.

Completion of a local change, opening a PR, passing CI, and merging are distinct
outcomes. Report the one actually reached. User cancellation is not successful
completion. Memory updates and monitor cleanup are not automatic report steps;
clean up task-owned monitors only when their requested monitoring is finished
or cancelled.
