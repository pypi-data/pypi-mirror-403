"""
tokmor-pos: TokMor POS (EAR) + legacy POS8 tools.

In this project, "TokMor POS" means **EAR (E/A/R) speech parts** with **blank allowed**:
- E: existence-ish (high confidence)
- R: relation-ish (function words / punctuation)
- A: action-ish (high confidence)
- blank: abstain (do not force classification)

This package also contains legacy POS8/role tools kept for compatibility.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    # EAR (TokMor POS)
    "ear_tag_token",
    "ear_tag_text",
    "ear_tag_tokens",
    # ParSon axes (P/A/R/S/O/N)
    "tag_axes_text",
    "tag_axes_token",
]

__version__ = "0.1.20"

from .ear import ear_tag_token, ear_tag_text, ear_tag_tokens  # noqa: E402
from .axes import tag_axes_text, tag_axes_token  # noqa: E402

# Legacy exports (optional; may be unavailable if legacy deps are not installed)
try:  # pragma: no cover
    from .api import get_pos8_tagger, tag_pos8, tag_pos8_with_microcrf  # type: ignore
    from .coarse_pos8 import CoarsePOS8Tagger, POS8, load_pos8_config  # type: ignore

    __all__ += [
        "get_pos8_tagger",
        "tag_pos8",
        "tag_pos8_with_microcrf",
        "CoarsePOS8Tagger",
        "POS8",
        "load_pos8_config",
    ]
except Exception:
    pass


