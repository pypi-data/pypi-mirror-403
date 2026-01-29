from __future__ import annotations

"""
Lexicon-based coarse POS (6POS) with optional Viterbi disambiguation.

Tagset (6POS):
- N: nouns/proper nouns
- V: verbs/aux
- P: function words (adp/det/pron/part/conj/etc.)
- A: adjectives
- R: adverbs
- O: other (num/punct/sym/x/unknown)

This module is intentionally dependency-free.
"""

import json
import math
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .resources import normalize_lang, resolve_lexicon6_path, resolve_transitions6_path

TAG6 = ("N", "V", "P", "A", "R", "O")


def _log(x: float) -> float:
    if x <= 0.0:
        return -1e9
    return math.log(x)


@dataclass(frozen=True)
class Lexicon6Entry:
    # List of (tag, score) where score is in (0,1]
    cand: Tuple[Tuple[str, float], ...]


@lru_cache(maxsize=2)
def _resolve_lexicon6_full_zip() -> Optional[Path]:
    """
    Optional big built-in lexicon6 pack shipped inside the wheel.
    Layout: tokmor_pos/models/lexicon6_full.zip containing lexicon6/<lang>.json files.
    """
    try:
        p = Path(__file__).resolve().parent / "models" / "lexicon6_full.zip"
        if p.exists():
            return p
    except Exception:
        pass
    return None


def _parse_lexicon6_json(obj: object) -> Dict[str, Lexicon6Entry]:
    if not isinstance(obj, dict):
        return {}
    out: Dict[str, Lexicon6Entry] = {}
    for k, v in obj.items():
        if not isinstance(k, str) or not k:
            continue
        if not isinstance(v, list) or not v:
            continue
        cand: List[Tuple[str, float]] = []
        for it in v:
            if not (isinstance(it, list) or isinstance(it, tuple)) or len(it) < 2:
                continue
            tag = it[0]
            sc = it[1]
            if tag not in TAG6:
                continue
            try:
                f = float(sc)
            except Exception:
                continue
            if f <= 0.0:
                continue
            cand.append((tag, min(1.0, f)))
        if cand:
            out[k] = Lexicon6Entry(cand=tuple(cand))
    return out


@lru_cache(maxsize=512)
def _load_lexicon6_from_zip(lang: str) -> Dict[str, Lexicon6Entry]:
    zpath = _resolve_lexicon6_full_zip()
    if not zpath:
        return {}
    ll = normalize_lang(lang)
    name = f"lexicon6/{ll}.json"
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            try:
                raw = zf.read(name)
            except KeyError:
                # Fallback inside zip if present
                try:
                    raw = zf.read("lexicon6/universal.json")
                except KeyError:
                    return {}
        obj = json.loads(raw.decode("utf-8", errors="ignore"))
        return _parse_lexicon6_json(obj)
    except Exception:
        return {}


@lru_cache(maxsize=512)
def load_lexicon6(lang: str) -> Dict[str, Lexicon6Entry]:
    p = resolve_lexicon6_path(lang)
    if not p:
        return _load_lexicon6_from_zip(lang)
    # If the resolver chose the tiny universal starter lexicon, but we have a full zip,
    # prefer the full zip for this language.
    try:
        if p.name == "universal.json":
            z = _load_lexicon6_from_zip(lang)
            if z:
                return z
    except Exception:
        pass
    try:
        obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        out = _parse_lexicon6_json(obj)
        return out if out else _load_lexicon6_from_zip(lang)
    except Exception:
        return _load_lexicon6_from_zip(lang)


@lru_cache(maxsize=1)
def load_transitions6() -> Dict[str, Dict[str, float]]:
    """
    Return log-prob transitions: prev -> next -> logp.
    Includes BOS/EOS.
    """
    p = resolve_transitions6_path()
    if p:
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(obj, dict) and "transitions" in obj and isinstance(obj["transitions"], dict):
                tr = obj["transitions"]
                out: Dict[str, Dict[str, float]] = {}
                for a, row in tr.items():
                    if not isinstance(row, dict):
                        continue
                    out[a] = {}
                    for b, prob in row.items():
                        try:
                            out[a][b] = _log(float(prob))
                        except Exception:
                            continue
                if out:
                    return out
        except Exception:
            pass

    # fallback: simple priors (works without training)
    # Encourage sticky tags (N->N, V->V, P->P), allow N<->A/R near content.
    base = 1e-3
    tags = list(TAG6)
    out2: Dict[str, Dict[str, float]] = {}
    for a in ["BOS"] + tags:
        out2[a] = {}
        for b in tags + (["EOS"] if a != "BOS" else []):
            out2[a][b] = _log(base)
    # BOS priors
    out2["BOS"]["P"] = _log(0.30)
    out2["BOS"]["N"] = _log(0.30)
    out2["BOS"]["V"] = _log(0.15)
    out2["BOS"]["A"] = _log(0.10)
    out2["BOS"]["R"] = _log(0.10)
    out2["BOS"]["O"] = _log(0.05)

    def _set(a: str, b: str, p_: float):
        out2[a][b] = _log(p_)

    for t in tags:
        _set(t, t, 0.45)
    _set("N", "A", 0.10)
    _set("A", "N", 0.18)
    _set("R", "V", 0.12)
    _set("P", "N", 0.20)
    _set("P", "V", 0.12)
    _set("V", "P", 0.15)
    _set("N", "P", 0.12)
    _set("O", "O", 0.60)
    # EOS preference
    for t in tags:
        out2[t]["EOS"] = _log(0.08)

    return out2


def _fallback_candidates(tok: str, *, lang: str) -> List[Tuple[str, float]]:
    if not tok:
        return [("O", 1.0)]
    if tok.isdigit():
        return [("O", 0.9)]
    if len(tok) == 1 and (not tok.isalnum()):
        return [("O", 0.95)]

    # Script-aware fallback (critical for languages where lexicon coverage is sparse).
    # If we bias too hard to O, the tagger collapses N/V/P -> O for scripts like Arabic/CJK.
    ll = normalize_lang(lang)
    def _has_han(s: str) -> bool:
        for ch in s:
            o = ord(ch)
            if (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF):
                return True
        return False

    def _has_arabic(s: str) -> bool:
        for ch in s:
            o = ord(ch)
            if (0x0600 <= o <= 0x06FF) or (0x0750 <= o <= 0x077F) or (0x08A0 <= o <= 0x08FF):
                return True
        return False

    if _has_han(tok):
        # Han tokens: keep a conservative content bias (this performed best on our UD eval set).
        return [("N", 0.55), ("V", 0.25), ("P", 0.10), ("O", 0.10)]
    if _has_arabic(tok):
        # Arabic script: avoid O-collapse, keep a meaningful P prior for clitics/particles.
        # For Arabic UD, we were over-predicting P (POS8 F). Bias more toward N to reduce N->F.
        if ll == "ar":
            return [("N", 0.55), ("V", 0.20), ("P", 0.15), ("O", 0.10)]
        return [("N", 0.45), ("P", 0.25), ("V", 0.20), ("O", 0.10)]

    # Generic fallback (still slightly N/V/P leaning, but keep O for symbols/mixed tokens).
    return [("N", 0.40), ("V", 0.20), ("P", 0.20), ("O", 0.20)]


def tag_lexicon6(tokens: List[str], *, lang: str, use_viterbi: bool = True) -> List[Tuple[str, float, str]]:
    """
    Return list aligned to tokens: (tag6, confidence, source)
    source in {"lexicon6", "fallback", "viterbi"} (viterbi still uses lexicon/fallback emits)
    """
    ll = normalize_lang(lang)
    lex = load_lexicon6(ll)

    emits: List[List[Tuple[str, float, str]]] = []
    for t in tokens:
        if not isinstance(t, str):
            t = str(t)
        ent = lex.get(t) or lex.get(t.lower())
        if ent:
            row = [(tag, score, "lexicon6") for tag, score in ent.cand]
        else:
            row = [(tag, score, "fallback") for tag, score in _fallback_candidates(t, lang=ll)]
        # normalize
        s = sum(max(0.0, sc) for _, sc, _ in row) or 1.0
        row2 = [(tag, sc / s, src) for tag, sc, src in row]
        emits.append(row2)

    if (not use_viterbi) or len(tokens) <= 1:
        out = []
        for row in emits:
            best = max(row, key=lambda x: x[1])
            out.append(best)
        return out

    tr = load_transitions6()

    # Viterbi over TAG6
    dp: List[Dict[str, float]] = []
    back: List[Dict[str, str]] = []

    # init
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

    # end
    last = dp[-1]
    best_last = None
    best_score = -1e18
    for tag, sc in last.items():
        s = sc + tr.get(tag, {}).get("EOS", -1e9)
        if s > best_score:
            best_score = s
            best_last = tag
    if best_last is None:
        # fallback to greedy
        return [max(row, key=lambda x: x[1]) for row in emits]

    tags_out: List[str] = [best_last]
    for i in range(len(tokens) - 1, 0, -1):
        tags_out.append(back[i].get(tags_out[-1], "O"))
    tags_out.reverse()

    # compute per-token confidence as normalized emit prob for chosen tag
    out2: List[Tuple[str, float, str]] = []
    for i, chosen in enumerate(tags_out):
        row = emits[i]
        p = 1e-6
        src = "viterbi"
        for tag, sc, row_src in row:
            if tag == chosen:
                p = sc
                src = row_src if row_src != "fallback" else "viterbi"
                break
        out2.append((chosen, float(p), src))
    return out2


def map_6pos_to_pos8(tag6: str) -> str:
    """
    Coarse mapping into TokMor POS8 space.
    """
    if tag6 == "N":
        return "N"
    if tag6 == "V":
        return "V"
    if tag6 in {"A", "R"}:
        return "M"
    if tag6 == "P":
        return "F"
    if tag6 == "O":
        return "O"
    return "UNK"

