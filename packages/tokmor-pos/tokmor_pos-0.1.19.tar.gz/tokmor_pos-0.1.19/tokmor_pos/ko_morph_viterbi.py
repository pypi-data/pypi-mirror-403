from __future__ import annotations

"""
Korean POS helper (Kiwi-like shape):
- generate token-level coarse candidates from TokMor's Korean morpheme POS tags
- run a tiny Viterbi over 6POS to pick a consistent sequence

This is dependency-free besides TokMor itself (already required by tokmor-pos).
"""

from functools import lru_cache
from typing import Dict, List, Tuple

from .lexicon6 import TAG6, _log, load_transitions6  # type: ignore


def _is_hangul(s: str) -> bool:
    return bool(s) and any("\uac00" <= ch <= "\ud7af" for ch in s)


@lru_cache(maxsize=20000)
def _ko_candidates_6pos(token: str) -> List[Tuple[str, float, str]]:
    """
    Return list of (tag6, prob, source).
    """
    t = token or ""
    if not t:
        return [("O", 1.0, "ko_morph:empty")]
    if not _is_hangul(t):
        # non-hangul: let lexicon6 / base rules handle it
        return [("O", 0.55, "ko_morph:nonhangul"), ("N", 0.25, "ko_morph:nonhangul"), ("P", 0.20, "ko_morph:nonhangul")]

    try:
        # Use TokMor's specialized analyzer via unified analyzer
        from tokmor.morphology.unified import get_unified_analyzer  # type: ignore

        an = get_unified_analyzer("ko")
        morphs = an.analyze(t)
    except Exception:
        morphs = []

    # Collect Sejong-ish tags
    tags: List[str] = []
    for m in morphs or []:
        p = getattr(m, "pos", "") or ""
        if p:
            tags.append(p.split("+", 1)[0])

    # Base prior
    # (These are probabilities before normalization; we normalize at the end.)
    score: Dict[str, float] = {"N": 0.25, "V": 0.20, "P": 0.20, "A": 0.15, "R": 0.10, "O": 0.05}
    reason = "ko_morph:prior"

    # Strong signals
    has_josa = any(p.startswith("J") for p in tags)  # JKS/JKO/JKB/JX/...
    has_eomi = any(p.startswith("E") for p in tags)  # EC/EF/EP/ETM/ETN
    has_verb = any(p in {"VV", "VX", "VCP", "VCN"} for p in tags)
    has_adj = any(p == "VA" for p in tags)
    has_adv = any(p.startswith("M") for p in tags)  # MAG/MAJ
    has_noun = any(p.startswith("NN") or p in {"NP", "NR"} for p in tags)

    if has_josa or has_eomi or any(p.startswith("X") for p in tags):
        # In UD, many of these behave like PART/ADP/DET => F in POS8, so P here.
        score["P"] += 0.80
        score["N"] += 0.20
        score["V"] += 0.10
        reason = "ko_morph:functional"

    if has_verb:
        score["V"] += 0.80
        reason = "ko_morph:verb"
    if has_adj:
        score["A"] += 0.80
        reason = "ko_morph:adj"
    if has_adv:
        score["R"] += 0.70
        reason = "ko_morph:adv"
    if has_noun and not (has_verb or has_adj):
        score["N"] += 0.60
        reason = "ko_morph:noun"

    # Normalize and return top-3
    s = sum(max(0.0, v) for v in score.values()) or 1.0
    rows = [(k, v / s, reason) for k, v in score.items() if k in TAG6]
    rows.sort(key=lambda x: -x[1])
    return rows[:3]


def viterbi_tag_ko_6pos(tokens: List[str]) -> List[Tuple[str, float, str]]:
    """
    Return list aligned to tokens: (tag6, confidence, source)
    """
    if not tokens:
        return []

    emits: List[List[Tuple[str, float, str]]] = [_ko_candidates_6pos(t) for t in tokens]
    tr = load_transitions6()

    # Viterbi over TAG6
    dp: List[Dict[str, float]] = []
    back: List[Dict[str, str]] = []

    dp0: Dict[str, float] = {}
    back0: Dict[str, str] = {}
    for tag, p_emit, _src in emits[0]:
        dp0[tag] = tr.get("BOS", {}).get(tag, -1e9) + _log(p_emit)
        back0[tag] = "BOS"
    dp.append(dp0)
    back.append(back0)

    for i in range(1, len(tokens)):
        dpi: Dict[str, float] = {}
        backi: Dict[str, str] = {}
        for tag, p_emit, _src in emits[i]:
            best_score = -1e18
            best_prev = None
            for prev_tag, prev_score in dp[i - 1].items():
                s = prev_score + tr.get(prev_tag, {}).get(tag, -1e9) + _log(p_emit)
                if s > best_score:
                    best_score = s
                    best_prev = prev_tag
            if best_prev is not None:
                dpi[tag] = best_score
                backi[tag] = best_prev
        dp.append(dpi)
        back.append(backi)

    last = dp[-1]
    best_last = None
    best_score = -1e18
    for tag, sc in last.items():
        s = sc + tr.get(tag, {}).get("EOS", -1e9)
        if s > best_score:
            best_score = s
            best_last = tag
    if best_last is None:
        # greedy fallback
        out = []
        for row in emits:
            out.append(max(row, key=lambda x: x[1]))
        return out

    tags_out: List[str] = [best_last]
    for i in range(len(tokens) - 1, 0, -1):
        tags_out.append(back[i].get(tags_out[-1], "O"))
    tags_out.reverse()

    out2: List[Tuple[str, float, str]] = []
    for i, chosen in enumerate(tags_out):
        row = emits[i]
        p = 1e-6
        src = "ko_morph:viterbi"
        for tag, sc, row_src in row:
            if tag == chosen:
                p = sc
                src = row_src
                break
        out2.append((chosen, float(p), src))
    return out2

