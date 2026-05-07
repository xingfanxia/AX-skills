---
name: apple-pdf
description: Default PDF generator. Render markdown, notes, or reports as professionally formatted PDFs with SF typography and clean layout. Use this whenever the user asks to "generate a PDF", "create a PDF", "make a PDF", or "convert to PDF" from any text or markdown source.
user-invocable: true
---

# Apple Style PDF Renderer

Convert markdown documents into beautifully formatted PDFs with Apple's design language — SF font stack, 8px-based spacing, 1.8 line height, and restrained gray palette.

## When to Use

Trigger phrases: "generate pdf", "create pdf", "make pdf", "convert to pdf", "生成PDF", "apple pdf", "apple style", "render pdf", "styled pdf", "export as pdf", "pretty pdf", "格式化PDF", "苹果风格"

Use this skill when the user wants to generate, create, or convert text/markdown to PDF. This is the DEFAULT pdf generation skill. This includes:
- Any "generate a PDF from X" request
- Rendering notes, docs, or reports as styled PDFs
- Exporting markdown for WeChat/clipboard as self-contained HTML
- Batch converting markdown files to styled PDFs

Note: For manipulating existing PDFs (extract text, merge, split, fill forms), use the `pdf` skill instead.

## Workflow

1. Identify the markdown file(s) the user wants to render
2. Ask about preferences if not specified: theme (light/dark), font size, watermark
3. Run the renderer script via Bash
4. Report the output path to the user

## Usage

Run the renderer script with `uv run`:

```bash
uv run ~/.claude/skills/apple-pdf/apple_pdf.py <input.md> [options]
```

### All Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output`, `-o` | `<input_stem>.pdf` | Output PDF path |
| `--theme` | `light` | Theme mode: `light` or `dark` |
| `--font-size` | `medium` | Font size preset: `small` (14px), `medium` (16px), `large` (18px) |
| `--watermark-text` | *(none)* | Add document watermark with this text |
| `--watermark-style` | `stamp` | Watermark style: `stamp`, `pattern`, `diamond` |
| `--watermark-opacity` | `0.15` | Watermark opacity (0.1 to 0.5) |
| `--avatar-url` | *(none)* | URL for image avatar watermark (small circle above images) |
| `--page-size` | `A4` | Page size: `A4`, `Letter`, `Legal` |
| `--margin` | `20mm` | Page margins (CSS value) |
| `--title` | *(auto from H1)* | Document title for PDF metadata |
| `--html-only` | `false` | Output styled HTML instead of PDF |
| `--no-page-breaks` | `false` | Disable automatic page breaks before H1 |

### Examples

```bash
# Basic — markdown to Apple-styled PDF
uv run ~/.claude/skills/apple-pdf/apple_pdf.py doc.md

# Dark mode, large font
uv run ~/.claude/skills/apple-pdf/apple_pdf.py doc.md --theme dark --font-size large

# With confidential watermark
uv run ~/.claude/skills/apple-pdf/apple_pdf.py doc.md --watermark-text "CONFIDENTIAL" --watermark-style pattern

# Custom output path
uv run ~/.claude/skills/apple-pdf/apple_pdf.py doc.md -o ~/Downloads/styled-report.pdf

# HTML output (for clipboard/WeChat)
uv run ~/.claude/skills/apple-pdf/apple_pdf.py doc.md --html-only -o styled.html

# Batch: render all .md files in a directory
for f in docs/*.md; do uv run ~/.claude/skills/apple-pdf/apple_pdf.py "$f"; done
```

## Design System

The renderer faithfully ports the Apple design language:

- **Fonts**: SF Pro Text/Display → system fallback stack with PingFang SC for CJK
- **Colors**: Light (#1d1d1f primary, #f5f5f7 surface) / Dark (#dcddde primary, #202020 bg)
- **Accent**: Obsidian purple #7f6df2
- **Spacing**: 8px base grid (4/8/16/24/32/48)
- **Headings**: 3-level hierarchy — H1 full underline, H2 short underline, H3 plain
- **Line height**: 1.8 with 0.02em letter spacing
- **Code**: SF Mono with pink/purple inline, surface-bg blocks
- **Tables**: Alternating row colors, subtle borders
- **Blockquotes**: 3px left border, secondary text color
- **HR**: Invisible spacer (24px margin, no line)

## Implementation Notes

- Uses `markdown` library with `fenced_code`, `tables`, `codehilite`, `toc`, `footnotes` extensions
- All styles are **inline** (no external CSS) — output is self-contained and paste-friendly
- PDF generation uses **WeasyPrint** for accurate CSS rendering
- Page breaks: H1 forces break (except first), avoid break inside paragraphs/lists/code
- Images referenced by relative path are resolved relative to the input markdown file
