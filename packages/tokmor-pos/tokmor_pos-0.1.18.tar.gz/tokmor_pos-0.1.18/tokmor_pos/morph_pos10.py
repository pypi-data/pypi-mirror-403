from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Iterable, Optional

# Reuse deterministic token-shape overrides (helps noisy UGC).
import re

# POS10:
# N common noun, P proper noun, V verb, A aux, J adj, R adv,
# F function-ish, Q number, T time/date, S punct/symbol, O other
POS10_SET = {"N", "P", "V", "A", "J", "R", "F", "Q", "T", "S", "O"}

_RX_DATE = re.compile(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}:\d{2}(:\d{2})?)$")


def _is_punct(tok: str) -> bool:
    return bool(tok) and all(not ch.isalnum() for ch in tok)


def _is_number(tok: str) -> bool:
    if not tok:
        return False
    t = tok.replace(",", "").replace("_", "")
    t = t.replace("-", "", 1)
    t = t.replace(".", "", 1)
    return t.isdigit()


def _map_universal_to_pos10(tag: str) -> Optional[str]:
    u = (tag or "").upper()
    if u == "PROPN":
        return "P"
    if u == "NOUN":
        return "N"
    if u == "VERB":
        return "V"
    if u == "AUX":
        return "A"
    if u == "ADJ":
        return "J"
    if u == "ADV":
        return "R"
    if u in {"DET", "PRON", "ADP", "CCONJ", "SCONJ", "PART", "INTJ"}:
        return "F"
    if u == "NUM":
        return "Q"
    if u in {"PUNCT", "SYM"}:
        return "S"
    if u in {"X"}:
        return "O"
    return None


def _map_lang_pos_to_pos10(lang: str, pos: str) -> Optional[str]:
    """
    Map tokmor unified analyzer POS labels to POS10.
    This is best-effort and intentionally conservative.
    """
    l = (lang or "").lower()
    p = (pos or "").strip()
    if not p:
        return None

    # Many tokmor dictionaries already store universal tags (NOUN/VERB/ADJ/ADV/PROPN/...)
    uni = _map_universal_to_pos10(p)
    if uni:
        return uni

    # Korean (Sejong-ish: NNG/NNP/VV/VA/MAG/J*/E*/X*)
    if l.startswith("ko"):
        base = p.split("+", 1)[0]
        if base.startswith("NNP"):
            return "P"
        if base.startswith("NN") or base in {"NP", "NR"}:
            return "N"
        if base in {"VV", "VX", "VCP", "VCN"}:
            return "V"
        if base in {"VA"}:
            return "J"
        if base in {"MAG", "MAJ"}:
            return "R"
        if base.startswith("J") or base.startswith("E") or base.startswith("X"):
            return "F"
        if base in {"SN"}:
            return "Q"
        if base.startswith("S"):
            return "S"
        if base in {"SL"}:
            return "O"
        return None

    # Japanese (labels contain: 名詞/固有名詞/動詞/助動詞/形容詞/副詞/助詞/記号/...)
    if l.startswith("ja"):
        if "固有名詞" in p:
            return "P"
        if "名詞" in p:
            return "N"
        if "助動詞" in p:
            return "A"
        if "動詞" in p:
            return "V"
        if "形容詞" in p:
            return "J"
        if "副詞" in p:
            return "R"
        if "助詞" in p or "接続詞" in p or "連体詞" in p:
            return "F"
        if "記号" in p:
            return "S"
        return None

    # Chinese (jieba-like: nr/ns/n/v/a/d/m/t/p/c/u/x/w ...)
    if l.startswith("zh"):
        if p in {"m"}:
            return "Q"
        if p in {"t"}:
            return "T"
        if p in {"nr", "ns", "nt"}:
            return "P"
        if p.startswith("n") or p in {"nz"}:
            return "N"
        if p.startswith("v"):
            return "V"
        if p.startswith("a"):
            return "J"
        if p in {"d"}:
            return "R"
        if p in {"p", "c", "u", "y", "e", "o"}:
            return "F"
        if p in {"w"}:
            return "S"
        if p in {"x"}:
            return "O"
        return None

    # English (Penn tags: NNP/NN/VB/VBZ/MD/JJ/RB/DT/IN/CC/TO/...)
    if l.startswith("en"):
        if p.startswith("NNP"):
            return "P"
        if p.startswith("NN") or p == "PRP":
            return "N"
        if p == "MD":
            return "A"
        if p.startswith("VB"):
            return "V"
        if p.startswith("JJ"):
            return "J"
        if p.startswith("RB"):
            return "R"
        if p in {"DT", "IN", "CC", "TO"}:
            return "F"
        if p == "CD":
            return "Q"
        return None

    return None


@lru_cache(maxsize=30000)
def guess_pos10_from_token_via_morph(lang: str, token: str) -> Optional[str]:
    """
    Analyze a token (standalone) using tokmor unified analyzer, then map morpheme POS to POS10.
    Returns None if uncertain.
    """
    t = token or ""
    if not t or len(t) > 64:
        return None

    # Deterministic token-shape overrides (helps UGC; avoids morphology quirks)
    if _is_punct(t):
        return "S"
    if _RX_DATE.match(t):
        return "T"
    if _is_number(t):
        return "Q"

    # Lazy import so tokmor-pos doesn't pay cost unless used.
    from tokmor.morphology.unified import get_unified_analyzer  # type: ignore

    an = get_unified_analyzer(lang)
    morphs = an.analyze(t)
    tags: list[str] = []
    for m in morphs:
        pos = getattr(m, "pos", "") or ""
        tag = _map_lang_pos_to_pos10(lang, pos)
        if tag in POS10_SET:
            tags.append(tag)
    if not tags:
        return None

    c = Counter(tags)
    top, top_n = c.most_common(1)[0]
    if top_n / len(tags) < 0.75:
        return None
    return top


def tag_pos10_lite(lang: str, tokens: Iterable[str]) -> list[str]:
    """
    POS tagger *without* a POS model: uses tokmor deterministic morphology as a hint layer.
    Emits POS10 tags or "UNK" when uncertain.
    """
    out: list[str] = []
    for tok in tokens:
        g = guess_pos10_from_token_via_morph(lang, tok)
        out.append(g if g else "UNK")
    return out

