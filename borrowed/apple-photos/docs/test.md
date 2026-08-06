# Test Strategy

## Default Offline Suite

The offline test runner (`pytest`) must run decoupled from the macOS environment. It must not query real Photos libraries, trigger TCC authorization prompts, open the Photos app, or call the native Swift helper.

### Test Categories
- **Unit Tests**: Cover filtering, search parsing, resource-set digests, pixel similarity metrics, dimension and decode rejection, manifest canonicalization, TOCTOU safety, TTY inputs, HMAC tokens, expiration, and replay prevention.
- **Contract Tests**: Validate assets, manifests, receipts, events, authorization claims, backups, and pixel-authorizing evidence against JSON schemas. Pixel tests cover threshold ceilings, byte-identical rejection, source drift, PhotoKit ownership mismatch, planner attestation, and candidate/keeper role safety. Bridge tests simulate helper outputs, structured per-item import evidence, malformed JSON, protocol mismatches, timeouts, stderr noise, and non-zero exit codes.
- **Integration Tests**: Inject synthetic readers and fake process bridges to verify read/search/filter/dump/backup, import duplicate reuse, partial coverage blocks, missing-placeholder sibling evidence, postcondition failures, delete workflows, stale asset rejections, and uncertainty handling.

## Static Safety Checks

- **Code Quality**: Ruff validation must pass on all source files and test suites.
- **Write Prevention**: Automated scanning rejects SQLite imports outside the replay ledger, rejects Photos database locators globally, and uses AST enumeration to permit only the replay ledger's exact literal SQL statements. Dynamic SQL, `executescript`, unrecognized SQLite execution APIs, and commands like `DELETE` or `VACUUM` fail the check.
- **Privacy Scan**: Scans Git publication candidates for generic user-home paths, absolute `file://` links, email addresses, and secret locator markers.
- **CLI Independence**: CLI help menus must render cleanly without macOS PhotoKit dependencies.

## Opt-In Live Tests

To execute live tests, set `APPLE_PHOTOS_ENABLE_LIVE_TESTS=1`, compile the helper locally, and run within a dedicated virtual machine or disposable macOS account. Live tests must never alter the System Photo Library setting or target a production library.

Verification requires:
- Read-only metadata probe and resource SHA-256 retrieval.
- Single-resource import with second-run duplicate reuse.
- Post-import album membership verification.
- Interactive confirmation flow for planning, authorization, delete execution, and postcondition validation.

## Completion Standard

An iteration is complete when Ruff, the complete Python and Swift suites, package builds, and publication scans pass, and unexecuted live steps are recorded in [working.md](working.md). Current exact test counts belong in the verification log rather than this policy.
