# Agentic Frontend and Full-Stack Repository Guideline

## Scope

This guideline is for large frontend and full-stack repositories maintained by AI coding agents such as Codex, Claude Code, Cursor, GitHub Copilot coding agent, Devin, Windsurf/Cascade, and Sourcegraph Amp. It focuses on repository architecture that helps agents locate responsibility, modify code safely, verify changes deterministically, and avoid entropy such as thousand-line page files, implicit contracts, global CSS pollution, and mixed UI/business logic.

This is not a generic clean-code or SOLID summary. Every rule below is intended to make agent behavior more reliable.

---

## 1. Executive Summary

1. Treat repository structure as an agent navigation API. A path should tell the agent ownership, boundary, allowed imports, and likely tests.
2. Keep `src/app/**/page.tsx`, `layout.tsx`, and `route.ts` thin. Route files compose feature entries; they do not own business rules, storage, browser APIs, or complex UI.
3. Use feature ownership as the main unit of safe change. A feature should contain its own `contracts`, `data`, `engine`, `state`, `ui`, `screens`, and `tests`.
4. Contractize every cross-boundary value: routes, API payloads, storage keys, assets, events, design tokens, DOM test IDs, domain entities, and UI state.
5. Use runtime schemas for external, persisted, or untrusted data. TypeScript types alone are erased at runtime and do not validate JSON, route params, storage, or messages.
6. Put business rules in pure `engine/` modules. A pure engine must not import React, Next.js, DOM, browser APIs, store, network clients, or storage adapters.
7. Put browser APIs and external data behind adapters. `window`, `document`, `localStorage`, `postMessage`, `fetch`, SDKs, and storage belong behind explicit contracts.
8. Separate state orchestration from rendering. `state/` owns reducers, state machines, selectors, and orchestration hooks; `ui/` renders; `screens/` wires data, state, and UI.
9. Use minimal client boundaries in React Server Components. Add `'use client'` only to the smallest interactive entry point and pass serializable props across the server-client boundary.
10. Do not let CSS classes become hidden APIs. Global CSS is limited to reset, fonts, and tokens; tests and visual regression use typed `data-testid` contracts.
11. Enforce file-size limits. Default thresholds: route file <= 80 LOC, component file <= 200 LOC, general source <= 300 LOC, hard cap <= 500 LOC unless allowlisted.
12. Make architecture rules executable. Use lint rules, dependency boundary checks, no-giant-file checks, no-browser-API-in-engine checks, and CI gates.
13. Make verification a single command. `pnpm verify` or equivalent should run typecheck, lint, unit tests, contract tests, Playwright, screenshots, and architecture checks.
14. Separate implementation and verification contexts. The agent that writes code should not be the only judge of completion; use CI, verifier subagents, review bots, or clean-context checks.
15. For long-running refactors, maintain a progress and evidence ledger. Use `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, and `.agent/DECISIONS.md` so future agent turns can resume accurately.

---

## 2. Source Matrix

| Source name | Organization | URL | Source type | Relevance | Confidence |
|---|---|---|---|---|---|
| Codex AGENTS.md guidance | OpenAI | https://developers.openai.com/codex/guides/agents-md | official | Agent instruction hierarchy, nested overrides, context size limits | High |
| Codex prompting | OpenAI | https://developers.openai.com/codex/prompting | official | Smaller tasks, validation steps, local/cloud coding workflows | High |
| Codex iterative repair loops | OpenAI | https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex | official | Review, repair, and validate loops | High |
| Codex goals | OpenAI | https://developers.openai.com/codex/use-cases/follow-goals | official | Long-running objective and stop-condition workflow | High |
| Codex ExecPlans | OpenAI | https://developers.openai.com/cookbook/articles/codex_exec_plans | official | Structured execution plans and progress tracking | High |
| Codex Skills | OpenAI | https://developers.openai.com/codex/skills | official | Progressive disclosure for reusable workflows | High |
| Claude Code memory | Anthropic | https://docs.anthropic.com/en/docs/claude-code/memory | official | CLAUDE.md scope, concise persistent instructions, enforcement caveat | High |
| Claude Code hooks | Anthropic | https://docs.anthropic.com/en/docs/claude-code/hooks-guide | official | Deterministic enforcement around tool use | High |
| Claude Code Skills | Anthropic | https://docs.anthropic.com/en/docs/claude-code/skills | official | Move procedures out of always-on context | High |
| Context engineering for agents | Anthropic | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | official | Context pollution, progressive disclosure, file hierarchy as signal | High |
| Long-running agent harnesses | Anthropic | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | official | Progress files, feature lists, browser-based acceptance | High |
| Harness design for long-running apps | Anthropic | https://www.anthropic.com/engineering/harness-design-long-running-apps | official | Planner/generator/evaluator separation | High |
| Cursor Rules | Cursor | https://cursor.com/docs/rules | official | `.cursor/rules`, scoped rules, concrete examples | High |
| Cursor Subagents | Cursor | https://cursor.com/docs/subagents | official | Verifier subagent, isolated context, parallel work | High |
| Cursor Bugbot | Cursor | https://cursor.com/docs/bugbot | official | PR review and bug/security/code-quality flow | High |
| GitHub Copilot coding agent | GitHub | https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent | official | Autonomous branch-based coding environment | High |
| Next.js Server and Client Components | Vercel | https://nextjs.org/docs/app/getting-started/server-and-client-components | official | Server/client component split and browser API boundary | High |
| Next.js `use client` | Vercel | https://nextjs.org/docs/app/api-reference/directives/use-client | official | Client boundary and serializable props | High |
| React `use client` | React | https://react.dev/reference/rsc/use-client | official | Transitive client module subtree semantics | High |
| TypeScript basic types | Microsoft | https://www.typescriptlang.org/docs/handbook/2/basic-types.html | official | Type erasure and runtime validation limitation | High |
| Zod | Zod project | https://zod.dev | official | TypeScript-first runtime schema validation | High |
| Playwright visual comparisons | Microsoft | https://playwright.dev/docs/test-snapshots | official | Screenshot regression and environment caveats | High |
| ESLint no-restricted-imports | ESLint | https://eslint.org/docs/latest/rules/no-restricted-imports | official | Enforce dependency and environment boundaries | High |
| dependency-cruiser | OSS | https://github.com/sverweij/dependency-cruiser | secondary | Dependency graph boundary checks for JS/TS | Medium |

---

## 3. Agentic Architecture Principles

### Principle 1: Repository structure is an agent navigation API

Why it matters for agents: Agents use file paths, names, directory hierarchy, local instructions, and nearby tests to infer responsibility. Vague folders such as `components`, `utils`, and `hooks` create low-signal search space and increase accidental edits.

Concrete rule:

- Use `src/app`, `src/features/<feature>`, `src/shared`, `src/server`, `tests`, `scripts`, and `.agent` as stable top-level landmarks.
- Every feature has a consistent internal shape: `contracts`, `data`, `engine`, `state`, `ui`, `screens`, `tests`.
- A path must imply allowed imports and verification scope.

Anti-pattern:

- `src/components/Dashboard.tsx` contains API calls, localStorage reads, pricing rules, chart rendering, user permissions, and CSS class contracts.

Example boundary:

```text
src/features/billing/engine/calculateInvoice.ts
```

This path tells the agent: billing-owned pure domain logic, likely unit-tested, no React or browser imports.

Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Principle 2: Route files are composition only

Why it matters for agents: Agents often start from `page.tsx` or `route.ts`. If route files contain business rules, storage, network, and UI, every change becomes high blast-radius.

Concrete rule:

- `page.tsx` reads route params/search params, validates them, and renders one feature screen.
- `route.ts` validates request input and delegates to one feature/server handler.
- Route files stay under LOC thresholds and do not contain business logic.

Anti-pattern:

- A 2,000-line `src/app/dashboard/page.tsx` that fetches data, formats domain values, writes localStorage, renders charts, and implements permissions.

Example boundary:

```text
src/app/projects/[projectId]/page.tsx
  -> src/features/projects/screens/ProjectScreen.tsx
  -> src/features/projects/application or data/state/ui/engine
```

Sources:

- https://nextjs.org/docs/app/getting-started/server-and-client-components
- https://developers.openai.com/codex/prompting

### Principle 3: Feature is the ownership unit

Why it matters for agents: Agents need a small, local, reversible workspace. Feature-level ownership lets an agent modify `features/checkout` without scanning every shared utility and route.

Concrete rule:

- Feature-private implementation stays inside `src/features/<feature>`.
- Other features import only the feature public API: `src/features/<feature>/index.ts` or `public.ts`.
- Deep imports into another feature's `ui`, `engine`, `state`, or `data` are forbidden.

Anti-pattern:

```ts
import { CheckoutTotalsInternal } from '@/features/checkout/ui/CheckoutTotalsInternal';
```

Preferred:

```ts
import { CheckoutSummary } from '@/features/checkout';
```

Source: https://cursor.com/docs/rules

### Principle 4: Pure engine owns business truth

Why it matters for agents: Pure functions are easiest for agents to test, refactor, reason about, and repair iteratively. UI code is high-noise context.

Concrete rule:

- Any rule affecting money, permissions, eligibility, ordering, quotas, validation, routing, state transition, persisted data, or external side effects goes in `engine/` first.
- `engine/` must not import React, Next, DOM, storage, store, network, or server modules.

Anti-pattern:

```tsx
<button disabled={user.role !== 'admin' || invoice.status === 'paid'}>
  Refund
</button>
```

Preferred:

```ts
// engine/canRefundInvoice.ts
export function canRefundInvoice(input: CanRefundInvoiceInput): boolean {
  return input.userRole === 'admin' && input.invoiceStatus === 'paid';
}
```

Source: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex

### Principle 5: Contracts are first-class modules

Why it matters for agents: Agents hallucinate or duplicate hidden string contracts. Making boundary values explicit reduces guesswork and enables mechanical validation.

Concrete rule:

- Route paths, search params, API DTOs, storage keys, event names, asset IDs, design tokens, DOM test IDs, and domain IDs live in `contracts/` or `shared/*` contract files.
- All boundary strings are imported from contract files.

Anti-pattern:

```ts
localStorage.setItem('dismissed-onboarding', 'true');
router.push('/projects/' + id);
page.locator('.project-card.primary');
```

Preferred:

```ts
onboardingStorage.set({ dismissed: true });
router.push(routes.project(projectId));
page.getByTestId(projectTestIds.card);
```

Sources:

- https://www.typescriptlang.org/docs/handbook/2/basic-types.html
- https://zod.dev

### Principle 6: Adapters isolate side effects

Why it matters for agents: Side effects create environmental dependencies and hidden contracts. Adapters give agents a safe place to mock, test, and replace external interactions.

Concrete rule:

- Browser APIs, storage, fetch, analytics, feature flags, SDKs, and postMessage live behind adapters.
- Components and engines consume typed functions, not raw APIs.

Anti-pattern:

```tsx
useEffect(() => {
  localStorage.setItem('cart', JSON.stringify(cart));
}, [cart]);
```

Preferred:

```ts
// features/cart/data/cartStorage.ts
export const cartStorage = createJsonStorage({ key, schema, defaultValue });
```

Source: https://nextjs.org/docs/app/getting-started/server-and-client-components

### Principle 7: Verification is a repo API

Why it matters for agents: Agents perform better when the repository provides deterministic validation commands and precise failure signals.

Concrete rule:

- Provide one command: `pnpm verify`.
- It must run typecheck, lint, tests, contract checks, Playwright, screenshot checks, architecture checks, and size checks.
- CI must run the same command or equivalent subsets.

Anti-pattern:

- README says "run tests" but there are six inconsistent commands and no architecture enforcement.

Source: https://developers.openai.com/codex/prompting

### Principle 8: Generation context and verification context are separate

Why it matters for agents: The same agent that implemented a change may over-trust its own assumptions. A clean verifier context catches missed files, failing tests, and incomplete behavior.

Concrete rule:

- Use CI, a verifier subagent, Bugbot, or a clean worktree to validate.
- For risky changes, update `.agent/EVIDENCE.md` with exact commands and outcomes.

Anti-pattern:

- Agent reads its diff, says "looks good", and marks done without running tests.

Sources:

- https://cursor.com/docs/subagents
- https://cursor.com/docs/bugbot

---

## 4. Contract Design Guidelines

### 4.1 What must be contractized

| Contract | Location | Must contain | Runtime validation | Agent rule |
|---|---|---|---|---|
| Route paths | `src/shared/routes/routes.ts` or `features/<feature>/contracts/routes.ts` | Route builders, params, search schemas | Yes for params/search | Never hardcode route strings outside contract files. |
| API request/response | `features/<feature>/contracts/api.ts` | Request schema, response schema, error schema | Yes | Never cast `await res.json()` directly to a type. |
| Storage/localStorage | `shared/storage` or `features/<feature>/data/storage.ts` | Key, version, schema, migration/default | Yes | UI must not call raw storage APIs. |
| Asset paths | `shared/assets/manifest.ts` | Typed asset IDs and mappings | Build/test check | Do not hardcode asset paths in components. |
| Domain entities | `features/<feature>/engine/types.ts` or `contracts/domain.ts` | Branded IDs, invariants, enums | Sometimes | External data is parsed before becoming a domain type. |
| UI state | `features/<feature>/state/types.ts` | State union, action union, selectors | Type-level plus tests | Avoid anonymous shared state objects. |
| Events/postMessage | `shared/events` or `features/<feature>/contracts/events.ts` | Event type union, origin policy, payload schema | Yes | No inline event name comparisons. |
| Design tokens | `shared/design/tokens.ts`, `tokens.css` | Token names, CSS variables, mapping | Build/lint check | No raw hex/px except allowlist. |
| DOM selectors | `features/<feature>/contracts/testIds.ts` | Stable `data-testid` constants | Test check | Tests and screenshots do not use CSS classes. |

### 4.2 Runtime validation decision rule

Use TypeScript types only for data created inside trusted code. Use runtime schemas for all external, persisted, or untrusted data:

- HTTP JSON
- route params and search params
- localStorage/sessionStorage/IndexedDB
- postMessage
- external API response
- CMS payloads
- config/env
- file uploads
- persisted feature state

TypeScript annotations are erased at runtime, so a type annotation cannot validate untrusted JSON. Use a schema library such as Zod, JSON Schema, Valibot, or generated validators.

```ts
// src/features/billing/contracts/api.ts
import { z } from 'zod';

export const InvoiceIdSchema = z.string().uuid().brand<'InvoiceId'>();
export type InvoiceId = z.infer<typeof InvoiceIdSchema>;

export const CreateInvoiceRequestSchema = z.object({
  customerId: z.string().uuid(),
  lineItems: z.array(z.object({
    sku: z.string().min(1),
    quantity: z.number().int().positive(),
  })),
});

export const CreateInvoiceResponseSchema = z.object({
  invoiceId: InvoiceIdSchema,
  status: z.enum(['draft', 'issued']),
});

export type CreateInvoiceRequest = z.infer<typeof CreateInvoiceRequestSchema>;
export type CreateInvoiceResponse = z.infer<typeof CreateInvoiceResponseSchema>;
```

```ts
// src/shared/routes/routes.ts
import { z } from 'zod';

export const ProjectRouteParamsSchema = z.object({
  projectId: z.string().uuid().brand<'ProjectId'>(),
});

export type ProjectId = z.infer<typeof ProjectRouteParamsSchema>['projectId'];

export const routes = {
  home: () => '/' as const,
  project: (projectId: ProjectId) =>
    `/projects/${encodeURIComponent(projectId)}` as const,
  projectSettings: (projectId: ProjectId) =>
    `/projects/${encodeURIComponent(projectId)}/settings` as const,
} as const;
```

```ts
// src/features/onboarding/data/onboardingStorage.ts
import { z } from 'zod';
import { createJsonStorage } from '@/shared/storage/createJsonStorage';

const OnboardingStorageSchema = z.object({
  version: z.literal(1),
  dismissedAt: z.string().datetime().nullable(),
  completedSteps: z.array(z.enum(['profile', 'billing', 'invite'])),
});

export const onboardingStorage = createJsonStorage({
  key: 'app:onboarding:v1',
  schema: OnboardingStorageSchema,
  defaultValue: { version: 1, dismissedAt: null, completedSteps: [] },
});
```

```ts
// src/features/dashboard/contracts/testIds.ts
export const dashboardTestIds = {
  shell: 'dashboard-shell',
  revenueChart: 'dashboard-revenue-chart',
  loadingState: 'dashboard-loading-state',
  errorState: 'dashboard-error-state',
} as const;

export type DashboardTestId =
  (typeof dashboardTestIds)[keyof typeof dashboardTestIds];
```

### 4.3 Contract rules for agents

- If a boundary contract exists, import it.
- If no boundary contract exists, create one before using the boundary.
- Do not change a contract without updating tests, fixtures, generated artifacts, and all call sites.
- Persisted contracts must be versioned.
- Schema parsing must happen at the boundary.
- Internal code uses parsed domain types, not raw DTOs.
- CSS class names are styling implementation details, not test APIs.

---

## 5. File and Module Decomposition Rules

### 5.1 Hard thresholds

| Target | Limit | Required action |
|---|---:|---|
| `src/app/**/page.tsx` | 80 LOC | Move UI to feature screen; move logic to feature modules. |
| `src/app/**/layout.tsx` | 100 LOC | Extract providers, shell, nav, or layout pieces. |
| `src/app/**/route.ts` | 100 LOC | Keep HTTP method wrapper; move handler to feature server module. |
| React component file | 200 LOC | Split into presentational subcomponents, state hook, or screen wrapper. |
| Any source file | 300 LOC | Split by responsibility. |
| Any non-generated source file | 500 LOC | Hard fail unless allowlisted with owner, reason, and expiry. |
| Function | 60 LOC or 5+ branches | Extract pure helpers or state machine. |
| Component props | 12+ props | Introduce view model object or split component. |
| Duplicated contract string | 2 occurrences | Create/import a contract constant. |

### 5.2 Refactor triggers

- A route file imports `localStorage`, `window`, `document`, or feature internals.
- A component contains a business rule affecting money, permissions, eligibility, ordering, state transitions, or persisted data.
- A component fetches data, owns state orchestration, contains business rules, and renders complex JSX.
- `useEffect` computes domain state from raw API response.
- A UI file calls browser storage or postMessage directly.
- A feature imports another feature's private internals.
- A shared utility has one consumer and feature-specific behavior.
- A CSS class is used as a test selector.
- A route, storage key, event name, or asset path is duplicated as a string literal.
- A new `any` lacks a boundary comment.
- `@ts-nocheck` is added.

### 5.3 Required splits

When a route file must split:

- It exceeds 80 LOC.
- It imports more than one feature.
- It contains JSX beyond a screen and simple layout wrapper.
- It directly calls business functions.
- It reads/writes storage or browser APIs.
- It has more than one data fetch or mutation.

When a component must split:

- It owns fetch, reducer/state machine, business rules, and JSX.
- It has 3+ conditional render states.
- It contains calculations that can be tested without React.
- It has 12+ props or multiple unrelated sections.
- It is over 200 LOC.

When pure domain logic must be extracted:

- The rule affects business correctness.
- The same condition appears in UI and API/server code.
- A unit test can validate it without rendering.
- The logic contains branching, sorting, pricing, permissions, quotas, or validation.

When an adapter must be created:

- Code touches browser APIs, storage, network, analytics, external SDKs, time, randomness, feature flags, or postMessage.
- The raw external shape differs from internal domain shape.
- Tests need a fake or mock.

When shared code can be created:

- At least two features need it.
- It is domain-neutral.
- It has stable ownership and tests.
- It does not import feature internals.

---

## 6. Next.js and React Agent-Friendly Reference Architecture

```text
src/
  app/
    projects/
      [projectId]/
        page.tsx
        loading.tsx
        error.tsx
    api/
      invoices/
        route.ts

  features/
    projects/
      index.ts
      AGENTS.md
      contracts/
        api.ts
        routes.ts
        testIds.ts
        events.ts
      data/
        server/
          projectRepository.ts
          projectRouteHandler.ts
        client/
          projectClient.ts
        mappers/
          projectDtoMapper.ts
        fixtures/
          project.fixtures.ts
      engine/
        projectTypes.ts
        projectRules.ts
        projectRules.test.ts
      state/
        projectState.ts
        useProjectState.ts
      ui/
        ProjectHeader.tsx
        ProjectTabs.tsx
        ProjectEmptyState.tsx
        Project.module.css
      screens/
        ProjectScreen.tsx
        ProjectScreen.client.tsx
      tests/
        project.contract.test.ts
        project.e2e.spec.ts
        project.visual.spec.ts

  shared/
    ui/
      Button.tsx
      Dialog.tsx
    design/
      tokens.ts
      tokens.css
    assets/
      manifest.ts
    storage/
      createJsonStorage.ts
      storageKeys.ts
    routes/
      routes.ts
    events/
      createMessageContract.ts
    config/
      env.ts
    browser/
      safeWindow.ts
      viewport.ts
    lib/
      date.ts
      result.ts

  server/
    db/
    auth/

  tests/
    playwright/
      global.setup.ts
      screenshot.css

  scripts/
    check-architecture.mjs
    check-giant-files.mjs
    check-forbidden-patterns.mjs

  .agent/
    PROGRESS.md
    EVIDENCE.md
    DECISIONS.md
    PLANS.md
```

### Layer rules

| Layer | Should contain | Must not contain |
|---|---|---|
| `src/app` | Route entries, layouts, loading/error boundaries, route handler delegators | Business rules, giant JSX, raw storage, DOM APIs |
| `features/<feature>/contracts` | Schemas, route builders, event contracts, storage keys, test IDs | Implementations or rendering |
| `features/<feature>/engine` | Pure domain logic, calculations, invariants | React, Next, DOM, fetch, storage, store |
| `features/<feature>/data` | API clients, repositories, DTO mappers, storage adapters | JSX or styling |
| `features/<feature>/state` | Reducers, state machines, selectors, orchestration hooks | Domain rules that belong in engine |
| `features/<feature>/ui` | Presentational components and local styles | Fetching, storage, domain calculations |
| `features/<feature>/screens` | Feature composition: data + state + UI | Deep domain algorithms |
| `shared/ui` | Cross-feature primitives | Feature-specific business behavior |
| `shared/design` | Tokens and themes | Page-specific styling |
| `shared/lib` | Pure generic helpers | React, Next, feature imports |

### Import graph

```text
src/app
  -> features/<feature> public API or screens
  -> shared/*

features/<feature>/screens
  -> features/<feature>/{contracts,data,state,ui,engine}
  -> shared/*

features/<feature>/ui
  -> features/<feature>/contracts
  -> shared/{ui,design,lib}
  X  no data/server, no storage, no browser APIs, no other feature internals

features/<feature>/state
  -> features/<feature>/{contracts,engine,data/client}
  -> shared/lib
  X  no JSX, no CSS, no route files

features/<feature>/engine
  -> features/<feature>/contracts
  -> shared/lib
  X  no React, Next, DOM, fetch, storage, store

shared/*
  X  no imports from features/*
```

### Next.js rules

- Use Server Components by default.
- Add `'use client'` only at the smallest interactive boundary.
- Props crossing server to client must be serializable.
- Client Components own event handlers and browser-only behavior, but through adapters when possible.
- Hooks belong in `state/` or `ui/hooks/`, not `engine/`.

---

## 7. Verification and Acceptance Harness

### 7.1 Required command surface

```json
{
  "scripts": {
    "verify": "pnpm check:types && pnpm check:lint && pnpm test:unit && pnpm test:contracts && pnpm test:e2e && pnpm test:visual && pnpm check:architecture",
    "check:types": "tsc --noEmit",
    "check:lint": "eslint .",
    "test:unit": "vitest run --config vitest.config.ts",
    "test:contracts": "vitest run --config vitest.contract.config.ts",
    "test:e2e": "playwright test --project=chromium",
    "test:visual": "playwright test --project=chromium --grep @visual",
    "check:architecture": "node scripts/check-giant-files.mjs && node scripts/check-forbidden-patterns.mjs && eslint . --max-warnings=0"
  }
}
```

### 7.2 Acceptance gates

| Gate | Purpose | Agent success condition |
|---|---|---|
| Typecheck | Catch contract drift and invalid types | `pnpm check:types` passes. |
| Lint | Enforce style and restricted imports | `pnpm check:lint` passes. |
| Unit tests | Validate pure engine and state | Changed engine/state has tests. |
| Contract tests | Validate schemas, storage, routes, events | Boundary fixtures parse and serialize. |
| Playwright E2E | Verify user-visible behavior | Critical flow passes. |
| Screenshot regression | Verify visual parity | Baselines pass in fixed CI environment. |
| Architecture checks | Enforce module boundaries | No forbidden imports or globals. |
| Giant-file checks | Prevent file entropy | Thresholds pass. |
| Forbidden-pattern checks | Block `@ts-nocheck`, undocumented `any`, raw browser APIs in pure modules | Zero findings. |
| Evidence ledger | Prevent false completion | `.agent/EVIDENCE.md` updated for risky work. |

### 7.3 ESLint boundary example

```js
// eslint.config.mjs
export default [
  {
    files: ['src/features/*/engine/**/*.{ts,tsx}', 'src/shared/lib/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            'react',
            'react-dom',
            'next/*',
            '@/features/*/ui/*',
            '@/features/*/state/*',
            '@/features/*/data/*',
            '@/shared/browser/*',
            '@/shared/storage/*'
          ]
        }
      ],
      'no-restricted-globals': [
        'error',
        'window',
        'document',
        'localStorage',
        'sessionStorage'
      ]
    }
  },
  {
    files: ['src/features/*/ui/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            '@/features/*/data/server/*',
            '@/server/*'
          ]
        }
      ]
    }
  },
  {
    files: ['src/app/**/page.tsx', 'src/app/**/layout.tsx'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            '@/features/*/engine/*',
            '@/features/*/data/*',
            '@/shared/storage/*',
            '@/shared/browser/*'
          ]
        }
      ]
    }
  }
];
```

### 7.4 Giant-file check

```js
// scripts/check-giant-files.mjs
import fs from 'node:fs/promises';
import fg from 'fast-glob';

const files = await fg(
  ['src/**/*.{ts,tsx,css}', '!src/**/*.generated.*', '!src/**/__snapshots__/**'],
  { dot: false }
);

const limits = [
  { test: (f) => /src\/app\/.*\/page\.tsx$/.test(f), max: 80 },
  { test: (f) => /src\/app\/.*\/layout\.tsx$/.test(f), max: 100 },
  { test: (f) => /src\/app\/.*\/route\.ts$/.test(f), max: 100 },
  { test: (f) => f.endsWith('.tsx'), max: 200 },
  { test: () => true, max: 300 }
];

const allowlist = new Set([
  // 'src/path/to/exception.tsx' // owner, reason, expiry
]);

let failed = false;

for (const file of files) {
  if (allowlist.has(file)) continue;
  const text = await fs.readFile(file, 'utf8');
  const loc = text.split('\n').length;
  const max = limits.find((rule) => rule.test(file)).max;

  if (loc > max) {
    failed = true;
    console.error(`${file}: ${loc} LOC > ${max}. Split this file before continuing.`);
  }
}

if (failed) process.exit(1);
```

### 7.5 Playwright visual contract

```ts
// src/features/dashboard/tests/dashboard.visual.spec.ts
import { expect, test } from '@playwright/test';
import { routes } from '@/shared/routes/routes';
import { dashboardTestIds } from '../contracts/testIds';

test('@visual dashboard shell visual parity', async ({ page }) => {
  await page.goto(routes.dashboard());

  await expect(page.getByTestId(dashboardTestIds.shell)).toBeVisible();
  await expect(page.getByTestId(dashboardTestIds.revenueChart)).toBeVisible();

  await expect(page).toHaveScreenshot('dashboard-shell.png', {
    animations: 'disabled',
    maxDiffPixels: 100
  });
});
```

---

## 8. Instruction Files

### 8.1 What belongs where

| File | Include | Do not include |
|---|---|---|
| Global Codex `~/.codex/AGENTS.md` | Universal working habits and verification discipline | Repo-specific architecture |
| Global Claude `~/.claude/CLAUDE.md` | Personal defaults and verification habits | Long procedures or repo-specific policy |
| Repo `AGENTS.md` | Architecture map, commands, boundaries, done definition | Huge style guides or vague ideals |
| Repo `CLAUDE.md` | Claude-specific note and pointer to `AGENTS.md` | Duplicated long instructions |
| `.cursor/rules/*.mdc` | Focused path-scoped rules | Unscoped walls of text |
| Feature `AGENTS.md` | Local exceptions and feature-specific rules | Global policy |
| `.agent/PROGRESS.md` | Current checkpoint status | Permanent architecture docs |
| `.agent/EVIDENCE.md` | Command output and verification evidence | Aspirational claims |

### 8.2 Repo `AGENTS.md` template

```md
# AGENTS.md - Frontend and Full-Stack Repository Contract

This file is the primary repository contract for AI coding agents.

## First steps

1. Read this file.
2. Read `package.json` scripts.
3. Identify the smallest feature boundary that owns the requested change.
4. Read relevant contracts before implementation.
5. Make a plan when the change touches more than one layer.
6. Run verification before claiming done.

## Architecture map

- `src/app/`: Next.js route entrypoints only.
- `src/features/<feature>/`: feature-owned code.
- `src/features/<feature>/contracts/`: schemas, routes, events, storage keys, test IDs.
- `src/features/<feature>/engine/`: pure domain logic.
- `src/features/<feature>/data/`: API clients, repositories, DTO mappers, storage adapters.
- `src/features/<feature>/state/`: reducers, state machines, selectors, feature hooks.
- `src/features/<feature>/ui/`: presentational components only.
- `src/features/<feature>/screens/`: data + state + UI composition.
- `src/shared/`: cross-feature primitives and infrastructure only.
- `.agent/`: progress, evidence, decisions, and long-running plans.

## Route rules

- `src/app/**/page.tsx` must be thin.
- `src/app/**/route.ts` must validate request input and delegate to a feature server handler.
- Route files must not contain business rules, raw storage, browser APIs, or giant JSX.

## Boundary rules

- Other modules may import a feature only through its public API.
- Do not import another feature's internals.
- Keep pure engine code free of React, Next, DOM, store, network, and storage imports.
- Browser APIs and external data belong behind adapters.

## Contract rules

Contractize routes, search params, API bodies, storage keys, assets, domain entities, events, design tokens, and DOM test IDs.

Do not duplicate string contracts. Use runtime schemas at external, persisted, and untrusted boundaries.

## File limits

- `page.tsx`: max 80 LOC
- `layout.tsx`: max 100 LOC
- `route.ts`: max 100 LOC
- React component file: max 200 LOC
- General source file: max 300 LOC
- Non-generated hard cap: max 500 LOC

## Verification

Run:

```bash
pnpm verify
```

Do not claim done unless verification passes or exact blockers are documented.
```

### 8.3 Repo `CLAUDE.md` template

```md
# CLAUDE.md

Primary repository instructions live in `AGENTS.md`.

Claude-specific guidance:

- Read `AGENTS.md` before making edits.
- Use plan mode for changes touching multiple features, contracts, or architecture boundaries.
- For long-running work, maintain `.agent/PROGRESS.md` and `.agent/EVIDENCE.md`.
- If context is compacted or resumed, reread `AGENTS.md`, `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, and the recent git diff.
- Do not rely on memory for architecture rules.
- Do not mark done from inspection alone. Run `pnpm verify` or document exact blockers.
```

### 8.4 Cursor rule templates

```md
---
description: Frontend architecture boundaries for agents.
globs: src/**/*.{ts,tsx}
alwaysApply: false
---

# Frontend Architecture Boundaries

- `src/app/**` is route composition only.
- `src/features/<feature>/engine/**` is pure domain logic.
- `src/features/<feature>/data/**` owns external data and storage adapters.
- `src/features/<feature>/state/**` owns reducers, state machines, selectors, and hooks.
- `src/features/<feature>/ui/**` owns presentational UI only.
- `src/features/<feature>/screens/**` wires data + state + UI.
- `src/shared/**` must not import from `src/features/**`.

Do not import another feature's internals. Use its public API.
```

```md
---
description: Frontend verification and done definition.
alwaysApply: true
---

# Verification Rules

Default command:

```bash
pnpm verify
```

Do not claim done until relevant verification passes.

- Changed domain logic: run unit tests.
- Changed contracts: run contract tests.
- Changed user flows: run Playwright.
- Changed UI layout: run screenshot regression.
- Long-running or risky work: update `.agent/EVIDENCE.md`.
```

---

## 9. Architecture Refactor Goal Prompt

```md
You are refactoring this frontend/full-stack repository to make it safer for long-term AI coding agent maintenance.

## Read first

- AGENTS.md
- package.json scripts
- current route files
- feature structure
- shared structure
- tests and Playwright config

## Goal

Refactor the target area so that:

- route files are thin composition only
- feature code is organized into contracts/data/engine/state/ui/screens/tests
- business rules live in pure engine modules
- browser APIs and storage live behind adapters
- cross-boundary strings are explicit typed contracts
- UI components are presentational and under size limits
- feature modules expose explicit public APIs
- verification commands pass

## Non-goals

- Do not change product behavior unless required.
- Do not redesign UI unless explicitly requested.
- Do not update visual snapshots unless the task explicitly says visual output changed.
- Do not introduce new dependencies without documenting why.
- Do not modify unrelated features.

## Required plan

Before editing, produce:

1. Current files and responsibilities.
2. Boundary violations found.
3. Proposed target structure.
4. Contracts to create or update.
5. Tests/checks to run.
6. Rollback strategy.

## Acceptance

Complete only when:

- no route file exceeds limits
- no component exceeds limits
- pure engine imports no React/DOM/store/network/storage
- UI does not directly touch raw browser APIs except through approved adapters/hooks
- contracts are explicit and tested
- architecture checks pass
- `pnpm verify` passes or blockers are documented with command output
```

---

## 10. Counter-Evidence and Caveats

- More instructions can reduce reliability by consuming context and creating conflicts. Keep always-on rules short and move detailed workflows into Skills or scoped files.
- Instruction files are not enforcement. Claude memory docs explicitly frame memory files as context; hard rules need hooks, linters, tests, or CI.
- Screenshot tests are environment-sensitive. Playwright documents that screenshots can vary by OS, hardware, headless mode, and power settings. Baselines must be generated and checked in a stable CI environment.
- Review bots do not replace CI. Bugbot or similar tools should supplement required checks, not become the only gate.
- Strict boundaries need an exception process. Every exception should have an owner, reason, verification coverage, and expiry.

---

## Final Mental Model

```text
explicit feature ownership
+ typed contracts
+ pure domain engine
+ adapterized side effects
+ small files
+ executable import boundaries
+ deterministic verification
+ independent review
+ progress/evidence ledger
= frontend/full-stack repo that coding agents can safely maintain
```
