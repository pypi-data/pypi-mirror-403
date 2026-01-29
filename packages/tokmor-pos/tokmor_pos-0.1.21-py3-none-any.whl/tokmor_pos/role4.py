from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal

from .coarse_pos8 import POS8Result


Role4 = Literal["ENTITY", "ACTION", "ATTRIBUTE", "FUNCTION", "UNK"]


@dataclass
class Role4Result:
    token: str
    role4: Role4
    # Simple continuous hints in [0, 1]. These are not probabilities; they are gating-friendly scores.
    e: float
    a: float
    r: float
    # Evidence (for debugging / product transparency)
    pos8: str
    pos8_rule: str
    source: str  # 'pos8' | 'pos8_number' | 'pos8_time' | 'pos8_punct' | 'pos8_regex' | 'morph_fallback' | 'unknown'


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def role4_from_pos8_tag(tag: str) -> Role4:
    """
    Deterministic mapping from POS8 → Role4.
    This is intentionally simple and conservative.
    """
    if tag == "N":
        return "ENTITY"
    if tag == "V":
        return "ACTION"
    if tag == "M":
        return "ATTRIBUTE"
    if tag in {"F", "S"}:
        return "FUNCTION"
    if tag in {"Q", "T"}:
        # Numbers/time behave like entity-like values in downstream candidate generation
        return "ENTITY"
    if tag == "O":
        return "UNK"
    if tag == "UNK":
        return "UNK"
    return "UNK"


def ear_scores_from_pos8_tag(tag: str) -> tuple[float, float, float]:
    """
    Minimal structure hint scores derived from POS8.

    Interpretation:
      - e (existence/entityness prior): nouns/values
      - a (agency/action prior): verbs
      - r (relational/function prior): function words / particles / punctuation-as-structure
    """
    if tag == "N":
        return 1.0, 0.0, 0.0
    if tag == "V":
        return 0.0, 1.0, 0.0
    if tag == "M":
        return 0.2, 0.1, 0.0
    if tag == "F":
        return 0.0, 0.0, 1.0
    if tag == "S":
        return 0.0, 0.0, 0.8
    if tag == "Q":
        return 0.9, 0.0, 0.0
    if tag == "T":
        return 0.9, 0.0, 0.0
    return 0.0, 0.0, 0.0


def tag_role4_from_pos8(pos8: Iterable[POS8Result]) -> List[Role4Result]:
    out: List[Role4Result] = []
    for r in pos8:
        role = role4_from_pos8_tag(r.tag)
        e, a, rel = ear_scores_from_pos8_tag(r.tag)
        src = "pos8"
        if r.rule == "number":
            src = "pos8_number"
        elif r.rule == "time":
            src = "pos8_time"
        elif r.rule == "punct":
            src = "pos8_punct"
        elif isinstance(r.rule, str) and r.rule.startswith("regex:"):
            src = "pos8_regex"
        if r.rule == "morph_fallback":
            src = "morph_fallback"
        if r.tag == "UNK":
            src = "unknown"
        out.append(
            Role4Result(
                token=r.token,
                role4=role,
                e=_clamp01(e),
                a=_clamp01(a),
                r=_clamp01(rel),
                pos8=str(r.tag),
                pos8_rule=str(r.rule or ""),
                source=src,
            )
        )
    return out


