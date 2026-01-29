from __future__ import annotations

import os
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional


def normalize_lang(lang: str) -> str:
    l = (lang or "").lower().replace("_", "-")
    alias = {
        "simple": "en",
        "zh-cn": "zh",
        "zh-tw": "zh",
        # Chinese variants / Wikipedia-style codes: route to zh for lexicon reuse.
        "yue": "zh",
        "wuu": "zh",
        "nan": "zh",
        "gan": "zh",
        "hak": "zh",
        "cdo": "zh",
        "lzh": "zh",
        "zh-classical": "zh",
        "zh-min-nan": "zh",
        "zh-yue": "zh",
        # Wikipedia / historical / variant codes: route to closest standard language.
        "als": "de",          # Alemannic -> German
        "be-tarask": "be",    # Belarusian (Taraškievica) -> Belarusian
        "be-x-old": "be",     # old Belarusian code -> Belarusian
        "mo": "ro",           # Moldovan -> Romanian
        "roa-rup": "ro",      # Aromanian -> Romanian (fallback)
        "roa-tara": "it",     # Tarantino dialect -> Italian (fallback)
        "hyw": "hy",          # Western Armenian -> Armenian (fallback)
        "bat-smg": "lt",      # Samogitian -> Lithuanian (fallback)
        "fiu-vro": "et",      # Võro -> Estonian (fallback)
        "eml": "it",          # Emiliano-Romagnolo -> Italian (fallback)
    }
    return alias.get(l, l)


@lru_cache(maxsize=1)
def data_dirs() -> List[Path]:
    """
    Ordered list of runtime data directories to search for tokmor-pos assets.

    Priority:
    1) TOKMORPOS_DATA_DIR  (tokmor-pos-specific packs)
    2) TOKMOR_DATA_DIR     (tokmor packs, e.g., extended_dict)
    """
    out: List[Path] = []
    for env_key in ("TOKMORPOS_DATA_DIR", "TOKMOR_DATA_DIR"):
        v = os.getenv(env_key)
        if not v:
            continue
        p = Path(v).expanduser()
        if p not in out:
            out.append(p)

    # Built-in fallback (shipped inside the wheel). This makes tokmor-pos usable out-of-the-box.
    pkg = Path(__file__).resolve().parent / "models"
    if pkg.exists() and pkg not in out:
        out.append(pkg)
    return out


@lru_cache(maxsize=1)
def data_dir() -> Optional[Path]:
    """
    Optional runtime data directory for tokmor-pos assets.

    Priority:
    1) TOKMORPOS_DATA_DIR
    2) TOKMOR_DATA_DIR
    """
    ds = data_dirs()
    return ds[0] if ds else None


def resolve_microcrf_path(lang: str) -> Optional[Path]:
    l = normalize_lang(lang)
    for root in data_dirs():
        cand = root / "micro_crf" / f"{l}_bio.pkl"
        if cand.exists():
            return cand
    return None


def resolve_extended_dict_path(lang: str) -> Optional[Path]:
    """
    Resolve path to a TokMor extended_dict (surface -> coarse POS hint).

    Expected pack layout (under TOKMOR_DATA_DIR or TOKMORPOS_DATA_DIR):
      extended_dict/{lang}_extended.json

    Values are typically in: NOUN/PROPN/VERB/ADJ/ADV.
    """
    l = normalize_lang(lang)
    for root in data_dirs():
        cand = root / "extended_dict" / f"{l}_extended.json"
        if cand.exists():
            return cand
    return None


def resolve_lexicon6_path(lang: str) -> Optional[Path]:
    """
    Resolve path to a lexicon6 pack file.

    Expected pack layout (under TOKMOR_DATA_DIR or TOKMORPOS_DATA_DIR):
      lexicon6/{lang}.json
    """
    l = normalize_lang(lang)
    for root in data_dirs():
        cand = root / "lexicon6" / f"{l}.json"
        if cand.exists():
            # If an external pack includes empty per-language files ({}), it can block
            # our built-in universal fallback. Treat tiny files as "missing".
            try:
                if cand.stat().st_size <= 4:
                    # keep searching (may hit wheel-shipped universal.json)
                    pass
                else:
                    return cand
            except Exception:
                return cand
        # Universal fallback: if we don't ship per-language lexicon6, still provide a usable default.
        if root.name == "models":
            u = root / "lexicon6" / "universal.json"
            if u.exists():
                return u
    return None


def resolve_transitions6_path() -> Optional[Path]:
    """
    Resolve path to a global 6POS transitions file.
    Expected:
      lexicon6/transitions_6pos.json
    """
    for root in data_dirs():
        cand = root / "lexicon6" / "transitions_6pos.json"
        if cand.exists():
            return cand
    return None


@lru_cache(maxsize=128)
def load_extended_dict(lang: str) -> Dict[str, str]:
    """
    Load extended_dict for a language. Returns {} when missing or disabled.
    """
    v = os.getenv("TOKMOR_DISABLE_EXTENDED_DICT", "").strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return {}
    return load_extended_dict_force(lang)


@lru_cache(maxsize=128)
def load_extended_dict_force(lang: str) -> Dict[str, str]:
    """
    Load extended_dict for a language, ignoring TOKMOR_DISABLE_EXTENDED_DICT.
    Useful when the caller explicitly opts in (e.g., CLI flag).
    """
    p = resolve_extended_dict_path(lang)
    if not p:
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}



