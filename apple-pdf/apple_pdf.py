# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "markdown>=3.5",
#   "playwright>=1.40",
#   "pygments>=2.17",
# ]
# ///
"""
Apple Style PDF Renderer
Converts markdown to Apple-styled PDF with SF typography, restrained palette,
and professional layout. Ported from obsidian-apple-style plugin.
"""
import argparse
import html
import re
import sys
import urllib.parse
from pathlib import Path

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from playwright.sync_api import sync_playwright

# ─────────────────────────────────────────────────────────────────────────────
# Apple Theme — ported from themes/apple-theme.js
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "light": {
        "primary": "#1d1d1f",
        "secondary": "#6e6e73",
        "tertiary": "#86868b",
        "background": "#ffffff",
        "surface": "#f5f5f7",
        "divider": "#d2d2d7",
        "accent": "#7f6df2",
        "code_text": "#c7254e",
        "code_bg": "#f5f5f7",
        "link": "#7f6df2",
        "blockquote_border": "#7f6df2",
        "blockquote_bg": "#f5f5f7",
        "table_header_bg": "#f5f5f7",
        "table_alt_bg": "#fafafa",
        "table_border": "#e5e5ea",
    },
    "dark": {
        "primary": "#dcddde",
        "secondary": "#b3b3b3",
        "tertiary": "#7f7f7f",
        "background": "#202020",
        "surface": "#1e1e1e",
        "divider": "#3a3a3c",
        "accent": "#7f6df2",
        "code_text": "#e096d3",
        "code_bg": "#2c2c2e",
        "link": "#a594f9",
        "blockquote_border": "#7f6df2",
        "blockquote_bg": "#2c2c2e",
        "table_header_bg": "#2c2c2e",
        "table_alt_bg": "#262626",
        "table_border": "#3a3a3c",
    },
}

FONT_SIZES = {
    "small": {"base": 14, "h1": 22, "h2": 18, "h3": 16, "code": 12, "caption": 12},
    "medium": {"base": 16, "h1": 28, "h2": 21, "h3": 18, "code": 14, "caption": 13},
    "large": {"base": 18, "h1": 32, "h2": 24, "h3": 20, "code": 16, "caption": 14},
}

FONTS = {
    "text": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif",
    "code": "'SF Mono', Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
    "display": "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif",
}


def get_style(tag: str, font_size: str, theme: str) -> str:
    """Return inline CSS string for a given HTML tag. Ported from AppleTheme.getStyle()."""
    c = COLORS[theme]
    fs = FONT_SIZES[font_size]

    styles = {
        "section": f"font-family: {FONTS['text']}; font-size: {fs['base']}px; color: {c['primary']}; line-height: 1.8; letter-spacing: 0.02em; background-color: {c['background']}; max-width: 100%; margin: 0 auto; padding: 0;",
        "h1": f"font-family: {FONTS['display']}; font-size: {fs['h1']}px; font-weight: 700; color: {c['primary']}; letter-spacing: -0.3px; margin: 48px 0 24px 0; padding-bottom: 12px; border-bottom: 1px solid {c['divider']}; line-height: 1.3;",
        "h2": f"font-family: {FONTS['display']}; font-size: {fs['h2']}px; font-weight: 600; color: {c['primary']}; letter-spacing: -0.2px; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid {c['divider']}; display: inline-block; line-height: 1.4;",
        "h3": f"font-family: {FONTS['display']}; font-size: {fs['h3']}px; font-weight: 500; color: {c['primary']}; margin: 24px 0 12px 0; line-height: 1.4;",
        "h4": f"font-family: {FONTS['display']}; font-size: {fs['base'] + 1}px; font-weight: 500; color: {c['secondary']}; margin: 20px 0 8px 0; line-height: 1.4;",
        "h5": f"font-family: {FONTS['display']}; font-size: {fs['base']}px; font-weight: 500; color: {c['secondary']}; margin: 16px 0 8px 0; line-height: 1.4;",
        "h6": f"font-family: {FONTS['display']}; font-size: {fs['base'] - 1}px; font-weight: 500; color: {c['tertiary']}; margin: 16px 0 8px 0; line-height: 1.4; text-transform: uppercase; letter-spacing: 0.05em;",
        "p": f"margin: 0 0 12px 0; line-height: 1.8; color: {c['primary']};",
        "a": f"color: {c['link']}; text-decoration: none; border-bottom: 1px solid transparent;",
        "strong": f"font-weight: 600; color: {c['primary']};",
        "em": f"font-style: italic; color: {c['primary']};",
        "blockquote": f"margin: 16px 0; padding: 12px 16px; border-left: 3px solid {c['blockquote_border']}; background-color: {c['blockquote_bg']}; border-radius: 0 8px 8px 0; color: {c['secondary']};",
        "ul": f"margin: 8px 0 16px 0; padding-left: 24px; color: {c['primary']};",
        "ol": f"margin: 8px 0 16px 0; padding-left: 24px; color: {c['primary']};",
        "li": f"margin: 4px 0; line-height: 1.8; color: {c['primary']};",
        "code": f"font-family: {FONTS['code']}; font-size: {fs['code']}px; color: {c['code_text']}; background-color: {c['code_bg']}; padding: 2px 6px; border-radius: 4px;",
        "pre": f"font-family: {FONTS['code']}; font-size: {fs['code']}px; background-color: {c['code_bg']}; border-radius: 8px; padding: 16px; margin: 16px 0; overflow-x: auto; line-height: 1.6; color: {c['primary']};",
        "hr": f"border: none; margin: 24px 0;",
        "table": f"width: 100%; border-collapse: collapse; margin: 16px 0; font-size: {fs['base'] - 1}px;",
        "thead": f"background-color: {c['table_header_bg']};",
        "th": f"padding: 10px 14px; text-align: left; font-weight: 600; color: {c['primary']}; border-bottom: 2px solid {c['table_border']}; font-size: {fs['base'] - 1}px;",
        "td": f"padding: 10px 14px; border-bottom: 1px solid {c['table_border']}; color: {c['primary']}; font-size: {fs['base'] - 1}px;",
        "img": f"max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0;",
        "figure": f"margin: 16px 0; text-align: center;",
        "figcaption": f"font-size: {fs['caption']}px; color: {c['tertiary']}; margin-top: 8px;",
    }
    return styles.get(tag, "")


# ─────────────────────────────────────────────────────────────────────────────
# Markdown → Styled HTML conversion
# ─────────────────────────────────────────────────────────────────────────────

def inject_inline_styles(html_content: str, font_size: str, theme: str) -> str:
    """Post-process HTML to inject inline styles on every tag."""
    tag_map = [
        "h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote",
        "ul", "ol", "li", "table", "thead", "th", "td", "hr",
        "pre", "img", "figure", "figcaption", "a", "strong", "em",
    ]
    result = html_content

    for tag in tag_map:
        style = get_style(tag, font_size, theme)
        if not style:
            continue
        # Replace opening tags, preserving existing attributes
        result = re.sub(
            rf'<{tag}(\s|>)',
            lambda m: f'<{tag} style="{style}"{m.group(1)}',
            result,
        )

    # Handle inline <code> vs <pre><code> — code inside pre should not have inline code style
    code_style = get_style("code", font_size, theme)
    result = re.sub(
        r'<code(\s|>)',
        lambda m: f'<code style="{code_style}"{m.group(1)}',
        result,
    )
    # Remove inline code styling from code blocks (inside <pre>)
    pre_code_style = f"font-family: {FONTS['code']}; font-size: {FONT_SIZES[font_size]['code']}px; background: none; padding: 0; border-radius: 0; color: inherit;"
    result = re.sub(
        r'(<pre[^>]*>)\s*<code[^>]*>',
        lambda m: f'{m.group(1)}<code style="{pre_code_style}">',
        result,
    )

    # Table row alternating colors
    c = COLORS[theme]
    row_idx = [0]

    def alt_row(m):
        row_idx[0] += 1
        bg = c["table_alt_bg"] if row_idx[0] % 2 == 0 else "transparent"
        return f'<tr style="background-color: {bg};">'

    # Reset counter for each table
    parts = result.split("<tbody>")
    new_parts = [parts[0]]
    for part in parts[1:]:
        row_idx[0] = 0
        part = re.sub(r'<tr>', alt_row, part)
        new_parts.append(part)
    result = "<tbody>".join(new_parts)

    return result


def convert_images_to_absolute(html_content: str, base_dir: Path) -> str:
    """Convert relative image paths to absolute file:// URLs."""
    def replace_src(m):
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:", "file://")):
            return m.group(0)
        abs_path = (base_dir / src).resolve()
        if abs_path.exists():
            return f'src="file://{urllib.parse.quote(str(abs_path))}"'
        return m.group(0)

    return re.sub(r'src="([^"]*)"', replace_src, html_content)


def wrap_images_in_figures(html_content: str, font_size: str, theme: str, avatar_url: str | None = None) -> str:
    """Wrap standalone <img> tags in <figure> with optional avatar."""
    fig_style = get_style("figure", font_size, theme)
    cap_style = get_style("figcaption", font_size, theme)

    def wrap_img(m):
        img_tag = m.group(0)
        alt_match = re.search(r'alt="([^"]*)"', img_tag)
        alt = alt_match.group(1) if alt_match else ""

        avatar_html = ""
        if avatar_url:
            avatar_html = f'<img src="{avatar_url}" style="width: 24px; height: 24px; border-radius: 50%; margin-right: 6px; vertical-align: middle;" />'

        caption = f'<figcaption style="{cap_style}">{avatar_html}{html.escape(alt)}</figcaption>' if alt else ""
        return f'<figure style="{fig_style}">{img_tag}{caption}</figure>'

    # Only wrap images that are NOT already inside a figure
    # Split on <figure> to avoid wrapping images that are already in figures
    result = re.sub(r'(<img[^>]+>)', wrap_img, html_content)
    return result


def markdown_to_styled_html(
    md_text: str,
    font_size: str = "medium",
    theme: str = "light",
    base_dir: Path | None = None,
    avatar_url: str | None = None,
) -> str:
    """Convert markdown text to fully styled HTML with inline styles."""
    # Parse markdown
    extensions = [
        "fenced_code",
        "tables",
        "toc",
        "footnotes",
        "attr_list",
        "def_list",
        "md_in_html",
        CodeHiliteExtension(css_class="highlight", guess_lang=True, use_pygments=False),
    ]
    md = markdown.Markdown(extensions=extensions)
    body_html = md.convert(md_text)

    # Inject inline styles
    body_html = inject_inline_styles(body_html, font_size, theme)

    # Handle images
    if base_dir:
        body_html = convert_images_to_absolute(body_html, base_dir)
    body_html = wrap_images_in_figures(body_html, font_size, theme, avatar_url)

    # Wrap in section
    section_style = get_style("section", font_size, theme)
    return f'<section style="{section_style}">{body_html}</section>'


# ─────────────────────────────────────────────────────────────────────────────
# Watermark generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_watermark_css(text: str, style: str, opacity: float) -> str:
    """Generate CSS for document watermark overlay."""
    escaped = html.escape(text)

    if style == "stamp":
        return f"""
        .watermark {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 72px;
            font-family: {FONTS['display']};
            font-weight: 700;
            color: rgba(0, 0, 0, {opacity});
            white-space: nowrap;
            pointer-events: none;
            z-index: 9999;
            border: 4px solid rgba(0, 0, 0, {opacity});
            padding: 16px 32px;
            border-radius: 12px;
        }}
        """
    elif style == "pattern":
        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='260' height='140'><text transform='rotate(-35 130 70)' x='50%' y='50%' font-size='16' font-family='SF Pro Display, Helvetica Neue, Arial, sans-serif' fill='rgba(0,0,0,{opacity})' text-anchor='middle' dominant-baseline='middle'>{escaped}</text></svg>"""
        encoded = urllib.parse.quote(svg)
        return f"""
        .watermark {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: url("data:image/svg+xml,{encoded}");
            background-repeat: repeat;
            pointer-events: none;
            z-index: 9999;
        }}
        """
    elif style == "diamond":
        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><line x1='90' y1='0' x2='180' y2='90' stroke='rgba(0,0,0,{opacity * 0.3})' stroke-width='0.5' stroke-dasharray='4,4'/><line x1='180' y1='90' x2='90' y2='180' stroke='rgba(0,0,0,{opacity * 0.3})' stroke-width='0.5' stroke-dasharray='4,4'/><line x1='90' y1='180' x2='0' y2='90' stroke='rgba(0,0,0,{opacity * 0.3})' stroke-width='0.5' stroke-dasharray='4,4'/><line x1='0' y1='90' x2='90' y2='0' stroke='rgba(0,0,0,{opacity * 0.3})' stroke-width='0.5' stroke-dasharray='4,4'/><text x='90' y='20' font-size='10' font-family='Arial,sans-serif' fill='rgba(0,0,0,{opacity})' text-anchor='middle'>{escaped}</text><text x='90' y='95' font-size='10' font-family='Arial,sans-serif' fill='rgba(0,0,0,{opacity})' text-anchor='middle'>{escaped}</text></svg>"""
        encoded = urllib.parse.quote(svg)
        return f"""
        .watermark {{
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: url("data:image/svg+xml,{encoded}");
            background-repeat: repeat;
            pointer-events: none;
            z-index: 9999;
        }}
        """
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Full HTML document generation
# ─────────────────────────────────────────────────────────────────────────────

def build_html_document(
    styled_body: str,
    title: str = "Document",
    theme: str = "light",
    page_size: str = "A4",
    margin: str = "20mm",
    no_page_breaks: bool = False,
    watermark_text: str | None = None,
    watermark_style: str = "stamp",
    watermark_opacity: float = 0.15,
) -> str:
    """Build a complete HTML document ready for PDF conversion."""
    c = COLORS[theme]

    page_break_css = ""
    if not no_page_breaks:
        page_break_css = """
        h1 { page-break-before: always; }
        h1:first-of-type { page-break-before: avoid; }
        p, li, figure, pre, blockquote { page-break-inside: avoid; }
        h1, h2, h3 { page-break-after: avoid; }
        """

    watermark_css = ""
    watermark_html = ""
    if watermark_text:
        watermark_css = generate_watermark_css(watermark_text, watermark_style, watermark_opacity)
        if watermark_style == "stamp":
            watermark_html = f'<div class="watermark">{html.escape(watermark_text)}</div>'
        else:
            watermark_html = '<div class="watermark"></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        @page {{
            size: {page_size};
            margin: {margin};
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: {c['background']};
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        section {{
            max-width: 100%;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        {page_break_css}
        {watermark_css}
    </style>
</head>
<body>
    {watermark_html}
    {styled_body}
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def extract_title(md_text: str) -> str:
    """Extract title from first H1 heading."""
    match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    return match.group(1).strip() if match else "Document"


def main():
    parser = argparse.ArgumentParser(
        description="Apple Style PDF Renderer — convert markdown to beautifully formatted PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s doc.md                                    # Basic PDF
  %(prog)s doc.md --theme dark --font-size large     # Dark mode, large
  %(prog)s doc.md --watermark-text "CONFIDENTIAL"    # With watermark
  %(prog)s doc.md --html-only -o styled.html         # HTML output
        """,
    )
    parser.add_argument("input", help="Input markdown file path")
    parser.add_argument("-o", "--output", help="Output file path (default: <input>.pdf)")
    parser.add_argument("--theme", choices=["light", "dark"], default="light", help="Theme mode (default: light)")
    parser.add_argument("--font-size", choices=["small", "medium", "large"], default="medium", help="Font size preset (default: medium)")
    parser.add_argument("--watermark-text", help="Document watermark text")
    parser.add_argument("--watermark-style", choices=["stamp", "pattern", "diamond"], default="stamp", help="Watermark style (default: stamp)")
    parser.add_argument("--watermark-opacity", type=float, default=0.15, help="Watermark opacity 0.1-0.5 (default: 0.15)")
    parser.add_argument("--avatar-url", help="Image avatar URL for figure captions")
    parser.add_argument("--page-size", default="A4", help="Page size: A4, Letter, Legal (default: A4)")
    parser.add_argument("--margin", default="20mm", help="Page margins as CSS value (default: 20mm)")
    parser.add_argument("--title", help="Document title (default: auto from first H1)")
    parser.add_argument("--html-only", action="store_true", help="Output styled HTML instead of PDF")
    parser.add_argument("--no-page-breaks", action="store_true", help="Disable automatic page breaks before H1")

    args = parser.parse_args()

    # Read input
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
    elif args.html_only:
        output_path = input_path.with_suffix(".html")
    else:
        output_path = input_path.with_suffix(".pdf")

    # Auto-detect title
    title = args.title or extract_title(md_text)

    # Convert markdown to styled HTML
    styled_body = markdown_to_styled_html(
        md_text,
        font_size=args.font_size,
        theme=args.theme,
        base_dir=input_path.parent,
        avatar_url=args.avatar_url,
    )

    # Build full HTML document
    full_html = build_html_document(
        styled_body,
        title=title,
        theme=args.theme,
        page_size=args.page_size,
        margin=args.margin,
        no_page_breaks=args.no_page_breaks,
        watermark_text=args.watermark_text,
        watermark_style=args.watermark_style,
        watermark_opacity=args.watermark_opacity,
    )

    # Output
    if args.html_only:
        output_path.write_text(full_html, encoding="utf-8")
        print(f"HTML written to {output_path}")
    else:
        # Use Playwright for PDF — same approach as Obsidian plugin (Electron printToPDF)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(full_html, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format=args.page_size,
                margin={"top": args.margin, "right": args.margin, "bottom": args.margin, "left": args.margin},
                print_background=True,
            )
            browser.close()
        print(f"PDF written to {output_path}")


if __name__ == "__main__":
    main()
