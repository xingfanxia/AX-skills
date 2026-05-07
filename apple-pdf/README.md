# apple-pdf

> Markdown / notes / reports → professionally formatted PDFs with SF typography. Default PDF generator for AX's workflow.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Convert any markdown file or text into a clean, Apple-style PDF — SF Pro Display headings, SF Pro Text body, sensible margins, syntax-highlighted code, and table support out of the box. No CSS to fight with.

## When to use

- "Generate a PDF of this report"
- "Make a PDF from this markdown"
- "Export these meeting notes as PDF"

## Install

```bash
git clone https://github.com/xingfanxia/AX-skills.git ~/AX-skills
ln -sf ~/AX-skills/apple-pdf ~/.claude/skills/apple-pdf

# Optional: install codex side too
ln -sf ~/AX-skills/apple-pdf ~/.codex/skills/apple-pdf
```

The Python entrypoint uses only stdlib + `reportlab` (auto-installed via PEP 723 `uv` shebang).

## Usage

The agent invokes the skill automatically when you say "make this a PDF" or "generate a PDF". For direct invocation:

```bash
python ~/.claude/skills/apple-pdf/apple_pdf.py input.md -o output.pdf
```

See [SKILL.md](./SKILL.md) for full options and the prompting contract.
