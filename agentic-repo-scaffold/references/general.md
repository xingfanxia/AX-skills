# Agentic General and Framework-Agnostic Repository Guideline

## Scope

This guideline applies to any large repository maintained by AI coding agents, regardless of framework or language. It is useful for backend systems, frontend systems, monorepos, CLI tools, SDKs, infrastructure-as-code, data systems, ML systems, internal tools, platform packages, and mixed-language repositories.

The core abstraction is:

```text
public contracts
+ pure core logic
+ application workflows
+ ports
+ adapters
+ generated code isolation
+ deterministic verification
+ scoped agent instructions
```

This is not a traditional clean-code guide. It is a set of executable engineering rules that help agents locate, modify, verify, and roll back code safely.

---

## 1. Executive Summary

1. Repository structure is an agent navigation API. Directory names must express ownership, stability, allowed imports, and verification scope.
2. Every module/package/service needs an explicit public API. External consumers import from `public/`, `index.*`, `api/`, or `contracts/`; internals are private by default.
3. Core logic must be pure. `core/` should not depend on filesystem, network, database, framework, global config, clock, random, process environment, or CLI flags.
4. Application/workflow code orchestrates. It coordinates use cases, state machines, policies, and ports, but does not own concrete side-effect details.
5. Adapters own side effects. Filesystem, network, DB, queues, cloud SDKs, external tools, and OS/process interactions live in adapters.
6. All boundaries are contracts. Public APIs, CLI args, config/env, file formats, wire formats, persistence, events, errors, permissions, telemetry, and generated artifacts require schemas/specs/types/tests.
7. Generated code must be isolated and reproducible. Put generated output in `generated/`, mark it clearly, prohibit manual edits, and check that generators are clean.
8. Build and test must be deterministic. Provide one command such as `make verify`; pin tool versions, dependencies, fixtures, time, and randomness where practical.
9. Architecture rules must be executable. Use import rules, architecture tests, dependency graph checks, custom scripts, hooks, and CI, not prose alone.
10. Separate generation context from verification context. The agent that writes a change should not be the only judge of whether it is done.
11. Instruction files must be short, scoped, and layered. Global rules describe work habits; repo rules describe architecture and commands; local rules describe exceptions; Skills store long procedures.
12. No giant files. Set LOC, complexity, import-count, and responsibility thresholds for every language and fail CI when they are exceeded without an exception.
13. Long-running work needs progress, evidence, and decision ledgers. Use `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, and `.agent/DECISIONS.md`.
14. Public contract changes require compatibility checks. Agents must not change public surfaces without updating specs, fixtures, docs, and breaking-change gates.
15. Anything an agent would otherwise infer from tribal knowledge should become a file, schema, lint rule, test, CI gate, or documented public API.

---

## 2. Source Matrix

| Source name | Organization | URL | Source type | General relevance | Confidence |
|---|---|---|---|---|---|
| Codex AGENTS.md guidance | OpenAI | https://developers.openai.com/codex/guides/agents-md | official | Instruction hierarchy, nested overrides, context size limits | High |
| Codex prompting | OpenAI | https://developers.openai.com/codex/prompting | official | Validation, smaller tasks, coding-agent workflows | High |
| Codex ExecPlans | OpenAI | https://developers.openai.com/cookbook/articles/codex_exec_plans | official | Structured long-running plans | High |
| Codex Skills | OpenAI | https://developers.openai.com/codex/skills | official | Progressive disclosure for reusable procedures | High |
| Claude Code memory | Anthropic | https://docs.anthropic.com/en/docs/claude-code/memory | official | CLAUDE.md scope and enforcement caveat | High |
| Claude Code hooks | Anthropic | https://docs.anthropic.com/en/docs/claude-code/hooks-guide | official | Deterministic enforcement around tool calls | High |
| Claude Code Skills | Anthropic | https://docs.anthropic.com/en/docs/claude-code/skills | official | Procedure packaging outside always-on context | High |
| Context engineering for agents | Anthropic | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | official | Context pollution, file hierarchy, progressive disclosure | High |
| Long-running agent harnesses | Anthropic | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | official | Progress files, acceptance harnesses, incremental work | High |
| Cursor Rules | Cursor | https://cursor.com/docs/rules | official | Scoped repository rules | High |
| Cursor Subagents | Cursor | https://cursor.com/docs/subagents | official | Isolated contexts and verifier pattern | High |
| Cursor Bugbot | Cursor | https://cursor.com/docs/bugbot | official | PR review and branch quality gates | High |
| GitHub Copilot coding agent | GitHub | https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent | official | Autonomous branch-based coding agent | High |
| OpenAPI Specification | OpenAPI Initiative | https://swagger.io/specification/ | official | HTTP API contracts | High |
| JSON Schema | JSON Schema | https://json-schema.org/specification | official | Runtime validation for JSON contracts | High |
| Protocol Buffers | Google | https://protobuf.dev/programming-guides/proto3/ | official | Binary/data/RPC schema contracts | High |
| AsyncAPI | AsyncAPI Initiative | https://www.asyncapi.com/ | official | Event-driven contracts | High |
| CloudEvents | CNCF | https://cloudevents.io/ | official | Event metadata contract | High |
| RFC 9457 Problem Details | IETF | https://www.rfc-editor.org/info/rfc9457 | standard | Machine-readable HTTP error contracts | High |
| OpenTelemetry | OpenTelemetry | https://opentelemetry.io/docs/ | official | Observability contracts | High |
| OWASP API Security Top 10 | OWASP | https://owasp.org/API-Security/editions/2023/en/0x00-header/ | official | Security verification categories | High |
| SLSA | OpenSSF | https://slsa.dev/ | official | Supply-chain integrity and provenance | High |
| OpenSSF Scorecard | OpenSSF | https://scorecard.dev/ | official | Automated security posture checks | High |
| Bazel hermeticity | Bazel | https://bazel.build/basics/hermeticity | official | Reproducible and hermetic build principle | Medium |
| ArchUnit | ArchUnit | https://www.archunit.org/ | official | Executable architecture tests | Medium |
| dependency-cruiser | OSS | https://github.com/sverweij/dependency-cruiser | secondary | Dependency graph checks | Medium |
| Pact docs | Pact | https://docs.pact.io/ | official | Consumer/provider contract testing | High |
| Testcontainers | Testcontainers | https://testcontainers.com/guides/introducing-testcontainers/ | official | Real-dependency integration tests | High |

---

## 3. Agentic General Architecture Principles

### Principle 1: Repository structure is the first API agents read

Why it matters for agents: Agents use paths, names, and local files as the initial context graph. If structure is ambiguous, they overuse search, edit the wrong module, or create duplicate abstractions.

Concrete rule:

- Use directories that state responsibility: `public`, `contracts`, `core`, `application`, `ports`, `adapters`, `generated`, `tests`, `tools`, `.agent`.
- In monorepos, every package/service/module should follow the same internal pattern unless it has a documented exception.

Anti-pattern:

- `lib/`, `helpers/`, `misc/`, `new/`, `old/`, `v2/`, `common/` without ownership or contract rules.

Example boundary:

```text
packages/invoicing/core/rules/calculateTax.ts
packages/invoicing/adapters/postgres/InvoiceRepository.ts
packages/invoicing/public/index.ts
```

Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

### Principle 2: Public API is explicit; internals are private

Why it matters for agents: Without explicit public APIs, agents deep-import internals and make future refactors unsafe.

Concrete rule:

- A module exposes a small public API via `public/`, `index.*`, `api/`, or generated clients.
- Deep imports into private directories are blocked by lint/architecture checks.
- Public exports have compatibility tests or API snapshots.

Anti-pattern:

```ts
import { InternalParserState } from '@repo/parser/core/parser/InternalParserState';
```

Preferred:

```ts
import { parseDocument } from '@repo/parser';
```

Source: https://cursor.com/docs/rules

### Principle 3: Core logic is pure

Why it matters for agents: Pure code can be tested and changed without provisioning cloud resources, databases, browsers, or credentials. It gives agents a deterministic repair target.

Concrete rule:

- `core/` imports only local core/contracts and pure shared libraries.
- No IO, framework, config, env, time, randomness, process state, telemetry, or external SDKs.

Anti-pattern:

- A core parser reads files, logs metrics, reads environment variables, and updates a DB.

Preferred:

```text
core/parseDocument.ts      # pure parse function
adapters/filesystem/readDocument.ts
application/commands/parseFile.ts
```

Source: https://developers.openai.com/codex/prompting

### Principle 4: Workflows orchestrate through ports

Why it matters for agents: Agents need a single place to understand use-case flow. Ports make external dependencies visible and replaceable.

Concrete rule:

- `application/` owns commands, queries, workflows, transactions, policy calls, and orchestration.
- `application/` depends on `ports`, not `adapters`.
- Concrete adapters are wired at the outer composition root.

Anti-pattern:

- CLI command contains parsing, validation, algorithm, filesystem writes, network calls, and formatting in one file.

Preferred:

```text
cli/command.ts -> application/commands/runImport.ts -> core/* + ports/* -> adapters/*
```

Source: https://docs.pact.io/

### Principle 5: Every boundary is a contract

Why it matters for agents: Agents are good at following explicit contracts and poor at preserving hidden tribal knowledge.

Concrete rule:

- If another module, process, user, file, service, database, queue, CLI, or agent depends on it, it is a contract.
- Contract files are committed, versioned where necessary, tested, and used by generators or validators.

Anti-pattern:

- A CSV column order is described only in a Slack message or hidden in parsing code.

Preferred:

```text
contracts/file-formats/import-v1.schema.json
contracts/errors/importErrors.ts
contracts/cli/importCommand.ts
```

Sources:

- https://json-schema.org/specification
- https://swagger.io/specification/
- https://protobuf.dev/programming-guides/proto3/

### Principle 6: Generated code is not source code

Why it matters for agents: Agents frequently patch generated files when tests fail. Those changes disappear on regeneration and create false fixes.

Concrete rule:

- Generated files live under `generated/` or have a clear suffix/header.
- Manual edits are forbidden.
- Verification includes a generated-clean check.

Anti-pattern:

- Agent edits generated TypeScript client instead of updating OpenAPI spec and regenerating.

Preferred:

```text
contracts/api/openapi.yaml
scripts/generate-api-client.sh
src/generated/api-client/*
```

Source: https://developers.openai.com/codex/skills

### Principle 7: Deterministic verification is mandatory

Why it matters for agents: Agents need crisp pass/fail evidence. Flaky, undocumented, or environment-dependent tests lead to false completion.

Concrete rule:

- Provide one default command: `make verify` or equivalent.
- Pin tool versions and dependencies.
- Use fixtures, fake clocks, seeded randomness, containers, or hermetic builds when practical.

Anti-pattern:

- "It passes on my machine" tests that require unstated local services or credentials.

Source: https://bazel.build/basics/hermeticity

### Principle 8: Architecture rules are executable

Why it matters for agents: Instructions are context, not enforcement. Agents under context pressure may violate prose rules.

Concrete rule:

- Use tools such as ArchUnit, dependency-cruiser, import-linter, ESLint, Bazel visibility, CODEOWNERS, custom scripts, hooks, and CI checks.

Anti-pattern:

- README says "core must not import adapters" but no check fails when it does.

Sources:

- https://www.archunit.org/
- https://github.com/sverweij/dependency-cruiser
- https://docs.anthropic.com/en/docs/claude-code/hooks-guide

### Principle 9: Verification context is separate from implementation context

Why it matters for agents: The implementing agent may overfit to its own assumptions and declare done prematurely.

Concrete rule:

- Use CI, verifier subagents, review bots, or clean worktree verification.
- Long-running tasks record evidence in `.agent/EVIDENCE.md`.

Anti-pattern:

- Same agent writes code and approves it without running tests.

Sources:

- https://cursor.com/docs/subagents
- https://cursor.com/docs/bugbot

### Principle 10: Instructions are layered, not dumped into one file

Why it matters for agents: Long, global, always-on instructions create context pollution and conflicts.

Concrete rule:

- Global instructions: universal habits.
- Repo instructions: architecture, commands, boundaries.
- Module-local instructions: local exceptions.
- Skills: long procedures and workflows.
- Task prompt: current goal, constraints, acceptance.

Anti-pattern:

- A 5,000-line root instruction file with every historical decision and unrelated examples.

Sources:

- https://developers.openai.com/codex/guides/agents-md
- https://docs.anthropic.com/en/docs/claude-code/skills
- https://cursor.com/docs/rules

---

## 4. General Contract Design Guidelines

### 4.1 What must be contractized

| Boundary | Contract artifact | Verification |
|---|---|---|
| Public package/module API | Exported types, API snapshot, public docs | API extractor, compile check, semver/breaking check |
| CLI command | Args schema, examples, exit codes | Golden tests, help snapshot, invalid input tests |
| Config/env | Schema, defaults, secret names | Boot validation, missing/invalid config tests |
| File format | JSON Schema, Protobuf, Avro, CSV schema | Parser tests, compatibility fixtures |
| Network/API | OpenAPI, gRPC, GraphQL schema | Contract lint, generated client/server, breaking diff |
| Events/messages | AsyncAPI, CloudEvents, schema registry | Producer/consumer tests |
| Errors | Typed error enum/envelope | Negative tests, docs/examples |
| Persistence | Migrations, schema, versioning | Migration dry-runs, data compatibility tests |
| Permissions/capabilities | Policy file/table/test fixtures | Authz matrix tests |
| Telemetry | Span/metric/log field names | Telemetry assertion tests |
| Generated code | Generator command + source contract | Generated-clean check |
| Workflow/task | State machine or workflow spec | Transition tests |
| External tools | Wrapper command contract | Tool availability/version check |

General rule:

```text
If another module, process, user, service, file, database, queue, CLI, or agent depends on it, it is a contract.
```

### 4.2 Contract placement

Recommended locations:

```text
contracts/
  api/
  events/
  config/
  errors/
  telemetry/
  file-formats/
  permissions/

packages/<module>/contracts/
  input.schema.json
  output.schema.json
  errors.ts
  events.ts
```

Placement rules:

- Repo-level contracts are for cross-module or external boundaries.
- Module-level contracts are for feature/module-local boundaries.
- Generated contracts should state their source and generation command.
- Fixtures belong next to the contract they validate.

### 4.3 Runtime validation rule

- Trusted in-memory values created by core code can use compile-time types only.
- External, persisted, or untrusted values need runtime validation.
- Public contract changes require compatibility checks.
- Persisted formats require versioning and migration/default handling.
- Strings that cross boundaries should be constants, enums, branded IDs, or generated types.

### 4.4 Avoid stringly typed boundaries

Do not inline:

- endpoint paths
- event names
- storage keys
- feature flag keys
- metric names
- error codes
- file format names
- permission names
- CLI command names used by tests or scripts
- generated artifact names

Instead, define contract constants and import them.

```ts
export const importEventTypes = {
  importStarted: 'import.started.v1',
  importCompleted: 'import.completed.v1',
  importFailed: 'import.failed.v1'
} as const;
```

---

## 5. General Module Decomposition Rules

### 5.1 Hard thresholds

| Target | Limit | Action |
|---|---:|---|
| Public entry file | 100 LOC | Export only; move logic inward. |
| CLI command file | 120 LOC | Extract parser, use case, output formatter. |
| Core logic file | 250 LOC | Split by model, rule, algorithm, or state machine. |
| Application workflow | 250 LOC | Split validation, orchestration, policy, adapters. |
| Adapter | 250 LOC | Split client, mapper, retry, and error translator. |
| Test file | 400 LOC | Split by behavior or contract. |
| Any non-generated file | 500 LOC hard cap | Allowlist only with owner, reason, expiry. |
| Function/method | 60 LOC | Extract helpers or state machine. |
| Module imports | More than 15 imports | Split responsibility or introduce facade. |
| Public API exports | More than 30 exports | Split module, namespace, or subpackage. |

### 5.2 Refactor triggers

- Core imports an adapter, framework, environment, filesystem, network, clock, or random.
- Public API exports private implementation details.
- Adapter contains business/domain rules.
- Config reads are scattered outside config module.
- Same contract string appears twice.
- Generated file is manually modified.
- Test depends on wall clock or external network without fixture.
- Workflow cannot be tested without full system startup.
- New behavior lacks an acceptance command.
- A fix touches unrelated modules to bypass a boundary.
- A module has no owner or instruction file in a large repo.

### 5.3 Required split rules

Split a public entry file when:

- It contains implementation logic.
- It performs side effects at import time.
- It exports too many unrelated symbols.
- It exceeds 100 LOC.

Split a CLI command when:

- It parses args, runs business logic, performs IO, and formats output in one file.
- It has multiple output modes or more than one side effect.
- It exceeds 120 LOC.

Split a core file when:

- It contains multiple algorithms or state machines.
- It mixes parsing, validation, calculation, and formatting.
- It needs time, random, IO, or config to run.
- It exceeds 250 LOC.

Split an adapter when:

- It contains raw client calls, retry policy, mapping, and business decisions.
- It supports multiple external resources or protocols.
- It exceeds 250 LOC.

Create a shared package only when:

- At least two modules need the same stable behavior.
- The behavior is domain-neutral or intentionally platform-level.
- It has a public API, tests, and owner.
- It does not import consuming modules.

---

## 6. General Reference Architecture

```text
repo/
  AGENTS.md
  CLAUDE.md
  README.md

  docs/
    architecture/
      module-map.md
      dependency-rules.md
      adr/
    contracts/
      public-apis.md
      compatibility-policy.md

  contracts/
    api/
    events/
    config/
    errors/
    telemetry/
    file-formats/
    permissions/

  packages/
    <module>/
      AGENTS.md

      public/
        index.ts
        types.ts

      contracts/
        input.schema.json
        output.schema.json
        errors.ts
        events.ts

      core/
        model/
        rules/
        algorithms/
        state-machine/

      application/
        commands/
        queries/
        workflows/

      ports/
        StoragePort.ts
        NetworkPort.ts
        ClockPort.ts
        RandomPort.ts

      adapters/
        filesystem/
        network/
        database/
        third-party/
        cli/
        web/
        queue/

      generated/
        README.md

      tests/
        unit/
        contract/
        integration/
        architecture/
        fixtures/

  tools/
    verify/
      check-boundaries.*
      check-giant-files.*
      check-generated-clean.*
      check-contracts.*
    scripts/

  .agent/
    PROGRESS.md
    EVIDENCE.md
    DECISIONS.md
```

### Layer rules

| Layer | Purpose | Allowed | Forbidden |
|---|---|---|---|
| `public/` | Stable module API | Exports, public types, factories | Private internals, side effects at import time |
| `contracts/` | Boundary specs | Schema, type, examples, compatibility notes | Implementation |
| `core/` | Pure logic | Deterministic model/rules/algorithms | IO, framework, clock/random, config |
| `application/` | Use cases/workflows | Orchestration, policies, ports | Concrete SDK clients |
| `ports/` | Dependency interfaces | Interfaces/protocols | Implementation logic |
| `adapters/` | Side effects | Concrete IO implementations | Domain decisions |
| `generated/` | Generated artifacts | Generated files only | Manual edits |
| `tests/unit` | Pure behavior tests | Core/application fakes | Real network |
| `tests/contract` | Boundary compatibility | Specs, schemas, fixtures | Broad flaky end-to-end replacement |
| `tests/integration` | Real dependency behavior | DB/cache/fs/network fakes or containers | Replacing unit tests |
| `tests/architecture` | Boundary enforcement | Import/dependency rules | Product behavior tests |

### Import graph

```text
public/
  -> contracts/
  -> core/ types only when stable
  X  no adapters with side effects at import time

application/
  -> core/
  -> contracts/
  -> ports/
  X  no adapters/

core/
  -> contracts/
  -> pure shared libraries
  X  no IO, framework, env, clock, random, adapters

adapters/
  -> ports/
  -> contracts/
  -> external SDKs
  -> core mappers if pure

shared/
  X  no imports from consuming packages unless explicitly platform-owned
```

---

## 7. General Verification and Acceptance Harness

### 7.1 Standard command surface

```text
make verify
make check-static
make check-contracts
make test-unit
make test-integration
make test-architecture
make check-security
make check-generated
make check-giant-files
```

### 7.2 Generic `Makefile` shape

```makefile
verify: check-static check-contracts test-unit test-integration test-architecture check-security check-generated check-giant-files

check-static:
	./tools/verify/check-static.sh

check-contracts:
	./tools/verify/check-contracts.sh

test-unit:
	./tools/verify/test-unit.sh

test-integration:
	./tools/verify/test-integration.sh

test-architecture:
	./tools/verify/test-architecture.sh

check-security:
	./tools/verify/check-security.sh

check-generated:
	./tools/verify/check-generated-clean.sh

check-giant-files:
	./tools/verify/check-giant-files.sh
```

### 7.3 Acceptance matrix by change type

| Change type | Required checks |
|---|---|
| Pure core logic | Unit tests plus property/golden tests if applicable |
| Public API | API snapshot plus compatibility check plus docs/examples |
| CLI | Arg parsing tests, golden output, exit code tests |
| Config/env | Missing/invalid config tests |
| Adapter | Integration test or contract test |
| Persistence | Migration dry-run and fixture compatibility |
| Event/message | Schema validation plus producer/consumer tests |
| Generated code | Generator run plus generated-clean check |
| Architecture refactor | Architecture tests plus no giant files plus full verify |
| Security-sensitive code | Negative security tests plus secret/PII/resource checks |
| Performance-sensitive code | Benchmark, load fixture, or regression test |

### 7.4 Generic architecture check example

```js
// tools/verify/check-boundaries.mjs
import fs from 'node:fs/promises';
import fg from 'fast-glob';

const files = await fg([
  'packages/**/*.{ts,tsx,js,jsx,py,go,java,kt,rs}',
  '!**/generated/**',
  '!**/vendor/**',
  '!**/node_modules/**'
]);

const rules = [
  {
    name: 'core must be pure',
    file: /\/core\//,
    forbidden: [
      /\/adapters\//,
      /\bprocess\.env\b/,
      /\bDate\.now\(\)/,
      /\bMath\.random\(\)/,
      /from ['\"](fs|path|http|https|axios|got|node-fetch)/
    ]
  },
  {
    name: 'application must not import adapters',
    file: /\/application\//,
    forbidden: [
      /\/adapters\//
    ]
  },
  {
    name: 'generated files must not be edited manually',
    file: /\/generated\//,
    forbidden: [
      /MANUAL EDIT/
    ]
  }
];

let failed = false;

for (const file of files) {
  const text = await fs.readFile(file, 'utf8');

  for (const rule of rules) {
    if (!rule.file.test(file)) continue;

    for (const pattern of rule.forbidden) {
      if (pattern.test(text)) {
        failed = true;
        console.error(`${file}: violates "${rule.name}" with ${pattern}`);
      }
    }
  }
}

if (failed) process.exit(1);
```

### 7.5 Generated-clean check pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

./tools/scripts/generate-all.sh

if ! git diff --quiet -- packages '**/generated/**'; then
  echo 'Generated files are not clean. Run the generator and commit the result.' >&2
  git diff -- packages '**/generated/**'
  exit 1
fi
```

### 7.6 Giant-file check pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

LIMITS = [
    ('/public/', 100),
    ('/cli/', 120),
    ('/core/', 250),
    ('/application/', 250),
    ('/adapters/', 250),
    ('/tests/', 400),
]
DEFAULT_LIMIT = 300
HARD_CAP = 500
EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.java', '.kt', '.rs', '.rb', '.php', '.cs'}

failed = False

for path in Path('.').rglob('*'):
    if not path.is_file():
        continue
    text_path = str(path).replace('\\', '/')
    if '/generated/' in text_path or '/vendor/' in text_path or '/node_modules/' in text_path:
        continue
    if path.suffix not in EXTENSIONS:
        continue
    lines = path.read_text(errors='ignore').splitlines()
    loc = len(lines)
    limit = DEFAULT_LIMIT
    for marker, marker_limit in LIMITS:
        if marker in text_path:
            limit = marker_limit
            break
    if loc > HARD_CAP or loc > limit:
        failed = True
        print(f'{text_path}: {loc} LOC > {limit}. Split this file or add an expiring allowlist entry.')

if failed:
    raise SystemExit(1)
PY
```

---

## 8. Agent Instruction Files

### 8.1 What belongs where

| File | Include | Do not include |
|---|---|---|
| Global Codex `~/.codex/AGENTS.md` | Universal habits and verification discipline | Repo-specific architecture |
| Global Claude `~/.claude/CLAUDE.md` | Personal defaults and verification habits | Long procedures |
| Repo `AGENTS.md` | Architecture map, commands, boundaries, done definition | Huge style guide or historical notes |
| Repo `CLAUDE.md` | Claude-specific pointer to `AGENTS.md` | Duplicated long repo guide |
| `.cursor/rules/*.mdc` | Focused scoped rules with globs | Vague global prose |
| Module-local `AGENTS.md` | Local exceptions and module ownership | Global policy |
| Skills | Repeatable multi-step procedures | Always-on context |
| `.agent/PROGRESS.md` | Current checkpoint state | Permanent architecture docs |
| `.agent/EVIDENCE.md` | Command output and acceptance evidence | Unsupported claims |
| `.agent/DECISIONS.md` | Architecture decisions and tradeoffs | Temporary TODO lists |

### 8.2 Repo `AGENTS.md` template

```md
# AGENTS.md - General Repository Contract for AI Coding Agents

This repository is designed to be maintained by human engineers and AI coding agents.

## First steps

1. Read this file.
2. Read local AGENTS.md files in the target subtree.
3. Read build/test scripts.
4. Identify the smallest owning module.
5. Read contracts before implementation.
6. Make a plan for multi-module changes.
7. Run verification before claiming done.

## Repository shape

Preferred module shape:

- `public/`: stable public API.
- `contracts/`: schemas, specs, examples, errors, compatibility notes.
- `core/`: pure domain/algorithm/state logic.
- `application/`: workflows/use cases/orchestration.
- `ports/`: interfaces for dependencies.
- `adapters/`: concrete side effects.
- `generated/`: generated files only.
- `tests/`: unit, contract, integration, architecture, fixtures.

## Import rules

- Public consumers may import only from `public/` or documented module entrypoints.
- `core/` must not import `adapters/`, frameworks, filesystem, network, env, clock, or random.
- `application/` may import `core/` and `ports/`, not concrete adapters.
- `adapters/` may import ports/contracts and external SDKs.
- `generated/` must not be manually edited.
- Shared utilities must not import feature/module internals.

## Contract rules

Contractize every cross-boundary value:

- public APIs
- CLI args
- config/env
- file formats
- network APIs
- events/messages
- errors
- persistence schema
- permissions/capabilities
- telemetry names/fields
- generated artifacts

Do not duplicate string contracts.
Do not change public contracts without compatibility checks and tests.
Do not parse untrusted data without runtime validation.

## Core purity rules

Files under `core/` must be deterministic and side-effect free.

Forbidden in `core/`:

- filesystem
- network
- database/cache/queue clients
- process env
- global clock/random
- framework imports
- telemetry exporters
- external SDK calls

Inject dependencies through ports and application workflows.

## File limits

- public entry file: max 100 LOC
- CLI command file: max 120 LOC
- core logic file: max 250 LOC
- application workflow: max 250 LOC
- adapter: max 250 LOC
- test file: max 400 LOC
- any non-generated file: max 500 LOC hard cap

Split files that exceed these limits unless allowlisted with owner, reason, and expiry.

## Verification

Default command:

```bash
make verify
```

Verification should include:

- static analysis
- contract checks
- unit tests
- integration tests
- architecture checks
- security checks
- generated-code clean check
- giant-file check

Do not claim done unless verification passes or exact blockers are documented.

## Long-running work

For multi-checkpoint work:

- update `.agent/PROGRESS.md`
- update `.agent/EVIDENCE.md`
- update `.agent/DECISIONS.md`
- keep changes small and reversible
- keep the repo buildable between checkpoints

## Done definition

A task is done only when:

- change is in the owning module
- contracts are updated
- core logic remains pure
- side effects are adapterized
- file-size limits are respected
- generated files are produced by generator, not hand-edited
- relevant tests pass
- architecture checks pass
- verification evidence is available
```

### 8.3 Repo `CLAUDE.md` template

```md
# CLAUDE.md

Primary repository instructions live in `AGENTS.md`.

Claude-specific guidance:

- Read `AGENTS.md` and local module instructions before editing.
- Use plan mode for changes touching multiple modules, contracts, or architecture boundaries.
- For long-running work, maintain `.agent/PROGRESS.md`, `.agent/EVIDENCE.md`, and `.agent/DECISIONS.md`.
- If context is compacted or resumed, reread the repo instructions, progress ledger, evidence ledger, and recent git diff.
- Do not rely on memory for architecture rules.
- Do not mark done from inspection alone. Run `make verify` or document exact blockers.
```

### 8.4 Cursor rule templates

```md
---
description: Framework-agnostic module boundary rules for AI coding agents.
globs: **/*.{ts,tsx,js,jsx,py,go,java,kt,rs,rb,php,cs,sql}
alwaysApply: false
---

# General Module Boundaries

Use this structure when possible:

- `public/`: stable module API
- `contracts/`: schemas/specs/examples
- `core/`: pure logic
- `application/`: workflows/use cases
- `ports/`: dependency interfaces
- `adapters/`: side effects
- `generated/`: generated artifacts
- `tests/`: verification

Rules:

- Core must not import adapters, frameworks, env, filesystem, network, clock, or random.
- Application depends on ports, not adapters.
- Consumers import public APIs only.
- Generated files are not manually edited.
```

```md
---
description: Contract-first rules for any large repository.
globs: **/*
alwaysApply: false
---

# General Contract Rules

Contractize:

- public APIs
- CLI args
- config/env
- file formats
- network APIs
- events/messages
- errors
- persistence schema
- permissions/capabilities
- telemetry names/fields
- generated artifacts

Do not duplicate contract strings.
Do not parse untrusted data without runtime validation.
Do not change public contracts without compatibility checks and tests.
```

```md
---
description: General verification and done definition.
alwaysApply: true
---

# Verification Rules

Default command:

```bash
make verify
```

Do not claim done until relevant verification passes.

Run targeted checks by change type:

- core logic: unit tests
- public API: compatibility/API snapshot tests
- CLI: arg/golden/exit-code tests
- adapters: integration or contract tests
- persistence: migration/schema compatibility tests
- events/messages: schema + producer/consumer tests
- generated code: generator + generated-clean check
- architecture: boundary checks
- security-sensitive code: negative security tests

Document exact blockers if verification cannot run.
```

---

## 9. General Architecture Refactor Goal Prompt

```md
You are refactoring this repository to make it safe for long-term AI coding agent maintenance.

## Read first

- AGENTS.md
- local AGENTS.md files in target subtree
- build/test scripts
- contracts
- module public APIs
- architecture docs
- current tests

## Goal

Refactor the target area so that:

- ownership boundaries are visible from paths
- public APIs are explicit
- cross-boundary values have contracts
- core logic is pure and deterministic
- workflows orchestrate through ports
- side effects live in adapters
- generated code is isolated
- architecture rules are executable
- verification can run from one command

## Non-goals

- Do not change behavior unless explicitly requested.
- Do not change public contracts unless explicitly requested.
- Do not hand-edit generated files.
- Do not modify unrelated modules.
- Do not add dependencies without documenting why.

## Required plan

Before editing, produce:

1. Current module map.
2. Boundary violations.
3. Target structure.
4. Contracts to create/update.
5. Tests/checks to run.
6. Rollback strategy.

## Checkpoints

1. Identify public API and contracts.
2. Extract pure core logic.
3. Introduce ports.
4. Move side effects into adapters.
5. Simplify public entrypoints/workflows.
6. Add boundary checks.
7. Run verification.

## Acceptance

Complete only when:

- consumers use public APIs only
- core has no side effects
- contracts are explicit and tested
- generated files are clean
- file-size thresholds are respected
- architecture checks pass
- verification passes or blockers are documented with exact command output
```

---

## 10. Counter-Evidence and Caveats

- Instruction files are not enforcement. Memory/instruction files are context; hard rules need hooks, CI, linters, tests, or architecture checks.
- More instructions can reduce performance. Long always-on files consume context and create conflicts. Prefer short global rules, scoped repo/module rules, and Skills.
- Contract tests do not replace all integration tests. Contract tests verify boundary expectations; integration tests verify real dependency behavior.
- Strict architecture boundaries require an exception process. Exceptions need owner, reason, expiry, and verification coverage.
- Reproducible builds can add tool overhead. Full hermeticity is valuable but not always necessary; the minimum is pinned dependencies and clean CI.
- Generated-code checks only work when generator commands are reliable and documented.
- No single agent should be assumed reliable across every task type. Design the repo so correctness is checked by tools, not by model confidence.

---

## Final Mental Model

```text
explicit public API
+ pure core
+ workflow/application layer
+ side-effect adapters
+ machine-readable contracts
+ generated-code isolation
+ executable architecture rules
+ one-command verification
= general large repo that coding agents can safely maintain
```
