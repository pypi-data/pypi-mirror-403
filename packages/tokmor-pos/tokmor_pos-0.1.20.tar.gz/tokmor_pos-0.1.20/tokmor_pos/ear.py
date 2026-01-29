from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import tokmor

from .parson_mini import get_parson_mini

LATIN_LANGS = {"en", "de", "fr", "es", "it", "pt", "nl"}

# Default thresholds (high precision; blank allowed)
EAR_E_P_MIN = float(os.getenv("EAR_E_P_MIN", "0.70").strip() or "0.70")  # Existence via ParSon P (Presence)
EAR_A_A_MIN = float(os.getenv("EAR_A_A_MIN", "0.70").strip() or "0.70")  # Action via ParSon A
EAR_R_IS_FUNCTION_ONLY = (os.getenv("EAR_R_FUNCTION_ONLY", "1").strip() or "1") not in {"0", "false", "False", "no", "NO"}


def _base_lang(lang: str) -> str:
    return (lang or "").split("-", 1)[0].lower()


def _is_punct(tok: str) -> bool:
    return bool(tok) and all((not ch.isalnum()) for ch in tok)


def _is_number(tok: str) -> bool:
    if not tok:
        return False
    t = tok.replace(",", "").replace("_", "")
    t = t.replace("-", "", 1)
    t = t.replace(".", "", 1)
    return t.isdigit()


def _looks_like_latin_verb(tok: str) -> bool:
    tl = (tok or "").lower()
    if len(tl) < 2:
        return False
    if tl in {
        "is", "am", "are", "was", "were", "be", "been", "being",
        "do", "does", "did", "have", "has", "had",
        "will", "would", "can", "could", "should", "may", "might", "must", "shall",
    }:
        return True
    if len(tl) >= 4 and (tl.endswith("ing") or tl.endswith("ed")):
        return True
    # Small allowlist: common base-form verbs that don't match suffix heuristics.
    if tl in {"come", "go", "get", "make", "take", "see", "say", "know"}:
        return True
    return False


def _latin_entity_forms(tok: str) -> list[str]:
    t = (tok or "").strip()
    if not t:
        return []
    forms: list[str] = []

    def add(x: str) -> None:
        x = (x or "").strip()
        if x and x not in forms:
            forms.append(x)

    add(t)
    stripped = re.sub(r"""^[\s"'“”‘’\(\)\[\]\{\}<>,.;:!?]+|[\s"'“”‘’\(\)\[\]\{\}<>,.;:!?]+$""", "", t)
    add(stripped)
    for s in [t, stripped]:
        if not s:
            continue
        if s.endswith("'s") or s.endswith("’s"):
            add(s[:-2])
        if s.endswith("'") or s.endswith("’"):
            add(s[:-1])
    return forms


def _patch_ppmi_base(PPMIClassifierV2: Any) -> None:
    """
    Prefer full matrices under ~/ppmi/wiki_ppmi_large if present.
    """
    try:
        base_override = os.getenv("PPMI_BASE_DIR", "").strip()
        if base_override:
            PPMIClassifierV2.PPMI_BASE = Path(base_override).expanduser().resolve()
            return
        cand_all = Path.home() / "ppmi" / "wiki_ppmi_all"
        cand_large = Path.home() / "ppmi" / "wiki_ppmi_large"
        if (cand_all / "en" / "ppmi.npz").exists():
            PPMIClassifierV2.PPMI_BASE = cand_all
        elif (cand_large / "en" / "ppmi.npz").exists():
            PPMIClassifierV2.PPMI_BASE = cand_large
    except Exception:
        return


def _ensure_centroids(PPMIClassifierV2: Any, lang: str) -> None:
    """
    Some setups keep centroids under wiki_ppmi_all only.
    Ensure type_centroids.npz exists next to ppmi.npz/vocab.json so ppmi_rel works.
    """
    try:
        base_dir = getattr(PPMIClassifierV2, "PPMI_BASE", None)
        if not isinstance(base_dir, Path):
            return
        pl = _base_lang(lang)
        ppmi_lang = "zh-Hans" if pl == "zh" else pl
        cur_dir = base_dir / ppmi_lang
        if ppmi_lang == "zh-Hans" and not cur_dir.exists():
            alt = base_dir / "zh"
            if alt.exists():
                cur_dir = alt
        centroid_fp = cur_dir / "type_centroids.npz"
        if centroid_fp.exists():
            return
        alt_centroid = Path.home() / "ppmi" / "wiki_ppmi_all" / ppmi_lang / "type_centroids.npz"
        if not alt_centroid.exists() and ppmi_lang == "zh-Hans":
            alt_centroid = Path.home() / "ppmi" / "wiki_ppmi_all" / "zh" / "type_centroids.npz"
        # Centroids copy is handled by the full ParSon project; tokmor-pos does not bundle PPMI.
    except Exception:
        return


@dataclass(frozen=True)
class TokenEAR:
    text: str
    ear: str  # "E"|"A"|"R"|"" (blank allowed)
    meta: dict[str, Any]


def ear_tag_token(
    token: str,
    *,
    lang: str,
    context_words: Optional[list[str]] = None,
    picky: bool = True,
    e_min_conf: float = 0.25,
) -> TokenEAR:
    """
    TokMor POS = EAR tagging (Existence / Action / Relation).
    Returns blank ("") when not confident if `picky=True`.
    """
    t = (token or "").strip()
    ll = _base_lang(lang)
    meta: dict[str, Any] = {}

    if not t:
        return TokenEAR(text=t, ear="R", meta={"reason": "empty"})
    if _is_punct(t):
        return TokenEAR(text=t, ear="R", meta={"reason": "punct"})
    if tokmor.function_word_tag(lang, t):
        return TokenEAR(text=t, ear="R", meta={"reason": "function_word"})
    if _is_number(t):
        return TokenEAR(text=t, ear="E", meta={"reason": "number"})

    # 1) ParSon mini axes (preferred). E means Existence (Presence), not entity.
    ps = get_parson_mini(lang)
    if ps is not None:
        ax = ps.get_axes(t)
        if ax is not None:
            P, A, R, S, O, N = ax.P, ax.A, ax.R, ax.S, ax.O, ax.N
            meta["axes"] = {"P": P, "A": A, "R": R, "S": S, "O": O, "N": N, "method": ax.method}

            # Relation: by default we keep R as function-word-only for stability.
            if not EAR_R_IS_FUNCTION_ONLY and R >= 0.80 and P >= 0.60:
                return TokenEAR(text=t, ear="R", meta={**meta, "reason": "parson_R"})

            # Action: high A, and (Latin) verb-like cue to avoid noun false positives.
            if A >= EAR_A_A_MIN:
                if ll in LATIN_LANGS and not _looks_like_latin_verb(t):
                    pass
                else:
                    return TokenEAR(text=t, ear="A", meta={**meta, "reason": "parson_A"})

            # Existence: high P (presence/existence), and not strongly action-ish.
            if P >= EAR_E_P_MIN and A <= 0.60:
                return TokenEAR(text=t, ear="E", meta={**meta, "reason": "parson_P"})

    # 2) PPMI is intentionally not bundled inside tokmor-pos.
    # If you want PPMI signals, install TokMor's external PPMI pack and add your own integration layer.

    # 3) Minimal non-ParSon fallback (high precision): only obvious Latin verbs.
    if ll in LATIN_LANGS and _looks_like_latin_verb(t):
        return TokenEAR(text=t, ear="A", meta={**meta, "reason": "latin_verb_cue"})

    # Default: blank if picky, else E.
    return TokenEAR(text=t, ear="" if picky else "E", meta={**meta, "reason": "blank" if picky else "default_E"})


def ear_tag_text(
    text: str,
    *,
    lang: str,
    picky: bool = True,
    e_min_conf: float = 0.25,
) -> list[TokenEAR]:
    ut = tokmor.unified_tokenize(text, lang=lang, sns=True, include_pos4=False, include_sns_tags=False)
    raw = [td for td in (ut.get("tokens") or []) if isinstance(td, dict)]
    texts = [str(td.get("text") or "") for td in raw]
    out: list[TokenEAR] = []
    for i, tok in enumerate(texts):
        ctx = []
        for j in range(max(0, i - 2), min(len(texts), i + 3)):
            if j == i:
                continue
            w = (texts[j] or "").strip()
            if w and not _is_punct(w):
                ctx.append(w)
        out.append(ear_tag_token(tok, lang=lang, context_words=ctx, picky=picky, e_min_conf=e_min_conf))
    return out


def ear_tag_tokens(
    tokens: Iterable[str],
    *,
    lang: str,
    picky: bool = True,
    e_min_conf: float = 0.25,
) -> list[TokenEAR]:
    toks = [str(t or "") for t in tokens]
    out: list[TokenEAR] = []
    for i, tok in enumerate(toks):
        ctx = []
        for j in range(max(0, i - 2), min(len(toks), i + 3)):
            if j == i:
                continue
            w = (toks[j] or "").strip()
            if w and not _is_punct(w):
                ctx.append(w)
        out.append(ear_tag_token(tok, lang=lang, context_words=ctx, picky=picky, e_min_conf=e_min_conf))
    return out

