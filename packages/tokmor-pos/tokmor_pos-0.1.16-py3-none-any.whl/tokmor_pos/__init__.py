"""
tokmor-pos: Structural POS8 hints + optional Micro-CRF boundary smoothing.

This is NOT a linguistic POS tagger. It emits lightweight, language-agnostic
"structural role" hints (POS8) and can optionally smooth span boundaries (BIO).
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "get_pos8_tagger",
    "tag_pos8",
    "tag_pos8_with_microcrf",
    "CoarsePOS8Tagger",
    "POS8",
    "load_pos8_config",
]

__version__ = "0.1.16"

from .api import get_pos8_tagger, tag_pos8, tag_pos8_with_microcrf  # noqa: E402
from .coarse_pos8 import CoarsePOS8Tagger, POS8, load_pos8_config  # noqa: E402


