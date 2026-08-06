# Apple Photos Skill

[![CI](https://github.com/grapeot/apple-photos-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/grapeot/apple-photos-skill/actions/workflows/ci.yml)

`apple-photos` is a live-unverified alpha. Offline contracts and synthetic mutation paths are tested, but live import and delete operations are unvalidated against real System Photo Libraries. Do not run mutation commands on production libraries.

The Python 3.11+ CLI uses `osxphotos==0.76.1` exclusively for read-only metadata access. Mutations execute via a native Swift PhotoKit helper targeting the System Photo Library only, without writing to the Photos SQLite database. Uncertain post-dispatch outcomes are journaled as `outcome_unknown` rather than reported as safe-to-retry failures.

## Status

Core offline contracts, planners, public-CLI authorization gates, process bridge, and fake end-to-end paths are implemented. Live PhotoKit interaction requires compiling the macOS helper and is strictly opt-in. See [Known Live Gaps](#known-live-gaps).

## Installation

Install core development dependencies:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

On macOS, install the pinned read adapter:

```bash
uv pip install -e '.[dev,photos]'
```

Locate and build the native helper on macOS:

```bash
HELPER_SOURCE="$(apple-photos helper-source --format path)"
swift build -c release --package-path "$HELPER_SOURCE"
export APPLE_PHOTOS_HELPER="$HELPER_SOURCE/.build/release/PhotoKitHelper"
```

The JSON output of `apple-photos helper-source` exposes build arguments as a `build_argv` array to avoid path shell-quoting ambiguity.

Source distributions and wheels include the helper source, canonical skill, schemas, and architecture/test documents. A local Swift build is required; no signed native binary is distributed.

The native helper requires macOS Photos read/write authorization. The Python process separately requires read access to the target `.photoslibrary` directory.

## Safety Model

- **Reads**: Run against a user-specified `.photoslibrary` path.
- **Snapshots**: Plans bind to the System Photo Library's sorted PhotoKit asset-ID-set snapshot. Public PhotoKit does not expose library filesystem paths, so snapshot equality does not prove physical library identity.
- **Imports**: Plans enforce SHA-256 duplicate checks before staging. Execution requires `--manifest` and `--apply`. Items execute in individual PhotoKit transactions. The first transaction error or missing placeholder returns `outcome_unknown`, prevents every later item transaction, and marks those items `not_attempted_after_unknown`. Receipts preserve identifiers from earlier successful items, and the batch reports a non-retryable `partial` or `outcome_unknown` result without later mutations.
- **Deletions**: Move pixel-verified candidates to Recently Deleted; permanent erase or bypassing macOS confirmation is unsupported. Plans freeze candidate/keeper identifiers, pixel metrics, source bindings, and metadata. Applying requires `--manifest`, `--authorization-token`, and `--apply`.
- **Authorization**: Deletes require interactive TTY input of `DELETE <count> <digest-prefix>` to generate a 15-minute manifest-bound HMAC token, which is consumed in a local ledger before executing helper mutations.
- **Delete Batch Bound**: Each delete manifest is limited to 50 candidate/keeper pairs so native source hashing and PhotoKit preflight remain bounded by the authorization window. Split larger evidence sets into separately reviewed and authorized manifests.
- **Isolation**: The Python orchestrator and native helper both verify the planner attestation and human authorization HMAC. This prevents unsigned direct helper requests and local plan substitution; it is not a boundary against same-user processes that can read the local secret. macOS TCC and PhotoKit confirmation dialogs enforce system-level boundaries.
- **Namespaces**: `osxphotos_uuid` and `osxphotos_album_uuid` (reads) are distinct from `photokit_local_identifier` (mutations). Resolve mutation identifiers via `apple-photos asset mutation-list` and `apple-photos album mutation-list`.
- **Pixel Evidence**: `evidence compare-images` is the only supported deletion evidence. A report authorizes planning only when every byte-different, single-resource still-image pair has equal dimensions and passes the canonical pixel thresholds. Compound, partially available, and non-photo resource sets are rejected. SHA-256 binds each compared input to its candidate or keeper PhotoKit resource; the helper repeats this ownership check immediately before mutation, and hash equality is not a duplicate criterion.

## Read Examples

```bash
apple-photos doctor --capability read
apple-photos doctor --capability mutation
apple-photos library inspect --library ./Example.photoslibrary
apple-photos album list --library ./Example.photoslibrary --format jsonl
apple-photos asset search "sunset" --library ./Example.photoslibrary
apple-photos asset list --library ./Example.photoslibrary --limit 100
apple-photos asset mutation-list
apple-photos album mutation-list
apple-photos asset metadata asset-id-1 asset-id-2 --library ./Example.photoslibrary
apple-photos asset filter --filter filter.json --library ./Example.photoslibrary
apple-photos metadata dump --library ./Example.photoslibrary --format jsonl
apple-photos metadata backup --library ./Example.photoslibrary --output ./metadata-backup
```

`metadata backup` generates a checksummed metadata snapshot, not a media file or `.photoslibrary` directory backup.

## Pixel Deletion Evidence

Create a JSONL pair manifest:

```json
{"pair_id":"pair-0001","left":"./candidate.png","right":"./keeper.jpg","candidate_local_identifier":"candidate/L0/001","keeper_local_identifier":"keeper/L0/001"}
```

Run the default conservative comparison gate:

```bash
apple-photos evidence compare-images \
  --input-manifest ./pairs.jsonl \
  --output ./pixel-evidence.json
```

The default policy requires equal dimensions, RGB mean absolute error at or below 1%, per-pixel luminance mean absolute error at or below 1%, and the 99th percentile of each pixel's maximum RGB-channel error at or below 5%. Global average brightness alone is intentionally insufficient because unrelated images can share the same average brightness. High-bit-depth or unverifiable-bit-depth images, non-opaque alpha, animated images, multi-frame images, videos, oversized inputs, decode failures, and invalid ICC profiles fail closed. Any failed or rejected pair makes the command return exit code `8` after writing the complete report.

The report sets `delete_authorizing: true` only when every pair passes under thresholds no weaker than the defaults and the two source files are not byte-identical. Failed, rejected, or byte-identical pairs cannot enter a delete plan. SHA-256 values in the report establish frozen-input integrity and PhotoKit resource ownership; candidate and keeper hashes are not compared for equality.

## Mutation Planning

Plan imports:

```bash
apple-photos import plan ./incoming/example.jpg \
  --album-id album-local-id \
  --output ./import-plan.json
```

Apply imports:

```bash
apple-photos import apply --manifest ./import-plan.json --apply
```

Plan deletions:

```bash
apple-photos delete plan \
  --evidence-report ./pixel-evidence.json \
  --pair-manifest ./pairs.jsonl \
  --output ./delete-plan.json
```

Authorize and apply deletions:

```bash
apple-photos delete authorize \
  --manifest ./delete-plan.json \
  --output ./delete-plan.token

apple-photos delete apply \
  --manifest ./delete-plan.json \
  --authorization-token ./delete-plan.token \
  --apply
```

Run `apple-photos --help` or append `--help` to commands for details.

## Output Contracts

Read commands with `--format json` return a single JSON object. Commands with `--format jsonl` stream a `run_start` event, item records, and a `run_end` event. Mutation commands and errors return a single JSON object. Machine output goes to stdout; diagnostics and errors go to stderr. Schema contracts are defined in `schemas/`.

Exit codes:
- `2`: Usage/Schema Error
- `3`: Unsupported Capability
- `4`: Permission/Authorization Failure
- `5`: Stale Plan/Conflict
- `6`: Dependency/Read Failure
- `7`: Local Protocol/Bridge Error
- `8`: Partial/Integrity/Unknown Outcome
- `9`: Backend Transaction Failure
- `10`: Lock Contention

## Agent Skill Registration

Register `skills/apple_photos.md` in the agent workspace. Installed wheels bundle the skill under `apple_photos_cli/bundled/skills/` with resource maps targeting installed package paths.

## Development

```bash
source .venv/bin/activate
ruff check .
pytest
```

Offline tests use synthetic asset fixtures and a mock PhotoKit bridge. They do not read or mutate real Photos libraries.

## Known Live Gaps

- **Helper Access**: The Swift helper requires local compilation and macOS Photos access permissions.
- **Live Tests**: Requires manual opt-in.
- **Resource Scope**: Imports support single-resource images and videos only. Compound assets (e.g., Live Photos, RAW+JPEG, bursts, edited pairs, Shared Albums, and iCloud Shared Library mutations) fail closed.
- **Post-Mutation State**: Post-deletion visibility and iCloud consistency vary by macOS version. Uncertain outcomes report as `outcome_unknown` and are not retried.
- **System Confirmation**: PhotoKit deletion may block while macOS waits for a Photos confirmation window. Delete dispatch has no client deadline, so the process and library lock remain active until the prompt is answered. Stay present. If the process is externally interrupted or crashes, treat the outcome as unknown, never retry automatically, and reconcile all frozen identifiers read-only.
- **Library Tracking**: Public PhotoKit does not expose System Photo Library filesystem paths or physical library identifiers. Snapshots digest the sorted PhotoKit asset-ID set; this detects content drift but cannot distinguish copies/restorations sharing identical IDs.
