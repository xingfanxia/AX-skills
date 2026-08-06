---
name: tavily-skill
description: >-
  CLI-based Tavily web search and URL extraction with stable JSON envelope.
  Writes full payload to disk and returns a ~500-byte status on stdout, so
  multi-search sessions don't bloat context. Use for deep-research / narrative-research (project-scoped: ax-blog)
  / long-form writing / any session with 5+ searches where token economy matters.
  For one-shot quick lookups whose result you consume immediately and discard,
  use the `mcp__tavily__*` MCP tools instead (lower latency, zero subprocess).
disable-model-invocation: true
---

# Tavily Skill (CLI)

Wraps `tavily-python` SDK as a CLI with two subcommands: `search` and `extract`.
Default mode writes the full payload to `tmp/tavily/<auto-name>.json` under the
current working directory and prints a compact status JSON on stdout. Pass
`--stdout` for inline payload consumption.

## When to use this vs `mcp__tavily__*` MCP

| Scenario | Tool |
|---|---|
| One-off quick search, consume result immediately | **MCP** (`mcp__tavily__tavily_search`) — already loaded, no subprocess |
| Multi-search research session (≥ 5 calls) | **this skill** — file mode keeps context lean |
| Want to grep/diff/replay search history later | **this skill** — files persist |
| Running from CI / cron / non-Claude-Code agent | **this skill** — works anywhere with bash |
| `/deep-research`, `/narrative-research`, `/wandian-writer` long-form research | **this skill** — autofit; 30+ searches a session |

Token math: one Tavily search w/ `raw_content=markdown` is ~25K tokens. MCP keeps that in context every turn. File mode keeps ~125 tokens (status only) — agent reads the file only when the specific result is needed.

## Invocation

Canonical command (absolute path, CWD-independent):

```bash
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill <subcommand> [args]
```

The `tavily-skill` console script is installed in the venv. API key is loaded
from `~/.claude/skills/tavily-skill/.env` (TAVILY_API_KEY; symlink → `~/creds/claude/tavily.env`).

### File mode (default — recommended for multi-search sessions)

```bash
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill search "your query" --output ./tmp/tavily/search-<slug>.json
```

Pass `--output <path>` explicitly so files land under the *current project's*
`tmp/tavily/` rather than the skill's own dir. Without `--output`, the file
lands relative to whatever CWD you invoked from.

stdout returns:

```json
{
  "command": "search",
  "status": "ok",
  "output_mode": "file",
  "output_path": "tmp/tavily/...",
  "payload_bytes": 48815,
  "summary": {"result_count": 3, "image_count": 0, "has_answer": false},
  "payload_schema": { ... }
}
```

To consume a result: `Read` the `output_path`.

### Stdout mode (one-shot)

```bash
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill search "your query" --stdout
```

Returns full payload on stdout. Use for one-off lookups where you immediately consume the answer.

### URL extract

```bash
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill extract https://example.com/article --stdout
~/.claude/skills/tavily-skill/.venv/bin/tavily-skill extract https://a.com https://b.com --query "topic" --chunks-per-source 3 --output ./tmp/tavily/extract.json
```

## Parameter reference

### `search`

| Param | Description | Default |
|---|---|---|
| `query` | Search query (positional) | required |
| `--max-results` | 1–20 | 6 |
| `--search-depth` | `basic` / `advanced` / `fast` / `ultra-fast` | `advanced` |
| `--topic` | `general` / `news` / `finance` | `general` |
| `--time-range` | `day` / `week` / `month` / `year` | — |
| `--start-date` / `--end-date` | `YYYY-MM-DD` | — |
| `--include-domain` / `--exclude-domain` | Repeat for multiple | — |
| `--answer` | `off` / `basic` / `advanced` | `off` |
| `--raw-content` | `off` / `markdown` / `text` | `markdown` |
| `--country` | Boost by country | — |
| `--timeout` | seconds | 60 |
| `--images` / `--no-images` | Enable/disable image results | off |
| `--image-descriptions` / `--no-image-descriptions` | LLM descriptions for images | off |
| `--stdout` | Print full payload to stdout | off |
| `--output` | Write payload to specific path | `tmp/tavily/<auto>.json` |

### `extract`

| Param | Description | Default |
|---|---|---|
| `urls...` | 1–20 URLs (positional) | required |
| `--extract-depth` | `basic` / `advanced` | `advanced` |
| `--format` | `markdown` / `text` | `markdown` |
| `--query` | Keep only chunks relevant to query | — |
| `--chunks-per-source` | Chunks retained per URL | — |
| `--images` / `--no-images` | Enable/disable image extraction | off |
| `--favicon` | Return favicon URLs | off |
| `--timeout` | seconds | 60 |
| `--stdout` | Print full payload to stdout | off |
| `--output` | Write payload to specific path | `tmp/tavily/<auto>.json` |

## Defaults

- `search_depth="advanced"`, `max_results=6`, `topic="general"`, `answer="off"`, `raw_content="markdown"`
- Images disabled by default — enable explicitly for visual topics or report-writing where you need accompanying images
- API key resolution order: `TAVILY_API_KEY` env var → `ONEPASSWORD_TAVILY_REFERENCE` env var (resolved via `op read`)

## Output envelope

All payloads are normalized to `{command, input, data}` to insulate against
tavily-python SDK changes. `data` matches Tavily SDK shape (`results`, `images`,
`answer`, `response_time`, `request_id`, `usage`).

## Image guidance

Off by default — most research workflows don't consume `data.images` and they
inflate payload size. Enable explicitly when:
- Writing an external report / newsletter that needs images
- Topic is inherently visual (UI, hardware, satellite, document samples, news event photos)
- You need image search specifically, not text retrieval
