# Agentic Backend and Service Repository Guideline

## Scope

This guideline is for backend services, API services, workers, event-driven systems, platform services, service monorepos, and backend-heavy full-stack repositories maintained by AI coding agents. It is designed for agents such as Codex, Claude Code, Cursor, GitHub Copilot coding agent, Devin, Windsurf/Cascade, and Sourcegraph Amp.

The focus is not generic clean code. The focus is repository design that lets agents locate ownership, change code safely, preserve contracts, test with deterministic evidence, and avoid backend-specific failure modes such as fat controllers, hidden API contracts, unsafe migrations, scattered side effects, implicit queue payloads, non-idempotent retries, and unobservable production behavior.

---

## 1. Executive Summary

1. Service boundaries must also be ownership, deployment, contract, and verification boundaries. A service directory should contain its API specs, source, migrations, tests, local instructions, and verification commands.
2. Transport handlers must be thin. HTTP controllers, gRPC handlers, GraphQL resolvers, webhook handlers, and queue consumers should parse, authenticate, validate, delegate, and map responses. They should not own business rules, SQL, retries, or SDK calls.
3. Domain core must be pure. `domain/` must not import web frameworks, ORM clients, DB drivers, queues, caches, HTTP clients, clock/random, environment variables, or observability exporters.
4. Application layer owns orchestration. Use cases handle transaction boundaries, authorization checks, idempotency, domain calls, outbox decisions, and ports.
5. Side effects must live behind ports and adapters. DB, Redis, S3, Stripe, OpenAI, email, queues, clock, random, feature flags, secrets, and metrics are adapters, not domain/application internals.
6. Public APIs must be specification-first or contract-first. REST uses OpenAPI, RPC uses Protobuf/gRPC, events use AsyncAPI or CloudEvents-compatible schemas.
7. Error responses are contracts. Public HTTP APIs should use RFC 9457 Problem Details or a typed error envelope, not ad hoc `{ error: string }` shapes.
8. Database schema is an executable contract. Use migrations, constraints, foreign keys, unique indexes, check constraints, and not-null constraints for invariants that must survive concurrency and multiple writers.
9. Migrations are append-only once applied to shared or persistent environments. Fix by adding new migrations, not by editing old ones.
10. Retried mutations must be idempotent. Resource creation, payments, webhooks, queue consumers, email/SMS sends, and quota/credit mutations need idempotency keys, dedupe storage, replay/no-op behavior, and tests.
11. Async jobs and events are APIs. Every message has a schema, version, producer, consumer, retry policy, timeout, DLQ/poison-message behavior, ordering assumptions, and idempotency contract.
12. Observability is a backend contract. New endpoints and jobs define span names, metric names, structured log fields, correlation IDs, and error classifications.
13. Security policy must be executable. AuthN/AuthZ, object-level authorization, input validation, resource limits, secret handling, and PII logging require reusable policies, tests, and CI checks.
14. Verification must run from a clean environment. `make verify` or equivalent should run static analysis, unit tests, contract checks, integration tests with real dependencies, migration dry-runs, architecture checks, and security checks.
15. The implementation agent cannot be the only judge of completion. Use CI, verifier subagents, clean-context checks, Bugbot/review bots, and evidence ledgers.

---

## 2. Source Matrix

| Source name | Organization | URL | Source type | Backend relevance | Confidence |
|---|---|---|---|---|---|
| Codex AGENTS.md guidance | OpenAI | https://developers.openai.com/codex/guides/agents-md | official | Instruction hierarchy, nested rules, context size limit | High |
| Codex prompting | OpenAI | https://developers.openai.com/codex/prompting | official | Validation-first work, small tasks, agent workflows | High |
| Codex iterative repair loops | OpenAI | https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex | official | Review, repair, validate loops | High |
| Codex ExecPlans | OpenAI | https://developers.openai.com/cookbook/articles/codex_exec_plans | official | Structured long-running execution plans | High |
| Claude Code memory | Anthropic | https://docs.anthropic.com/en/docs/claude-code/memory | official | CLAUDE.md scope and enforcement caveat | High |
| Claude Code hooks | Anthropic | https://docs.anthropic.com/en/docs/claude-code/hooks-guide | official | Deterministic enforcement around tool use | High |
| Context engineering for agents | Anthropic | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | official | Context pollution, file hierarchy, progressive disclosure | High |
| Long-running agent harnesses | Anthropic | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | official | Progress files and acceptance harnesses | High |
| Cursor Rules | Cursor | https://cursor.com/docs/rules | official | Persistent repo/team/user rules | High |
| Cursor Subagents | Cursor | https://cursor.com/docs/subagents | official | Verifier and isolated context pattern | High |
| Cursor Bugbot | Cursor | https://cursor.com/docs/bugbot | official | PR bug/security/code-quality review | High |
| GitHub Copilot coding agent | GitHub | https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent | official | Autonomous branch-based coding in own environment | High |
| OpenAPI Specification | OpenAPI Initiative | https://swagger.io/specification/ | official | HTTP API contract and discovery | High |
| JSON Schema | JSON Schema | https://json-schema.org/specification | official | JSON validation vocabulary and schemas | High |
| Protocol Buffers | Google | https://protobuf.dev/programming-guides/proto3/ | official | Interface definition language and generated bindings | High |
| gRPC introduction | gRPC | https://grpc.io/docs/what-is-grpc/introduction/ | official | RPC service definition using Protobuf | High |
| AsyncAPI | AsyncAPI Initiative | https://www.asyncapi.com/ | official | Event-driven API specification | High |
| CloudEvents | CNCF | https://cloudevents.io/ | official | Common event metadata format | High |
| RFC 9457 Problem Details | IETF | https://www.rfc-editor.org/info/rfc9457 | standard | Machine-readable HTTP API errors | High |
| PostgreSQL constraints | PostgreSQL | https://www.postgresql.org/docs/current/ddl-constraints.html | official | DB constraints as data integrity enforcement | High |
| Flyway versioned migrations | Redgate Flyway | https://documentation.red-gate.com/fd/versioned-migrations-273973333.html | official | Ordered, checksum-protected migrations | High |
| OpenTelemetry docs | OpenTelemetry | https://opentelemetry.io/docs/ | official | Traces, metrics, logs instrumentation framework | High |
| OpenTelemetry semantic conventions | OpenTelemetry | https://opentelemetry.io/docs/concepts/semantic-conventions/ | official | Stable telemetry attribute conventions | High |
| OWASP API Security Top 10 | OWASP | https://owasp.org/API-Security/editions/2023/en/0x00-header/ | official | API risk taxonomy: object auth, resource limits, etc. | High |
| Pact docs | Pact | https://docs.pact.io/ | official | Consumer-driven contract testing | High |
| Testcontainers | Testcontainers | https://testcontainers.com/guides/introducing-testcontainers/ | official | Integration tests with real dependencies in containers | High |
| Buf breaking/lint | Buf | https://buf.build/docs/breaking/ | official | Protobuf lint and breaking-change detection | High |
| Spectral | Stoplight | https://stoplight.io/open-source/spectral | official | OpenAPI/AsyncAPI/JSON Schema linting | Medium |
| ArchUnit | ArchUnit | https://www.archunit.org/ | official | Executable architecture tests for Java | Medium |
| dependency-cruiser | OSS | https://github.com/sverweij/dependency-cruiser | secondary | Dependency boundary checks for JS/TS | Medium |
| SLSA | OpenSSF | https://slsa.dev/ | official | Supply-chain integrity and provenance | High |
| OpenSSF Scorecard | OpenSSF | https://scorecard.dev/ | official | Automated security posture checks | High |
| Bazel hermeticity | Bazel | https://bazel.build/basics/hermeticity | official | Hermetic and reproducible build principle | Medium |

---

## 3. Agentic Backend Architecture Principles

### Principle 1: Service equals agent work unit

Why it matters for agents: A service directory gives the agent a bounded search space and a rollback unit. If API specs, migrations, tests, and source live together, the agent can reason locally.

Concrete rule:

- A service should own its `api/`, `proto/`, `asyncapi/`, `src/`, `migrations/`, `tests/`, and `AGENTS.md`.
- Cross-service imports are forbidden except through public clients, generated contracts, or documented shared packages.

Anti-pattern:

- Global `src/controllers`, `src/services`, `src/repositories`, and `migrations` shared across all services with unclear ownership.

Example:

```text
services/payments/
  api/
  proto/
  asyncapi/
  src/
  migrations/
  tests/
  AGENTS.md
```

Source: https://developers.openai.com/codex/guides/agents-md

### Principle 2: Transport layer is thin

Why it matters for agents: Agents often start from endpoint files. Fat controllers hide business logic and side effects in high-churn files.

Concrete rule:

- Handler <= 100 LOC.
- Handler performs context extraction, auth identity extraction, input validation, use-case call, and response mapping.
- Handler does not open DB transactions, call repositories directly, publish events directly, or call external SDKs.

Anti-pattern:

- `createPaymentController.ts` validates request, computes pricing, writes SQL, calls Stripe, retries on error, sends email, and logs metrics.

Preferred:

```text
transport/http/createPaymentController.ts
  -> application/commands/createPayment.ts
  -> domain/rules/*
  -> ports/*
  -> adapters/*
```

Source: https://swagger.io/specification/

### Principle 3: Domain core is pure

Why it matters for agents: Pure domain code can be tested without services, containers, credentials, or network. It is the safest place for business change.

Concrete rule:

- `domain/` imports only domain modules and pure shared utilities.
- No framework, DB, queue, cache, HTTP client, env, logger, telemetry, clock, random, or adapter imports.

Anti-pattern:

```ts
// domain/Subscription.ts
import { redis } from '../adapters/redis';
import { stripe } from '../adapters/stripe';
```

Preferred:

```ts
// domain/rules/canRenewSubscription.ts
export function canRenewSubscription(input: CanRenewSubscriptionInput): boolean {
  return input.status === 'active' && input.balanceCents >= input.priceCents;
}
```

Source: https://developers.openai.com/codex/prompting

### Principle 4: Application layer owns orchestration

Why it matters for agents: Transaction boundaries, authorization, idempotency, and outbox semantics need one obvious place. If orchestration is spread across controller, repository, and job consumer, agents miss critical side effects.

Concrete rule:

- One use-case file per command/query.
- Application use case depends on domain and ports, not concrete adapters.
- Application owns transaction, authz call, idempotency, outbox, and audit decision.

Anti-pattern:

- A repository method checks authorization and publishes events as a hidden side effect.

Example:

```text
application/commands/createInvoice.ts
ports/InvoiceRepository.ts
ports/PaymentGateway.ts
ports/EventPublisher.ts
```

Source: https://docs.stripe.com/api/idempotent_requests

### Principle 5: Ports define dependencies; adapters implement them

Why it matters for agents: Ports let agents unit-test application logic with fakes and integration-test adapters separately.

Concrete rule:

- `ports/` contains interfaces such as `PaymentGateway`, `InvoiceRepository`, `Clock`, and `IdempotencyStore`.
- `adapters/` contains concrete Stripe, Postgres, Redis, queue, email, and metrics implementations.

Anti-pattern:

```ts
// application/createPayment.ts
import Stripe from 'stripe';
import { prisma } from '../db/prisma';
```

Preferred:

```ts
export async function createPayment(input: Input, deps: {
  paymentGateway: PaymentGateway;
  repository: PaymentRepository;
  idempotencyStore: IdempotencyStore;
  clock: Clock;
}) { ... }
```

Source: https://testcontainers.com/guides/introducing-testcontainers/

### Principle 6: Contracts are versioned artifacts

Why it matters for agents: Agents otherwise infer request shapes from handler code and may silently break clients.

Concrete rule:

- REST contracts live in OpenAPI.
- RPC contracts live in `.proto` files.
- Event contracts live in AsyncAPI or event schemas.
- Contract lint and breaking-change checks run in CI.

Anti-pattern:

- API docs generated after deployment and never checked against code.

Source:

- https://swagger.io/specification/
- https://protobuf.dev/programming-guides/proto3/
- https://www.asyncapi.com/

### Principle 7: Database schema is executable domain constraint

Why it matters for agents: Application-only invariants can be bypassed by bugs, multiple writers, concurrent retries, or future agents. DB constraints create hard stops.

Concrete rule:

- Put not-null, uniqueness, foreign key, enum/check, and valid-state constraints in migrations whenever possible.
- Application tests should assert both business behavior and DB enforcement.

Anti-pattern:

- "There can only be one active subscription" enforced only in service code.

Preferred:

```sql
CREATE UNIQUE INDEX subscription_one_active_per_customer
ON subscriptions (customer_id)
WHERE status = 'active';
```

Source: https://www.postgresql.org/docs/current/ddl-constraints.html

### Principle 8: Migrations are immutable history

Why it matters for agents: Editing applied migrations causes local, staging, and production to diverge.

Concrete rule:

- Once a migration reaches a shared/persistent environment, do not edit it.
- Add a new forward migration for fixes.
- Use expand-migrate-contract for risky schema changes.

Anti-pattern:

- Editing `V031__create_users.sql` after staging has applied it.

Source: https://documentation.red-gate.com/fd/versioned-migrations-273973333.html

### Principle 9: Async messages are APIs

Why it matters for agents: Event payloads and queue jobs are often invisible contracts. An agent changing a field may break a producer or consumer in another repo.

Concrete rule:

- Every event/job has schema, version, owner, producer, consumer, retry policy, timeout, idempotency key, and DLQ behavior.

Anti-pattern:

```ts
queue.publish('user.updated', JSON.stringify(user));
```

Preferred:

```ts
publishUserUpdatedV1(UserUpdatedV1Schema.parse(payload));
```

Source:

- https://cloudevents.io/
- https://www.asyncapi.com/

### Principle 10: Observability is acceptance surface

Why it matters for agents: Backend failures often appear only in logs, traces, metrics, and production behavior. Agents need stable telemetry contracts to verify runtime effects.

Concrete rule:

- New endpoints/jobs define or reuse span names, metric names, log fields, error classifications, and correlation ID propagation.
- Avoid high-cardinality metric labels.

Anti-pattern:

- `logger.info('stuff happened')` with no request ID, tenant ID policy, or error classification.

Source:

- https://opentelemetry.io/docs/
- https://opentelemetry.io/docs/concepts/semantic-conventions/

### Principle 11: Security is a tested boundary

Why it matters for agents: Security defects often come from missing object authorization, resource limits, and validation in edge cases.

Concrete rule:

- Object-level authorization lives in application/policy layer.
- Input validation happens at transport boundary.
- Secrets and PII logging are centrally controlled.
- Add negative tests for authz and resource limits.

Anti-pattern:

- Controller trusts `accountId` from request body without checking that the authenticated user can access it.

Source: https://owasp.org/API-Security/editions/2023/en/0x00-header/

---

## 4. Backend Contract Design Guidelines

### 4.1 What must be contractized

| Contract | Recommended artifact | Validation/check | Agent rule |
|---|---|---|---|
| REST API | `api/openapi.yaml` or checked-in `openapi.json` | Spectral lint, OpenAPI diff, request/response validator | Do not add endpoint without API contract update. |
| gRPC/RPC | `proto/<service>/v1/*.proto` | `buf lint`, `buf breaking`, generated code | Do not renumber or reuse fields; reserve removed fields. |
| Events/messages | `asyncapi/*.yaml`, CloudEvents schema, schema registry | AsyncAPI validation, producer/consumer contract tests | Queue payloads are public APIs. |
| HTTP errors | RFC 9457 Problem Details or typed envelope | Error contract tests | Do not invent per-handler error JSON. |
| DB schema | SQL migrations, ORM schema, constraints | Migration dry-run, schema diff, integration tests | DB invariants belong in migrations. |
| Stored JSON/JSONB | JSON Schema, Zod, language schema | Runtime parse before use | No `as Type` on persisted JSON. |
| Idempotency | Contract file per mutation/job | Replay/dedupe tests | Retried mutations must be safe. |
| External service client | Port interface + adapter + fixture | Pact, fake provider, integration test | No SDK call outside adapter. |
| Config/env | `config/schema.*` | Boot-time validation | No direct `process.env` outside config adapter. |
| Secrets | Secret key contract and source | Secret scanning, no defaults for production secrets | No secret names scattered in code. |
| Authorization policy | `policies/*` or policy-as-code | Policy tests and authz matrix | No object-level auth hidden in controller. |
| Telemetry | `observability/contracts.*` | Span/metric/log assertions | No free-form metric names in business code. |
| Batch/job payload | `jobs/contracts/*` | Payload schema, retry, idempotency tests | No unversioned job payload. |
| CLI/admin command | `commands/contracts/*` | Arg parser tests, dry-run tests | Admin tools are production APIs. |

### 4.2 Runtime validation choice

Use this rule:

- Compile-time types only: allowed inside trusted pure domain code.
- Runtime schema required: HTTP body/query/path, webhooks, queue messages, DB JSON/JSONB, config/env, external API responses, CLI args, file input, user-provided IDs.
- Generated type plus runtime validation: preferred for OpenAPI, Protobuf, JSON Schema, and event schemas.
- DB constraint: required for invariants that must survive concurrency, retries, and multiple writers.

### 4.3 External, persisted, and untrusted data rules

- Never cast raw JSON to an internal type without validation.
- Validate at the boundary and map to domain types.
- Keep raw DTOs separate from domain entities.
- Persisted JSON must include `version` and migration/default handling.
- Webhook payloads must verify signature/origin before schema parse is trusted.
- External API adapters must translate provider-specific errors into typed internal errors.

### 4.4 Example: API and error contract

```ts
// services/payments/src/contracts/errors.ts
import { z } from 'zod';

export const ProblemDetailsSchema = z.object({
  type: z.string().url().optional(),
  title: z.string(),
  status: z.number().int(),
  detail: z.string().optional(),
  instance: z.string().optional(),
  code: z.enum([
    'payment.insufficient_funds',
    'payment.duplicate_idempotency_key',
    'payment.not_found',
    'payment.unauthorized'
  ])
});

export type ProblemDetails = z.infer<typeof ProblemDetailsSchema>;
```

```ts
// services/payments/src/contracts/createPayment.ts
import { z } from 'zod';

export const CreatePaymentRequestSchema = z.object({
  customerId: z.string().uuid(),
  amountCents: z.number().int().positive(),
  currency: z.enum(['usd', 'eur', 'gbp']),
  idempotencyKey: z.string().min(16).max(128)
});

export const CreatePaymentResponseSchema = z.object({
  paymentId: z.string().uuid(),
  status: z.enum(['authorized', 'requires_action', 'failed'])
});

export type CreatePaymentRequest = z.infer<typeof CreatePaymentRequestSchema>;
export type CreatePaymentResponse = z.infer<typeof CreatePaymentResponseSchema>;
```

---

## 5. Backend File and Module Decomposition Rules

### 5.1 Hard thresholds

| File/module | Limit | Refactor action |
|---|---:|---|
| HTTP controller / route handler | 80-100 LOC | Extract use case, mapper, validator, policy. |
| gRPC handler / GraphQL resolver | 100 LOC | Extract use case and response mapper. |
| Queue consumer entrypoint | 100 LOC | Extract job handler and idempotency wrapper. |
| Application use case | 200 LOC | Split command/query, transaction, policy, domain calls. |
| Domain service/rule file | 200 LOC | Extract pure functions or state machine. |
| Repository adapter | 250 LOC | Split query object, mapper, transaction helper. |
| External API adapter | 250 LOC | Split client, mapper, retry, error translator. |
| Migration file | 300 LOC | Split DDL, backfill, and constraint validation phases. |
| Test file | 400 LOC | Split by behavior, contract, or use case. |
| Any non-generated source | 500 LOC hard fail | Allowlist only with owner, reason, expiry. |

### 5.2 Smells that require immediate split

- Handler opens a DB transaction.
- Handler calls an external SDK.
- Domain imports framework or infrastructure.
- Repository computes business rules.
- Application use case builds HTTP response.
- Queue consumer mutates DB without idempotency.
- Job payload has no schema/version.
- Migration mixes schema change, long backfill, and destructive drop.
- Config read happens outside `config/`.
- Error codes are duplicated strings.
- Raw SQL appears outside repository/query adapter.
- Tests depend on wall clock or external network without fixture.
- New endpoint lacks OpenAPI update.
- Protobuf change lacks breaking check.
- Event payload change lacks schema update.

### 5.3 Backend boundary model

```text
transport/
  Owns protocol concerns:
  - HTTP/gRPC/GraphQL/queue parsing
  - headers/status/cookies/metadata
  - request context
  - auth identity extraction
  - response mapping

application/
  Owns use-case orchestration:
  - transaction boundary
  - authorization call
  - idempotency
  - domain calls
  - ports
  - outbox
  - audit event

domain/
  Owns pure business truth:
  - entities
  - value objects
  - invariants
  - policies
  - state transitions
  - calculations

ports/
  Owns dependency contracts:
  - repository interfaces
  - external gateway interfaces
  - queue publisher interfaces
  - clock/random interfaces
  - email interfaces

adapters/
  Owns side effects:
  - SQL/ORM
  - Redis/cache
  - external APIs
  - queue SDK
  - filesystem/S3
  - telemetry exporter

migrations/
  Owns persisted schema evolution:
  - DDL
  - constraints
  - indexes
  - data backfills
  - compatibility phases

tests/
  Owns verification:
  - unit
  - contract
  - integration
  - migration
  - architecture
  - security
```

---

## 6. Backend Reference Architecture

```text
services/
  payments/
    AGENTS.md
    README.md

    api/
      openapi.yaml
      spectral.yaml
      examples/
        create-payment.request.json
        create-payment.response.json

    proto/
      payments/v1/payment.proto
      buf.yaml
      buf.gen.yaml

    asyncapi/
      payment-events.yaml
      examples/
        payment-authorized.v1.json

    src/
      transport/
        http/
          paymentController.ts
          errorMapper.ts
          requestContext.ts
        grpc/
          paymentGrpcHandler.ts
        queue/
          paymentWebhookConsumer.ts

      application/
        commands/
          createPayment.ts
          capturePayment.ts
          refundPayment.ts
        queries/
          getPayment.ts
        policies/
          canRefundPayment.ts
        transactions/
          withPaymentTransaction.ts
        idempotency/
          paymentIdempotency.ts

      domain/
        model/
          Payment.ts
          PaymentId.ts
          Money.ts
        rules/
          calculateRefund.ts
          transitionPaymentState.ts
        events/
          PaymentAuthorized.ts
        errors/
          PaymentDomainError.ts

      ports/
        PaymentRepository.ts
        PaymentGateway.ts
        EventPublisher.ts
        Clock.ts
        IdempotencyStore.ts

      adapters/
        db/
          sql/
            paymentQueries.ts
          PaymentPostgresRepository.ts
          paymentRowMapper.ts
        stripe/
          StripePaymentGateway.ts
          stripeErrorMapper.ts
        queue/
          PaymentEventPublisher.ts
        idempotency/
          RedisIdempotencyStore.ts
        observability/
          paymentTelemetry.ts

      config/
        envSchema.ts
        serviceConfig.ts

      observability/
        spanNames.ts
        metricNames.ts
        logFields.ts

    migrations/
      V001__create_payments.sql
      V002__add_payment_idempotency.sql
      V003__add_payment_state_check.sql

    tests/
      unit/
        domain/
        application/
      contract/
        openapi/
        pact/
        events/
      integration/
        postgres/
        redis/
        stripe-fake/
      migration/
        migrate-clean-db.test.ts
        migrate-existing-db.test.ts
      architecture/
        boundaries.test.ts
      security/
        authorization.test.ts
        resource-limits.test.ts
      fixtures/
```

### Layer rules

| Layer | Allowed | Forbidden |
|---|---|---|
| `transport` | Protocol parse/map, context, status codes | Domain rules, SQL, external SDK calls, retry logic |
| `application` | Use cases, transactions, authz, idempotency, ports | HTTP response types, framework decorators |
| `domain` | Pure model/rules/errors/events | DB, queue, HTTP, config, clock, random, logger |
| `ports` | Interfaces/protocols | Implementation details |
| `adapters` | Concrete side effects | Domain decisions not delegated to domain/application |
| `migrations` | Schema evolution | Application logic hidden in SQL files |
| `config` | Env/schema/defaults | Direct secret reads outside config |
| `observability` | Names, attributes, wrappers | PII and free-form metric names |
| `tests/contract` | Boundary compatibility | Replacing all integration tests |
| `tests/integration` | Real dependency behavior | Only in-memory proof for DB-heavy code |

---

## 7. Backend Verification and Acceptance Harness

### 7.1 Required command surface

```json
{
  "scripts": {
    "verify": "npm run check:static && npm run check:contracts && npm run test:unit && npm run test:integration && npm run test:migrations && npm run check:architecture && npm run check:security",
    "check:static": "tsc --noEmit && eslint .",
    "check:contracts": "npm run check:openapi && npm run check:proto && npm run check:events",
    "check:openapi": "spectral lint services/payments/api/openapi.yaml && oasdiff breaking base.yaml services/payments/api/openapi.yaml",
    "check:proto": "buf lint && buf breaking --against '.git#branch=main'",
    "check:events": "asyncapi validate services/payments/asyncapi/payment-events.yaml",
    "test:unit": "vitest run tests/unit",
    "test:integration": "vitest run tests/integration",
    "test:migrations": "vitest run tests/migration",
    "check:architecture": "node scripts/check-backend-boundaries.mjs && node scripts/check-giant-files.mjs",
    "check:security": "node scripts/check-forbidden-patterns.mjs"
  }
}
```

Adjust the commands to the repo's language and build system, but preserve the semantics.

### 7.2 Backend verification matrix

| Check | What it catches | Agent acceptance rule |
|---|---|---|
| Static analysis | Type drift, invalid imports, dead code | Must pass before done. |
| OpenAPI lint | Malformed or inconsistent API specs | Endpoint changes update and lint spec. |
| OpenAPI breaking diff | Accidental client breakage | Breaking changes require explicit approval. |
| Buf lint/breaking | Protobuf style and compatibility issues | No proto change without Buf checks. |
| AsyncAPI/event validation | Broken queue/event contracts | Event changes require schema and producer/consumer tests. |
| Unit tests | Domain/use-case correctness | Domain rule changes require tests. |
| Contract tests | Consumer/provider compatibility | External boundary changes require contract tests. |
| Integration tests | DB/cache/queue/external-adapter behavior | Adapter changes require realistic dependency tests. |
| Migration dry-run | Schema drift and migration failure | Clean DB and fixture DB migrations pass. |
| Architecture tests | Domain purity and ports/adapters boundaries | No forbidden imports. |
| Security tests | Authz, input, resource limits | High-risk endpoint requires negative tests. |
| Observability tests | Missing spans/metrics/log fields | New endpoint/job emits required telemetry. |

### 7.3 Architecture check example

```js
// scripts/check-backend-boundaries.mjs
import fs from 'node:fs/promises';
import fg from 'fast-glob';

const files = await fg(['services/*/src/**/*.{ts,tsx,js,jsx}', '!**/*.generated.*']);

const rules = [
  {
    name: 'domain must be pure',
    file: /\/src\/domain\//,
    forbidden: [
      /from ['\"](express|fastify|koa|@nestjs\/)/,
      /from ['\"](pg|mysql2|mongoose|prisma|typeorm|sequelize)/,
      /from ['\"](ioredis|redis|bullmq|amqplib|kafkajs)/,
      /from ['\"](axios|node-fetch|got)/,
      /\bprocess\.env\b/,
      /\bDate\.now\(\)/,
      /\bMath\.random\(\)/
    ]
  },
  {
    name: 'transport must not access infrastructure directly',
    file: /\/src\/transport\//,
    forbidden: [
      /from ['\"].*\/adapters\/db\//,
      /from ['\"].*\/adapters\/stripe\//,
      /from ['\"](pg|mysql2|prisma|typeorm|sequelize|axios|got|node-fetch)/
    ]
  },
  {
    name: 'application must depend on ports, not adapters',
    file: /\/src\/application\//,
    forbidden: [
      /from ['\"].*\/adapters\//,
      /from ['\"](express|fastify|koa|@nestjs\/)/
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

### 7.4 Giant-file check example

```js
// scripts/check-giant-files.mjs
import fs from 'node:fs/promises';
import fg from 'fast-glob';

const files = await fg([
  'services/**/*.{ts,tsx,js,jsx,py,go,java,kt,rs,sql}',
  '!**/*.generated.*',
  '!**/node_modules/**',
  '!**/vendor/**'
]);

const limits = [
  { name: 'controller', test: (f) => /\/transport\/(http|grpc|queue)\//.test(f), max: 100 },
  { name: 'application use case', test: (f) => /\/application\//.test(f), max: 200 },
  { name: 'domain', test: (f) => /\/domain\//.test(f), max: 200 },
  { name: 'adapter', test: (f) => /\/adapters\//.test(f), max: 250 },
  { name: 'migration', test: (f) => /\/migrations\/.*\.sql$/.test(f), max: 300 },
  { name: 'default', test: () => true, max: 300 }
];

let failed = false;

for (const file of files) {
  const text = await fs.readFile(file, 'utf8');
  const loc = text.split('\n').length;
  const limit = limits.find((l) => l.test(file));

  if (loc > limit.max) {
    failed = true;
    console.error(`${file}: ${loc} LOC > ${limit.max} for ${limit.name}. Split this file.`);
  }
}

if (failed) process.exit(1);
```

---

## 8. Backend Instruction Files

### 8.1 Repo `AGENTS.md` template

```md
# AGENTS.md - Backend Service Repository Contract

This repository is maintained by human engineers and AI coding agents. Treat this file as the service architecture contract.

## First steps

1. Read this file.
2. Read package/build scripts.
3. Identify the service, endpoint, job, or adapter that owns the requested change.
4. Read relevant contracts before editing:
   - OpenAPI
   - Protobuf
   - AsyncAPI/event schemas
   - DB migrations/schema
   - error contracts
   - idempotency contracts
5. Make a small plan before touching multiple layers.
6. Run verification before claiming done.

## Architecture

Each service should use this shape:

- `api/`: REST/OpenAPI contracts and examples.
- `proto/`: gRPC/Protobuf contracts.
- `asyncapi/`: event-driven contracts.
- `src/transport/`: HTTP/gRPC/queue entrypoints. Thin only.
- `src/application/`: use cases, transactions, authorization, idempotency, outbox orchestration.
- `src/domain/`: pure business model, rules, state transitions, domain errors/events.
- `src/ports/`: interfaces for external dependencies.
- `src/adapters/`: DB, cache, queue, external API, filesystem, telemetry implementations.
- `src/config/`: env/config schema and loader.
- `src/observability/`: metric names, span names, log fields, instrumentation wrappers.
- `migrations/`: append-only database migrations.
- `tests/`: unit, contract, integration, migration, architecture, security.

## Transport rules

Transport files must only:

- extract request context
- authenticate request identity
- validate request shape
- call one application use case
- map result/error to protocol response

Transport files must not:

- contain business rules
- open DB transactions
- write SQL
- call external SDKs
- publish queue messages directly
- implement retry/idempotency logic
- exceed 100 LOC without splitting

## Domain rules

Files under `src/domain/` must be pure.

Forbidden in domain:

- web frameworks
- ORM/database clients
- queue/cache SDKs
- HTTP clients
- filesystem
- `process.env`
- global clock/random
- telemetry exporters
- adapters

Use injected ports, clocks, and IDs through application services.

## Application rules

Application use cases own:

- authorization calls
- transaction boundaries
- idempotency
- domain orchestration
- outbox/event emission decision
- audit decision
- port calls

Application must depend on `ports/`, not concrete `adapters/`.

## Adapter rules

Adapters own side effects:

- SQL/ORM
- Redis/cache
- S3/filesystem
- external API SDKs
- queue SDKs
- email/SMS
- telemetry exporters

Adapters must translate raw external data into validated domain/application types.

## Contract rules

Contractize all boundaries:

- REST endpoints: OpenAPI
- RPC: Protobuf
- events/messages: AsyncAPI or event schema
- errors: Problem Details or typed error envelope
- DB schema: migrations and constraints
- persisted JSON: schema + version
- jobs: payload schema + retry + DLQ + idempotency
- config/env: runtime schema
- external APIs: port + adapter + fixture/contract test
- telemetry: stable names and attributes

Do not duplicate contract strings. Import constants or generated types.

## Database rules

- Migrations are append-only after reaching shared environments.
- Do not edit applied migrations. Add a new migration.
- Prefer expand-migrate-contract for risky schema changes.
- Use DB constraints for invariants that must survive concurrency or multiple writers.
- Test migrations on clean DB and fixture DB.

## Idempotency rules

Every retried mutation must define:

- idempotency key source
- dedupe storage
- replay/no-op behavior
- TTL
- conflict behavior when same key has different payload
- tests for retry and duplicate delivery

Required for payments, resource creation, webhook processing, queue consumers, email/SMS sends, and quota/credit mutations.

## Security rules

- Validate all untrusted inputs at the boundary.
- Object-level authorization must be explicit in application/policy layer.
- Do not trust client-provided tenant/user/account IDs without authz check.
- Do not log secrets, tokens, credentials, or unnecessary PII.
- Add negative tests for authz/resource-limit changes.
- Use centralized secret/config loading.

## Observability rules

New endpoints/jobs must add or reuse:

- span name
- metric name
- structured log fields
- correlation/request ID propagation
- error classification
- high-cardinality field policy

Do not create metric names as inline strings in business code.

## File limits

- transport entrypoint: max 100 LOC
- application use case: max 200 LOC
- domain service/rule file: max 200 LOC
- adapter: max 250 LOC
- migration: max 300 LOC
- any non-generated source file: max 500 LOC hard cap

## Verification

Default:

```bash
make verify
```

or repository equivalent.

Do not claim done unless verification passes or exact blockers are documented.
```

### 8.2 Cursor rule templates

```md
---
description: Backend service architecture boundaries for transport, application, domain, ports, adapters, migrations, and tests.
globs: services/**/*.{ts,tsx,js,jsx,py,go,java,kt,rs}
alwaysApply: false
---

# Backend Architecture Boundaries

- Transport files are thin protocol adapters only.
- Application files orchestrate use cases, transactions, authz, idempotency, ports, and outbox.
- Domain files are pure business logic and must not import frameworks, DB, queue, cache, HTTP clients, env, clock, random, or adapters.
- Ports define dependency interfaces.
- Adapters implement side effects.
- Migrations own persisted schema changes.
- Tests must match the changed boundary.

Never bypass ports to call adapters from domain/application.
```

```md
---
description: Backend verification and done definition.
alwaysApply: true
---

# Backend Verification

Do not claim done until relevant verification passes.

Default command:

```bash
make verify
```

Targeted checks:

- domain/application change: unit tests
- endpoint change: OpenAPI lint/diff + endpoint tests
- proto change: buf lint + buf breaking
- event change: event schema validation + producer/consumer tests
- DB change: migration dry-run + integration tests
- adapter change: integration or contract tests
- authz/security change: negative security tests
- observability change: telemetry assertions

Document exact blockers if a check cannot run.
```

---

## 9. Backend Architecture Refactor Goal Prompt

```md
You are refactoring this backend/service repository to make it safer for long-term AI coding agent maintenance.

## Read first

- AGENTS.md
- service-local AGENTS.md
- package/build scripts
- API contracts
- proto files
- AsyncAPI/event schemas
- DB migrations
- current tests
- architecture checks

## Goal

Refactor the target backend area so that:

- transport handlers are thin
- business rules live in pure domain modules
- application use cases own orchestration
- external dependencies are behind ports/adapters
- API/event/RPC/error/storage/config contracts are explicit
- DB invariants are represented in migrations/constraints where possible
- retried mutations and queue consumers are idempotent
- observability names/fields are stable
- verification commands pass

## Non-goals

- Do not change product behavior unless explicitly required.
- Do not introduce breaking API/event/proto changes unless explicitly required.
- Do not edit applied migrations.
- Do not add dependencies without documenting why.
- Do not modify unrelated services.

## Required plan

Before editing, produce:

1. Current boundary map.
2. Violations found.
3. Target file structure.
4. Contracts to update.
5. Tests to add or run.
6. Migration/idempotency/security risks.
7. Rollback strategy.

## Acceptance

Complete only when:

- no handler contains business logic
- domain has no framework/DB/queue/cache/network/config imports
- public contracts are updated and checked
- DB migrations are append-only and tested
- retried mutations are idempotent
- jobs/events have schemas and retry/DLQ/idempotency policy
- security and observability are covered
- verification passes or blockers are documented with command output
```

---

## 10. Counter-Evidence and Caveats

- Instruction files are guidance, not enforcement. Hard backend boundaries need lint rules, architecture tests, hooks, and CI.
- Contract tests do not replace all integration tests. Use contract tests for boundary expectations and integration tests for real DB/cache/queue behavior.
- API specs can drift if generated but not checked. Treat specs as source of truth or validate them against implementation.
- Strict migration immutability needs a documented exception process for local-only migrations.
- Hermetic or reproducible builds add tooling overhead. The minimum is pinned dependencies, clean CI, and deterministic verification commands.
- Review bots and verifier agents should supplement required CI checks, not replace them.

---

## Final Mental Model

```text
thin transport
+ pure domain
+ application orchestration
+ ports/adapters
+ versioned API/event/DB/error contracts
+ idempotent side effects
+ observability/security gates
+ deterministic integration verification
= backend repo that coding agents can safely maintain
```
