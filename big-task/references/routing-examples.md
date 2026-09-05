# Work-shape examples

Use these to calibrate judgment, not as triggers or fixed tiers.

- A README typo can be edited and checked directly even in a complex backend.
- Restyling many existing screens from a locked reference can use bounded
  parallel ownership and targeted rendered checks without redoing product design.
- A small migration needs evidence about existing data and compatibility;
  the small diff does not establish that it is safe to deploy.
- An atomic credit-deduction change needs evidence about retries, transactions,
  and concurrent requests even if it touches one function.
- A new real-time subsystem merits clarifying its contracts and dependencies
  before implementation; optional planning detail should address those unknowns.
- Choosing a state-management library may be routine if the project has already
  chosen a pattern. If it creates an expensive new dependency boundary, compare
  concrete options and resolve the material choice.
- A request to review a plan yields findings. A request to improve it also
  authorizes clear plan edits, without authorizing product implementation.
