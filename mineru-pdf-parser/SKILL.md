---
name: mineru-pdf-parser
description: |
  Parse complex PDFs (and images / DOCX / PPTX / XLSX) into LLM-ready
  Markdown + structured JSON with MinerU — tables, formulas, and reading
  order preserved. Use for research ingestion, RAG data prep, and academic
  papers / technical reports where layout fidelity matters. Triggers:
  "PDF解析", "PDF转Markdown", "提取PDF表格/公式", "parse this PDF",
  "MinerU". NOT for reading a few pages (just read them), or for
  merge/split/rotate/fill/OCR-in-place — use the `pdf` skill for those.
---

# MinerU PDF Parser

Wraps the [MinerU](https://github.com/opendatalab/MinerU) CLI (PyPI `mineru`, v3.4.0 verified 2026-07). CLI-only — there is no stable `from mineru import MinerU` Python API; drive it via the `mineru` command.

**Why MinerU over the alternatives**: PyMuPDF4LLM is AGPL and Marker is GPL — both license blockers for most codebases. MarkItDown's `pdfminer.six` backend loses heading levels (~0% retention on structured docs). Docling (MIT, ~3s/page on CPU) is the legitimate fallback if MinerU install fails.

## Install

```bash
uv pip install -U "mineru[core]"        # persistent install (Python 3.10–3.13, macOS 14+)
uvx --from "mineru[core]" mineru --help # ad-hoc, no install (~106 pkgs resolved on first run)
```

## Usage

```bash
mineru -p <input> -o <output_dir>          # file OR directory; pdf/image/docx/pptx/xlsx
mineru -p paper.pdf -o out -b pipeline     # no GPU → pipeline (pure-CPU safe)
mineru -p big.pdf -o out -s 0 -e 49        # page range (0-based) for large files
```

## Backend selection (`-b`, default `hybrid-engine`)

| Backend | Trait | Pick when |
|---|---|---|
| `pipeline` | Most general, runs pure-CPU | No GPU, simple/text PDFs, OCR langs via `-l` |
| `hybrid-engine` | Default; high accuracy, local compute | GPU/Apple-Silicon box; `--effort high` adds image/chart analysis |
| `vlm-engine` | VLM high accuracy, local compute | GPU box, formula/table-dense papers |
| `vlm-http-client` / `hybrid-http-client` | Offload to OpenAI-compatible server via `-u <url>` | Remote vLLM/SGLang/LMDeploy deployment |

Other flags: `-m auto|txt|ocr` (pipeline/hybrid only), `-f/-t` formula/table toggles (default on), `--effort medium|high` (hybrid only; medium skips image/chart analysis).

## First run — model download

Models auto-download from HuggingFace on first parse (large; looks like a hang — tell the user). If HF is blocked: `export MINERU_MODEL_SOURCE=modelscope`. Pre-fetch with `mineru-models-download -s auto -m all`. CUDA/MPS acceleration is auto-attempted on Linux/macOS.

## Output (per input file, under the output dir)

- `{name}.md` — the LLM-ready Markdown
- `{name}_content_list.json` — structured blocks in reading order (RAG-friendly)
- `{name}_middle.json` — intermediate detail (debugging)
- `{name}_layout.pdf` (+ `{name}_span.pdf`, pipeline only) — visual QC of layout/reading order
- exact file set varies by backend; see [output docs](https://opendatalab.github.io/MinerU/reference/output_files/)

## Pitfalls

| Pitfall | Handling |
|---|---|
| First run "hangs" | It's the model download — pre-announce; pre-fetch with `mineru-models-download` |
| No GPU, default backend crawls | Force `-b pipeline` (the only pure-CPU-safe backend) |
| Scanned PDFs | Quality tracks scan clarity; retry once with another backend, then report honestly — don't silently deliver garbage |
| Hundreds of pages | Memory pressure — parse in `-s/-e` ranges or split the file first |
| Heading-swallow | A section title rendered as emphasized text inside a table cell isn't detected as a layout heading — consecutive identical `##` headers appear with no separating context. Recover by cross-referencing an anchor value (account number, opening balance, figure caption) against the source page |

Before declaring done: confirm `{name}.md` + `{name}_content_list.json` exist (report actual paths), and spot-check 1–2 pages against the original for lost/garbled tables and formulas. Also check:
- **Compression ratio** — a text-born PDF should compress ~5-10x into Markdown; a scan should barely shrink. A ratio outside that range means OCR silently no-op'd or the parse collapsed.
- **Dedupe** — if two differently-named PDFs produce byte-identical or equal-length Markdown, md5 the source files before reporting — MinerU does not dedupe inputs.

**Mandatory human review** (don't deliver unchecked): complex math (LaTeX export is lossy), archival needs that preserve page numbers/headers/footers (parsers strip them), and legal/financial/medical documents (sample back-check against the source PDF is required, not optional).

<!-- Pitfall rows adapted from staruhub/ClaudeSkills (MIT); all CLI facts verified against `mineru --help` v3.4.0 + https://opendatalab.github.io/MinerU/ -->
