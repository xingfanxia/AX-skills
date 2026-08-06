# Architecture RFC

## System Architecture and Trust Domains

The architecture isolates operations across three boundaries:
1. **Read-Only Adapter**: Pinned `osxphotos==0.76.1` normalization. Performs read-only queries against selected libraries, with zero SQLite write or mutation capacity.
2. **Swift Helper Process**: A compiled native binary performing PhotoKit mutations against the System Photo Library via `PHPhotoLibrary.shared()`. AppleScript or GUI automation is prohibited.
3. **Python Orchestrator**: CLI argument parsing, asset/album filtering, deterministic manifest generation, pixel deletion evidence, HMAC-SHA-256 planning and deletion authorization, advisory locking, and JSON/JSONL formatting.

## Core Safety Invariants

- **SQLite Writes**: Prohibited.
- **Library Snapshots**: Manifests bind to the sorted PhotoKit asset-ID-set digest. This detects content-set drift; it does not verify physical library identity.
- **Delete Eligibility**: Supports byte-different, single-resource still-image pairs only. Compound, partially available, and non-photo resource sets fail closed. Every pair must have equal dimensions, RGB MAE <= 1%, luma MAE <= 1%, and per-pixel maximum-channel RGB P99 <= 5%. Byte-identical duplicate deletion is unsupported.
- **Evidence Binding**: Pixel comparison freezes each input, rejects unsupported bit depth and alpha, normalizes EXIF orientation and embedded ICC profiles to sRGB, and binds candidate/keeper PhotoKit identifiers. SHA-256 proves frozen-input integrity and ownership by a current PhotoKit resource; hash equality is never the eligibility criterion.
- **Execution Freeze**: Resolves operations using identifiers frozen in the manifest; search/filter routines are never rerun at execution time.
- **Deletions**: Require interactive TTY confirmation and a single-use HMAC token.
- **Delete Batch Bound**: A manifest contains at most 50 pairs. This bounds native resource export and hashing under the 15-minute authorization window; larger evidence sets require independent plans and tokens.
- **Preconditions**: Precondition failures abort the batch before calling native helper mutations.
- **Postconditions**: Unverifiable post-mutation states report as `partial` or `outcome_unknown` and return non-zero exit codes.
- **Import Transaction Isolation**: Payloads are validated as a batch. Execution uses ordered per-item PhotoKit transactions and stops at the first unknown outcome. Earlier successful identifiers remain available; every remaining item receives `not_attempted_after_unknown` evidence without invoking another PhotoKit transaction.

## Component Specifications

### OsxphotosReader
Lazily instantiates the adapter, maps `PhotoInfo` to `AssetRecord` entities, and exposes normalized metadata.

### PhotoKitProcessBridge
Spawns the native helper without a shell and communicates through JSON on stdin/stdout. Successful responses may include stderr diagnostics without invalidating the protocol result. Read and import operations use bounded client deadlines. Delete dispatch has no client deadline so a macOS confirmation wait cannot outlive the process-held library lock. Protocol errors, external interruption, and non-zero exits remain structured and conservative.

### Application Orchestration
Coordinates components using dependency injection. Integrates fakes for the reader and process bridge to run unit and integration tests offline.

## Cryptographic Manifests and Safety Gates

### Canonical Manifests
Uses UTF-8, sorted keys, compact separators, and no non-finite numbers. The `manifest_sha256` field is the lowercase hex digest of the manifest object with that field omitted.
- **Import Manifest**: Records source paths, album IDs, snapshots, UTIs, and resource SHA-256 hashes. Apply step rejects symlinks, non-regular files, or size mismatches.
- **Library Snapshot**: Contains sorted local-identifier digests, item counts, and diagnostic sentinels. Exposes no filesystem path or physical ID; `physical_identity_verified` remains false.
- **Delete Manifest**: Freezes candidate/keeper identifiers, policy, metrics, input hashes, report and pair-manifest digests, and live metadata. Planning replays comparison, verifies both inputs belong to single-resource PhotoKit assets, and adds a local HMAC evidence attestation. The helper independently verifies the canonical planner attestation and human token, validates candidate and keeper metadata, and re-hashes current PhotoKit resources immediately before mutation.

### Delete Authorization Tokens
A local 32-byte HMAC secret (mode `0600` in the fixed CLI state directory) signs both the complete canonical planner claims and the human authorization claims. The authorization binds the manifest digest, planner-claims digest, snapshot digest, count, timestamp, nonce, and CLI major version. The native helper resolves the account home through the user database, verifies both envelopes, and atomically consumes the nonce in its own fixed-path ledger before PhotoKit access. The Python ledger independently prevents CLI replay. Same-user processes that can read or replace fixed state remain outside the cryptographic isolation boundary.
Applying requires interactive confirmation of `DELETE <count> <digest-prefix>` and consumes the token nonce in a local SQLite ledger before helper execution.

## State and Locking

Locks bind to the library snapshot digest in the fixed `~/Library/Application Support/apple-photos-skill` state directory. The fixed location gives the native helper a stable HMAC trust anchor; caller-selected secret paths are prohibited. State files must never sit inside a `.photoslibrary` bundle. Locking coordinates this CLI only; delete operations repeat target validation at the native mutation boundary, immediately before the PhotoKit transaction. The helper also rechecks token expiry at that boundary.

Prior to dispatching helper mutations, the orchestrator writes a `commit_pending` journal. It logs `commit_reported` upon helper response and a receipt post-verification. Import responses preserve ordered terminal evidence: `created_identifier_known`, the first `outcome_unknown`, and `not_attempted_after_unknown` for every remaining item. The orchestrator journals these statuses immediately, propagates uncertainty to batch duplicates, and performs no later album or verification mutations. Delete helper errors carry a validated mutation phase: known native precommit rejection records `partial` with `not_attempted` items, while any commit attempt or ambiguous response records `outcome_unknown`. A failure between journal creation and helper dispatch overwrites the pending journal with terminal `not_attempted` evidence. Callers must reconcile read-only and must not auto-retry uncertain outcomes.

## Metadata Backup Architecture

Metadata backups construct snapshots in temporary directories. Data files are streamed, flushed, fsynced, and hashed before the manifest is written. The backup directory is then atomically renamed and tagged with a `COMPLETE` marker.

## Failure Semantics and Exit Codes

The CLI maps failures to these exit codes:
- `2`: Usage/Schema Error
- `3`: Unsupported Capability
- `4`: Permission/Authorization Failure
- `5`: Stale Plan/Conflict
- `6`: Dependency/Read Failure
- `7`: Local Protocol/Bridge Error
- `8`: Partial/Integrity/Unknown Outcome
- `9`: Backend Transaction Failure
- `10`: Lock Contention
