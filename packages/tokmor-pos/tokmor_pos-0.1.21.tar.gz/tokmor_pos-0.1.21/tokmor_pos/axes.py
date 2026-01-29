from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import tokmor

from .ear import EAR_A_A_MIN, EAR_E_P_MIN, _base_lang, _is_number, _is_punct, _looks_like_latin_verb, LATIN_LANGS
from .parson_mini import get_parson_mini


@dataclass(frozen=True)
class TokenAxes:
    text: str
    axes: dict[str, float]  # P,A,R,S,O,N
    method: str
    ear_hint: str  # "E"|"A"|"R"|"" (blank allowed)


def _ear_hint_from_axes(
    tok: str,
    *,
    lang: str,
    axes: Optional[dict[str, float]] = None,
) -> str:
    """
    Derive EAR hint from ParSon axes (high precision, blank allowed).
    E = Existence (Presence), not entity.
    """
    t = (tok or "").strip()
    if not t:
        return "R"
    if _is_punct(t):
        return "R"
    if tokmor.function_word_tag(lang, t):
        return "R"
    if _is_number(t):
        return "E"
    if not axes:
        return ""

    ll = _base_lang(lang)
    P = float(axes.get("P", 0.5))
    A = float(axes.get("A", 0.5))
    R = float(axes.get("R", 0.5))

    # A: only when action-ish is strong; for Latin, require verb-like cue.
    if A >= EAR_A_A_MIN:
        if ll in LATIN_LANGS and not _looks_like_latin_verb(t):
            return ""
        return "A"

    # E: strong existence/presence but not strongly action-ish.
    if P >= EAR_E_P_MIN and A <= 0.60:
        return "E"

    # We keep R strictly as function_word/punct for stability.
    _ = R
    return ""


def tag_axes_token(tok: str, *, lang: str) -> Optional[TokenAxes]:
    t = (tok or "").strip()
    ps = get_parson_mini(lang)
    if ps is None:
        return None
    ax = ps.get_axes(t)
    if ax is None:
        return None
    axes = {"P": ax.P, "A": ax.A, "R": ax.R, "S": ax.S, "O": ax.O, "N": ax.N}
    ear_hint = _ear_hint_from_axes(t, lang=lang, axes=axes)
    return TokenAxes(text=t, axes=axes, method=ax.method, ear_hint=ear_hint)


def tag_axes_text(text: str, *, lang: str) -> list[TokenAxes]:
    ut = tokmor.unified_tokenize(text, lang=lang, sns=True, include_pos4=False, include_sns_tags=False)
    raw = [td for td in (ut.get("tokens") or []) if isinstance(td, dict)]
    toks = [str(td.get("text") or "") for td in raw]
    out: list[TokenAxes] = []
    for tok in toks:
        r = tag_axes_token(tok, lang=lang)
        if r is None:
            # still produce a row with blank axes for consistent output
            out.append(TokenAxes(text=str(tok or ""), axes={}, method="", ear_hint=_ear_hint_from_axes(str(tok or ""), lang=lang, axes=None)))
        else:
            out.append(r)
    return out

