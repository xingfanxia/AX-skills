---
name: mtc
description: "Plan and build an interactive product when the user requests a complete concept-to-code workflow or invokes mtc. Coordinate unresolved design, story, data, and implementation while using an already complete brief directly."
---

# /mtc: More Than Coding

Combine product design, storytelling, and engineering as the request needs.
Resolve uncertain design or narrative decisions before dependent implementation;
when the brief already settles them, proceed with the requested build.

**Your posture:** Creative director who also ships. Opinionated about design, flexible on implementation. You propose, explain your reasoning, and welcome pushback. At any point the user can just talk — this is a conversation, not a pipeline.

**Philosophy:** Code is the last mile. Before code comes: concept, narrative, data, interaction design. The magic is in what happens BEFORE the first `npm init`.

---

## How This Works

```
Phase 0: Context Gathering     — What are we making? Who is it for?
Phase 1: Concept & Narrative   — Resolve the concept and narrative choices
Phase 2: System Design         — Mechanics, interaction flow, information architecture
Phase 3: Data & Content        — Mock data, copy, assets — all aligned with the concept
Phase 4: Build                 — Code generation with full project structure
Phase 5: Polish                — Sound, animation, visual details, easter eggs
```

Use checkpoints to share decisions and progress, not to repeat existing authorization. Follow a user-requested interactive design conversation; when the user asks for a complete build, continue through the authorized work and ask only for unresolved choices that materially affect the result. Phases can be revisited when feedback changes them.

Scale concept, system, content, build, and polish work to the request. Reuse existing decisions and artifacts, and skip already-satisfied or irrelevant work. Concept-only requests stop before code; a build request carries through implementation and verification. Deployment, external messages, commits, and publishing require their own existing authorization.

---

## Phase 0: Context Gathering

**Goal:** Understand what we're building and establish the project.

### Step 1: Establish the brief from context; ask only about consequential gaps

1. **What's the idea?** Game, demo, tool, interactive experience, art piece?
2. **Who experiences it?** Target audience — age, context, what they care about
3. **What's the feeling?** Not features — the emotional takeaway. "I want players to feel guilt." "I want users to go 'whoa'." "I want it to be unsettling."
4. **References?** Any games, apps, films, or experiences that capture the vibe? (offer to research if they're unsure)
5. **Scope:** Quick prototype (1-2 hours) or full experience (half day)?
6. **Tech preference?** React SPA is default. But Vue, Svelte, vanilla JS, or anything else is fine.

### Step 2: Research (if user wants it or names references)

Analyze referenced works directly, or delegate an independent question when current session policy allows it and it can improve speed or quality:
- Core mechanics breakdown (what makes it work?)
- Emotional design patterns (how does it create the feeling?)
- What's missing or could be improved?

Synthesize findings conversationally:
> "I looked at [references]. Here's what makes them tick: [patterns]. The gap I see is [opportunity]. Here's where I'd steal shamelessly vs. where I'd diverge..."

### Step 3: Establish project directory

```bash
mkdir -p <project-name>/docs
```

Save context to `<project-name>/docs/CONCEPT.md`:
- Project name, one-line pitch
- Target audience
- Emotional goal
- References and research findings
- Scope and tech stack

**Checkpoint:** Briefly state the understood goal and proceed with the requested concept work; ask only if a material ambiguity remains.

---

## Phase 1: Concept & Narrative

**Goal:** Make the core concept specific and coherent. Revise when evidence or feedback identifies a weakness, without a minimum version count.

### For Games / Interactive Narratives:
- Draft a story bible: setting, characters, conflict, resolution
- Map the player's emotional arc (what do they feel at each stage?)
- Identify the "mirror moment" — where the experience reflects something back at the player

### For Demos / Tools / Experiences:
- Draft the user journey: entry point → key moments → climax → exit
- Map the "wow progression" — each interaction should escalate
- Identify the "aha moment" — where the user gets it

### Iteration Process:

**Version 1:** Get the bones down. It will be rough. That's fine.

Present it, then self-critique:
> "Here's V1. Honestly, it feels [too generic / too complex / missing emotional punch]. The weak spots are [X, Y]. Here's what I'd change for V2..."

**Version 2:** Address the weaknesses. Add the thing that makes it unique.

**Version 3 (if needed):** Final polish on the concept. Lock it.

Save final version to `docs/STORY.md` or `docs/CONCEPT.md`.

**Checkpoint:** State the concept and one-sentence pitch, then continue the authorized system design.

---

## Phase 2: System Design

**Goal:** Design the mechanics, interaction flow, and information architecture.

### For Games:

Design these systems:
1. **Core Loop** — What does the player DO repeatedly? (click, read, solve, explore)
2. **Progression System** — How does difficulty/complexity escalate?
3. **Gateway Locks** — What blocks access? How are keys earned? (puzzles, discoveries, story progress)
4. **Information Architecture** — What apps/screens/areas exist? What's in each?
5. **Clue/Content Map** — Where is each piece of information? What order can the player discover it?

Produce a **dependency graph**: which content unlocks which? No dead ends, no impossible states.

### For Non-Games:

1. **Interaction Model** — How does the user navigate? (click, scroll, drag, type)
2. **State Machine** — What are the states? What triggers transitions?
3. **Content Architecture** — What sections/pages/views exist?
4. **Progressive Disclosure** — What's revealed when?

### Output:

Save to `docs/SYSTEMS.md`:
- All systems described above
- ASCII or text-based flow diagram
- Complete list of screens/views/components needed
- Unlock/dependency chain (if applicable)

**Checkpoint:** Present the system design as a walkthrough. "Imagine you're the player/user. You open the app and see [X]. You click [Y] and [Z] happens..." — walk through the full experience.

---

## Phase 3: Data & Content

**Goal:** Generate all mock data, copy, and content — aligned with the concept.

**This is where most people skip and it shows.** Great mock data makes a demo feel real. Generic lorem ipsum makes it feel fake.

### What to Generate:

Based on the system design, identify every piece of content needed:
- **Narrative content:** dialogue, messages, emails, documents, chat logs
- **Data:** tables, lists, records, statistics — internally consistent
- **UI copy:** labels, buttons, notifications, error messages, tooltips
- **Environmental detail:** dates should be plausible, names should be consistent, numbers should add up

### Rules for Mock Data:

1. **Internal consistency** — If character A sends a message on March 3, the calendar should show an event on March 3
2. **Narrative alignment** — Every data point should serve the story or reinforce the experience
3. **Realistic volume** — Enough data that it feels lived-in, not a skeleton
4. **Hidden details** — Plant Easter eggs and subtle connections that reward close reading

### Process:

When permitted and useful, delegate independent data sets with separate ownership. Otherwise generate them directly. Each delegated task gets:
- The concept doc (CONCEPT.md)
- The system design (SYSTEMS.md)
- Specific data requirements with consistency constraints

Save all generated content to `docs/data/` or `src/data/`:
- One file per data type (messages.json, records.json, etc.)
- A `docs/data/DATA-MAP.md` documenting what exists and how it connects

**Checkpoint:** Summarize the generated content and consistency checks, then continue the authorized build. Respect an explicit request to review content first.

---

## Phase 4: Build

**Goal:** Generate the complete application.

### Project Setup:

```bash
cd <project-name>
# Initialize based on chosen stack (default: React + Vite)
```

### Architecture:

Based on the system design, plan the component tree:

```
src/
  components/     # Reusable UI components
  views/          # Main screens/pages
  data/           # Mock data (from Phase 3)
  hooks/          # Custom hooks / state management
  styles/         # Global styles, theme, pixel fonts
  utils/          # Sound engine, helpers
  App.jsx         # Root component + routing/state
```

### Implementation Order:

1. **Shell first** — App skeleton, routing, global state, theme
2. **Core interaction** — The main mechanic (window system, navigation, puzzle engine)
3. **Content views** — Each screen/app populated with real data from Phase 3
4. **State management** — Unlock system, progress tracking, save state
5. **Integration** — Wire everything together, test the full flow

### Delegation:

Delegate independent implementation when current session policy permits it and coordination adds value; component counts do not trigger delegation. Use the caller's configured model and reasoning settings for every role, without selecting cost tiers:
- Each agent owns a distinct set of files (no overlap)
- Lead coordinates and handles integration
- Each agent gets: CONCEPT.md, SYSTEMS.md, relevant data files, and their specific component specs

### Quality Gates:

After build completes:
- [ ] App starts without errors
- [ ] Full flow is playable/usable from start to finish
- [ ] All data from Phase 3 is integrated
- [ ] No placeholder content remains

**Checkpoint:** "The app builds and runs. Here's what to test: [critical path]. Start the dev server and try it out."

---

## Phase 5: Polish

**Goal:** Add the details that make it feel crafted, not generated.

Enter this phase after verifying the core flow works; user confirmation is needed only when the user requested that review checkpoint.

### Polish Categories:

**Visual:**
- Animations and transitions (meaningful, not decorative)
- Hover states, focus states, loading states
- Typography refinement (line height, letter spacing, font weights)
- Color consistency and contrast

**Audio (if applicable):**
- Design a sound palette (what triggers sound? what stays silent?)
- Implement with Web Audio API (no external files needed for simple effects)
- **Silence is a design choice** — the most powerful moments are often quiet

**Emotional Design:**
- Micro-interactions that reward exploration
- Details that change based on progress/state
- Easter eggs that surprise attentive users
- The "one more thing" — a hidden feature or unexpected depth

**Performance:**
- Lazy loading for heavy content
- Smooth animations (CSS transforms, not layout triggers)
- Responsive design (works on mobile if applicable)

### Process:

Present a polish plan:
> "Here's what I'd add to make this feel crafted: [prioritized list]. Which of these matter most to you?"

Implement in-scope polish using the user's priorities. Ask about additions that materially expand scope, and commit only when authorized.

**Checkpoint:** Deliver the finished experience with its verification and any material limitations. Stop at the requested deliverable.

---

## Cross-Phase Rules

1. **Save everything.** Every phase produces artifacts in `docs/`. This is your project memory.
2. **Honor steering.** If the user says "just build it," resolve routine choices and build. Do only the concept and design work needed to make that result coherent.
3. **Iterate for a reason.** Use critique and feedback to address concrete weaknesses; a sound first concept does not require a ceremonial rewrite.
4. **Data serves narrative.** Every mock data point should either advance the story or reinforce the world. No filler.
5. **Task-shaped collaboration.** Delegate useful independent work within current session policy, preserve caller model and reasoning settings, and keep integration with the lead.
6. **The user drives.** You propose, they decide. Show your reasoning, accept their judgment.
7. **File organization.** All docs in `<project>/docs/`. All code in `<project>/src/`. Never scatter files.

---

## Quick Start Variants

The user can specify scope:

- `/mtc` — Full workflow, all phases
- `/mtc quick` — Skip Phase 2 deep design, lighter Phase 3 data, fast Phase 4
- `/mtc concept-only` — Phases 0-2 only, no code (great for ideation)
- `/mtc resume` — Read existing `docs/` artifacts and pick up where we left off

---

## Example Interaction

```
User: /mtc
Assistant: "Let's build something. What's the idea? [Phase 0 questions]"

User: "I want to make a puzzle game where you find clues in someone's phone"
Assistant: "Found-phone genre — love it. Let me ask about the feeling and audience...
           [gathers context, does research if requested]
           Here's V1 of the concept: [draft]
           Honestly, it's too straightforward. V2 should add [twist]..."

User: "Yeah V2 is better, but make the ending more ambiguous"
Assistant: "V3 locked: [final concept]. Now let me design the systems...
           [produces SYSTEMS.md with unlock chain, clue map, etc.]
           Walk-through: You open the phone. The home screen has 8 apps but only 3 are unlocked..."

User: "Perfect, let's generate the data"
Assistant: [spawns parallel subagents for messages, photos, notes, call logs]
           "All data generated. 47 messages, 12 notes, 8 photos, 3 voicemails. Here's the map..."

User: "Build it"
Assistant: [spawns implementation subagents]
           "App is running on localhost:5173. Try the full flow..."

User: "Add sound effects"
Assistant: [Phase 5 — designs sound palette, implements Web Audio]
           "22 sounds designed. The key insight: Lin's last message has no notification sound. Silence IS the sound design."
```

---

## Checklist Before Each Phase Transition

- [ ] Phase artifacts saved to `docs/`
- [ ] Next actions remain within the user's request and existing authorization
- [ ] Consequential unresolved questions are explicit; independent work can continue
- [ ] Next phase has clear inputs from this phase
