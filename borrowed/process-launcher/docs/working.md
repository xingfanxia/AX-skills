# Working Notes

## Repository Contract

Tracked files should be safe for public release. Runtime files are local-only:

- `config/launcher.yaml`
- `.env`
- `logs/`
- caches and build outputs

Use `config/launcher.example.yaml` and `.env.example` for fake examples. Keep private overlays outside the repository.

## Development Setup

```bash
uv venv
uv pip install -e '.[dev]'
```

Run the CLI with either entrypoint:

```bash
process-launcher start --config config/launcher.yaml
python -m process_launcher start --config config/launcher.yaml
```

## TCC-Aware Deployment

The launcher must be started from an interactive terminal session to act as a macOS TCC permission bridge. When deploying:

- Start from Terminal.app, iTerm2, or a tmux/zellij server that was itself started from one of those.
- Do not use cron, launchd, or PM2 as the launcher's parent for TCC-sensitive jobs.
- Verify TCC permissions manually after deployment (unit tests cannot simulate the GUI ancestry chain).
- If you need launchd scheduling with TCC access, wrap the job in a signed `.app` bundle with a stable bundle ID and the required entitlements, then have the bundle call the launcher API or launch a TCC-signed helper.

## Release Checklist

- Search tracked public files for private paths, real emails, private domains, and secrets.
- Run the unit test suite.
- Run the package entrypoint smoke check.
- Confirm `config/launcher.yaml`, `.env`, and `logs/` are ignored.
- Confirm docs describe the private overlay pattern rather than embedding private recipes.
