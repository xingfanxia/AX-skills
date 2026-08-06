# AGENTS.md

## Scope

This repository contains the public Process Launcher package. Keep the code and docs generic enough for public release.

## Privacy Rules

- Do not commit `config/launcher.yaml`, `.env`, `logs/`, or runtime output.
- Keep real machine paths, real job names, private domains, real emails, and secrets out of tracked files.
- Use `config/launcher.example.yaml` for generic examples only.
- Keep private aliases and job recipes in a separate workspace overlay, not in this repository.

## Development

- Install with `uv pip install -e '.[dev]'` inside the project virtual environment.
- Use `process_launcher` as the Python import namespace.
- Use `process-launcher` or `python -m process_launcher` as the CLI entrypoint.
- Preserve the `live_integration` marker semantics. Live tests may start a real launcher process on port `7976`; default unit tests should not require an already running service.
- Do not weaken or delete tests to make packaging changes pass.
