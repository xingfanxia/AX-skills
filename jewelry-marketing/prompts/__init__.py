"""Prompt registry for jewelry-marketing skill.

Exports:
- ANALYSIS_PROMPT: the product-analysis prompt used by Gemini
- MARKETING_BUILDERS: dict[str, callable] — 12 finished-product templates
- DESIGN_BUILDERS: dict[str, callable] — 8 raw-material design templates
- TEMPLATE_ORDER: ordered list of template ids per pipeline (for output filenames)
- format_copy_md: render the 6-style copy bundles as markdown
- UNIVERSAL_SUFFIX: appended to every marketing prompt (slot policy)
- REALISM_SUFFIX: appended to photo-style marketing prompts
- OMIT_REFERENCE: set[str] — templates where reference image must NOT be sent
- DESIGN_DEPS: dict[str, str] — design templates that depend on sketch
"""

from .analysis import ANALYSIS_PROMPT_TEMPLATE, build_analysis_prompt, parse_analysis_json
from .marketing import (
    MARKETING_BUILDERS,
    MARKETING_ORDER,
    PHOTO_TEMPLATES,
    OMIT_REFERENCE,
    UNIVERSAL_SUFFIX,
    REALISM_SUFFIX,
)
from .design import DESIGN_BUILDERS, DESIGN_ORDER, DESIGN_DEPS
from .copy_format import format_copy_md

__all__ = [
    "ANALYSIS_PROMPT_TEMPLATE",
    "build_analysis_prompt",
    "parse_analysis_json",
    "MARKETING_BUILDERS",
    "MARKETING_ORDER",
    "PHOTO_TEMPLATES",
    "OMIT_REFERENCE",
    "UNIVERSAL_SUFFIX",
    "REALISM_SUFFIX",
    "DESIGN_BUILDERS",
    "DESIGN_ORDER",
    "DESIGN_DEPS",
    "format_copy_md",
]
