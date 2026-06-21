---
name: serenity-bottleneck-research
description: >
  Use this skill to analyze a secular technology/industry trend, supply chain, company, or public investment thesis using a Serenity-style bottleneck research process. The skill converts a broad narrative into concrete constraints, evidence gates, disconfirmation tests, and next primary-source checks. It must not be used to copy trades, produce buy/sell signals, or treat social-media posts as proof.
---

# Serenity Bottleneck Research Skill

## Purpose

This skill helps an agent perform **research-process distillation**, not **trade copying**.

The core idea is:

> Future alpha can come from translating a large demand wave into the physical, architectural, capacity, qualification, regulatory, data, or distribution constraints that the market has not yet priced correctly.

The output should be a structured research memo containing hypotheses to verify, not investment instructions.

## Non-goals and hard boundaries

Do **not**:

- Say “buy,” “sell,” “hold,” “enter,” “exit,” or give personalized financial advice.
- Copy a public figure’s ticker list or holdings as recommendations.
- Treat X posts, screenshots, newsletters, Discord/Telegram/WeChat chatter, or price action as proof.
- Assume that a company is attractive merely because it is small, obscure, upstream, or thematically related.
- Ignore liquidity, dilution, balance sheet, governance, customer concentration, or reflexivity risk.
- Collapse “research alpha” and “distribution alpha” into one thing.

Always distinguish:

- **Research alpha**: insight from understanding the system earlier or more deeply than the market.
- **Distribution alpha**: price impact from a person’s audience, reputation, media amplification, and follower capital.
- **Crowded attention trade**: a thesis whose price, liquidity, and risk changed materially after public diffusion.

## Default assumptions

If the user does not specify otherwise, assume:

- Horizon: 12–36 months.
- Goal: identify researchable bottleneck theses, not near-term trades.
- Output: ranked hypotheses with evidence quality, disconfirmation, and next checks.
- Geographies: global public equities and private supply-chain companies where relevant.
- Source standard: primary sources first; social sources only as leads.

## Required output structure

Every response using this skill should include these sections.

### 1. Framing

State the input and convert it into a precise research question.

Examples:

- Bad: “AI data centers will grow; find winners.”
- Better: “If AI cluster scale-out bandwidth rises faster than electrical interconnects can handle, which optical interconnect layers become capacity- or qualification-constrained?”

Include:

- Demand wave.
- Time horizon.
- End-market driver.
- System-level pressure.
- What would need to change for the thesis to matter.

### 2. Demand wave → architecture shift

Do not start from a ticker. Start from the system.

Answer:

1. What demand wave is forcing the system to change?
2. Which old architecture starts to fail?
3. What new architecture, process, material, or business model becomes necessary?
4. Is the shift already happening, merely forecasted, or still speculative?
5. What clock is driving urgency: capex cycle, product cycle, regulation, customer qualification, standardization, or physical capacity?

### 3. Value-chain map

Map the chain from downstream demand to upstream constraints.

Use this generic chain and adapt it:

```text
End demand
→ System architecture
→ Subsystems
→ Components
→ Materials / process equipment / IP / data / distribution
→ Capacity / qualification / standards / regulation
→ Companies with economic control
→ Financial statements
→ Market pricing
```

For each layer, identify:

- Key suppliers.
- Customer dependency.
- Substitutes.
- Switching time.
- Expansion lead time.
- Pricing power.
- Evidence available.

### 4. Beneficiary vs bottleneck vs chokepoint

Classify each candidate company or layer into exactly one primary category.

#### Beneficiary

The company benefits from the theme, but the system can route around it.

Signals:

- Many suppliers.
- Low switching cost.
- Commodity pricing.
- No unique qualification.
- Capacity can expand quickly.

Valuation implication: usually should not receive chokepoint multiples.

#### Bottleneck

The layer constrains throughput, capacity, yield, or deployment speed.

Signals:

- Long capacity expansion lead time.
- Scarce material, equipment, talent, process recipe, yield learning, or certification.
- Customer demand waits on this layer.
- Adjacent companies mention this constraint independently.

Valuation implication: may deserve scarcity economics if the company can capture the value.

#### Chokepoint

The architecture is practically dependent on this path in the relevant time window.

Signals:

- Few credible substitutes.
- Reference designs or customer roadmaps are locked in.
- Qualification cycles make switching slow.
- Standards, ecosystem dependencies, or customer integration create path dependence.
- Even if alternatives exist, they cannot arrive before the demand wave matters.

Valuation implication: strongest thesis type, but requires strongest evidence.

### 5. Evidence ladder

Label every evidence item by strength. Never mix levels without labeling them.

#### Level 0 — Noise / lead only

Use only to generate questions.

- Social posts.
- Screenshots of returns.
- Anonymous rumors.
- Follower count.
- Post-driven price action.
- Mirror sites and summaries of social posts.

#### Level 1 — Weak signal

Useful, but not proof.

- Company blog posts.
- Marketing pages.
- Generic investor-deck language.
- Conference hype.
- Unnamed customer references.
- Job postings without clear commercial linkage.

#### Level 2 — Medium signal

Can support a thesis if corroborated.

- Customer or supplier pages naming the company.
- Industry roadmaps.
- Standards-body activity.
- Trade publications with named sources.
- Government grant notices.
- Adjacent-company earnings-call comments.
- Patent clusters or technical papers tied to the company’s capability.

#### Level 3 — Strong signal

Can materially support a thesis.

- SEC filings, annual reports, 10-K/20-F/F-1/S-1, exchange announcements.
- Named contracts or purchase agreements.
- Explicit customer qualification or design-win disclosures with timing.
- Capacity expansion with concrete capex, throughput, or production dates.
- Financial statements showing revenue, margin, backlog, deferred revenue, cash flow, or segment inflection.

#### Level 4 — Confirmed economic capture

Strongest level.

- Multiple quarters of revenue conversion from the target segment.
- Gross margin expansion tied to the constrained layer.
- Backlog or long-term agreements converting to cash.
- Customers confirming dependency and economics.
- Competitors failing to route around the constraint.

### 6. Company control and economic capture

After finding a constraint, ask whether the specific company can capture economics.

Answer:

1. Does the company own the constrained asset, or merely participate near it?
2. Is the scarce thing a product, process, capacity slot, certification, IP, data asset, customer relationship, or regulatory license?
3. Can customers dual-source or vertically integrate?
4. Can competitors expand supply before the company captures economics?
5. Does pricing power show up in gross margin, backlog, prepayments, or contract terms?
6. Does the company need dilutive financing before the thesis works?
7. Are insiders aligned, conflicted, promotional, or distressed?

### 7. Market-pricing gap

A thesis is not complete until it explains why the market has not priced it.

Classify the gap:

- **Coverage gap**: too small or obscure for institutions.
- **Accounting lag**: new segment hidden inside legacy revenue.
- **Qualification lag**: design wins precede revenue by many quarters.
- **Architecture misunderstanding**: market tracks demand but misses the layer where value accrues.
- **Legacy stigma**: company is valued on an old failed business.
- **Liquidity discount**: market is right to demand a discount because trading capacity is low.
- **Balance-sheet discount**: market is right to discount due to dilution or insolvency risk.

Then state why the gap should close and what catalyst could close it.

### 8. Reflexivity and attention-risk filter

Before writing any thesis, evaluate whether the opportunity is still a research alpha or has become an attention trade.

Ask:

1. Did the stock move materially after a public post, newsletter, article, or influencer mention?
2. Did volume, option activity, social mentions, or short interest change abnormally?
3. Is the float small enough that follower capital can dominate price discovery?
4. Has the thesis become widely summarized in second-hand posts?
5. Is the current buyer getting the same information state as the original researcher, or a post-diffusion state?
6. Would the thesis still be attractive if the public figure stopped posting about it?
7. Is the expected return coming from fundamental repricing or from finding a later buyer?

Output one of:

- **Pre-diffusion research lead**: little public attention; needs diligence.
- **Diffusion-stage thesis**: market is learning; valuation and volume must be stress-tested.
- **Crowded attention trade**: research may be interesting, but price/liquidity/risk already changed.
- **Post-squeeze danger zone**: do not confuse historical move with current edge.

### 9. Disconfirmation-first thesis writing

Every thesis must include kill criteria.

Use this format:

```text
Thesis:
The system-level change is ___, which should make ___ scarce. Company ___ may control ___, and the market may still value it as ___ rather than ___ .

This thesis is wrong fastest if:
1. ___
2. ___
3. ___

Evidence required next:
1. ___
2. ___
3. ___
```

Common disconfirmations:

- Customers adopt a substitute.
- Capacity expands faster than expected.
- The constrained layer captures no margin.
- The company has no real control over the scarce asset.
- Design win never converts into revenue.
- Revenue comes with poor gross margin or cash burn.
- Dilution absorbs upside.
- Customer concentration creates bargaining-power asymmetry.
- Management is promotional without primary-source support.
- The thesis is already fully priced or crowded.

### 10. Ranking hypotheses

Rank candidates by research quality, not expected stock return.

Use this scoring table:

| Dimension | Score 0 | Score 1 | Score 2 | Score 3 |
|---|---:|---:|---:|---:|
| Demand urgency | No clear demand | Long-term narrative | Near-term driver | Customer/capex clock is visible |
| Architecture shift | No change | Speculative | Plausible | Already visible in roadmaps/orders |
| Constraint severity | Generic benefit | Some scarcity | Hard capacity/qualification limit | System cannot route around it in time |
| Company control | Unclear | Indirect exposure | Direct exposure | Owns/controls critical scarce asset |
| Economic capture | None | Possible | Some evidence | Visible in financials/contracts |
| Evidence quality | Social only | Weak | Medium | Strong/primary |
| Market-pricing gap | None | Story known | Partially misunderstood | Clear old-business/coverage/accounting gap |
| Reflexivity risk | Extreme | High | Medium | Low |
| Balance-sheet risk | Fatal | High | Manageable | Strong |
| Disconfirmation clarity | No kill criteria | Vague | Testable | Immediate primary-source checks |

Then classify:

- **A: Research candidate** — strong enough for deeper primary-source diligence.
- **B: Watchlist candidate** — interesting but missing evidence.
- **C: Story stock** — narrative ahead of evidence.
- **D: Attention trade / avoid as research alpha** — thesis may be real, but current price/action is dominated by crowding.

### 11. Required final memo format

Use this structure:

```markdown
# Bottleneck Research Memo: [Theme / Company]

## 1. One-sentence answer
[Direct conclusion. No buy/sell language.]

## 2. Demand wave and architecture shift
- Demand wave:
- Old architecture limit:
- New architecture/process:
- Time pressure:

## 3. Value-chain map
[Layered chain from downstream demand to upstream constraint.]

## 4. Candidate bottlenecks / chokepoints
| Layer | Candidate constraint | Beneficiary / bottleneck / chokepoint | Why it may matter | Evidence level |

## 5. Company control and economic capture
| Company / asset | What it controls | Evidence | Economic capture risk | Balance-sheet/governance risk |

## 6. Market-pricing gap
[Why the market may not have priced it; why that gap may or may not close.]

## 7. Reflexivity and attention-risk check
[Pre-diffusion / diffusion-stage / crowded attention trade / post-squeeze danger zone.]

## 8. Disconfirmation
- Fastest way the thesis is wrong:
- Evidence that would downgrade it:
- Evidence that would upgrade it:

## 9. Next primary-source checks
1. [Filing / transcript / contract / customer source]
2. [Technical source / standard / roadmap]
3. [Financial statement / segment data]

## 10. Research classification
[A/B/C/D with explanation.]
```

## Source-handling protocol

When the task requires current information, use current sources. Prefer:

1. Company filings and regulatory announcements.
2. Earnings-call transcripts and investor presentations.
3. Named customer/supplier announcements.
4. Standards bodies, technical roadmaps, patents, and peer-reviewed or reputable technical material.
5. Trade publications with named sources.
6. Social posts only as leads.

Always cite sources when making factual claims.

When sources conflict:

- Prefer primary sources over summaries.
- Separate facts from interpretation.
- Mark uncertain claims as uncertain.
- List what source would resolve the uncertainty.

## Anti-hallucination rules

Before finalizing, check:

- Did I start from the system rather than the ticker?
- Did I identify a real constraint, or only a thematic beneficiary?
- Did I show why the system cannot route around the constraint?
- Did I prove company control, not just company proximity?
- Did I separate evidence levels?
- Did I write disconfirmation before enthusiasm?
- Did I test whether the thesis is already crowded?
- Did I avoid buy/sell language?
- Did I provide next primary-source checks?

## Example user prompts this skill handles

- “Analyze whether CPO creates a bottleneck thesis.”
- “Map the AI optical interconnect supply chain and find under-researched constraints.”
- “Is this small-cap stock a real chokepoint or just a beneficiary?”
- “Distill this X thread into research questions and verification steps.”
- “Compare three companies in a supply chain and rank evidence quality.”
- “Find the kill criteria for this AI infrastructure thesis.”
