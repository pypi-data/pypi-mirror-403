from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Optional, Set


POS8_SET: Set[str] = {"N", "V", "M", "F", "Q", "T", "S", "O"}


def _map_ko(pos: str) -> Optional[str]:
    # Korean POS in tokmor.morphology.korean are Sejong-ish tags (NNG/JKS/VV/VA/...)
    if not pos:
        return None
    p = pos.split("+", 1)[0]
    if p.startswith("NN") or p in {"NP", "NR"}:
        return "N"
    if p in {"VV", "VX", "VCP", "VCN"}:
        return "V"
    if p in {"VA"}:
        return "M"
    if p.startswith("M"):  # MAG/MAJ
        return "M"
    if p.startswith("J") or p.startswith("E") or p.startswith("X"):
        return "F"
    if p in {"SN"}:
        return "Q"
    if p.startswith("S"):  # SF/SP/SS/SE/SO/SW
        return "S"
    if p in {"SL"}:
        return "O"
    return None


def _map_ja(pos: str) -> Optional[str]:
    # Japanese analyzer uses Japanese labels: 名詞/固有名詞/助詞/助動詞/形容詞/...
    if not pos:
        return None
    p = pos
    if "名詞" in p:
        return "N"
    if "動詞" in p or "助動詞" in p:
        return "V"
    if "形容詞" in p or "副詞" in p:
        return "M"
    if "助詞" in p or "接続詞" in p or "連体詞" in p:
        return "F"
    if "記号" in p:
        return "S"
    return None


def _map_zh(pos: str) -> Optional[str]:
    # Chinese analyzer uses jieba-like tags: n/v/a/d/m/t/p/c/u/x/ns/nr/...
    if not pos:
        return None
    p = pos
    if p in {"m"}:
        return "Q"
    if p in {"t"}:
        return "T"
    if p.startswith("n") or p in {"nz"}:
        return "N"
    if p.startswith("v"):
        return "V"
    if p.startswith("a") or p in {"d"}:
        return "M"
    if p in {"p", "c", "u", "y", "e", "o"}:
        return "F"
    if p in {"w"}:
        return "S"
    if p in {"x"}:
        return "O"
    return None


def _map_en(pos: str) -> Optional[str]:
    # English analyzer uses Penn tags: NN/NNS/NNP/VB/VBD/DT/IN/CC/RB/JJ/...
    if not pos:
        return None
    p = pos
    if p.startswith("NN") or p in {"PRP"}:
        return "N"
    if p.startswith("VB"):
        return "V"
    if p.startswith("JJ") or p.startswith("RB"):
        return "M"
    if p in {"DT", "IN", "CC", "TO"}:
        return "F"
    if p == "CD":
        return "Q"
    return None


def map_morph_pos_to_pos8(lang: str, pos: str) -> Optional[str]:
    l = (lang or "").lower()
    if l.startswith("ko"):
        return _map_ko(pos)
    if l.startswith("ja"):
        return _map_ja(pos)
    if l.startswith("zh"):
        return _map_zh(pos)
    if l.startswith("en"):
        return _map_en(pos)
    return None


@lru_cache(maxsize=20000)
def guess_pos8_from_token_via_morph(lang: str, token: str) -> Optional[str]:
    """
    Best-effort: analyze a token as a standalone string using tokmor's unified analyzer,
    then map morpheme POS labels to POS8 and pick the dominant tag.

    This is intentionally conservative: returns None if uncertain.
    """
    t = token or ""
    if not t or len(t) > 64:
        return None

    # Import lazily so tokmor-pos stays lightweight when the feature is unused.
    from tokmor.morphology.unified import get_unified_analyzer  # type: ignore

    an = get_unified_analyzer(lang)
    morphs = an.analyze(t)
    tags = []
    for m in morphs:
        p = getattr(m, "pos", "") or ""
        tag = map_morph_pos_to_pos8(lang, p)
        if tag in POS8_SET:
            tags.append(tag)
    if not tags:
        return None

    # Dominant tag; require a clear majority.
    # (We want to reduce UNK, but not by spraying wrong tags.)
    from collections import Counter

    c = Counter(tags)
    top, top_n = c.most_common(1)[0]
    if top_n / len(tags) < 0.75:
        return None
    return top


def apply_morph_fallback(lang: str, tokens: Iterable[str], tags: Iterable[str]) -> list[str]:
    """
    Replace UNK tags using token-level morphology guesses where available.
    """
    out: list[str] = []
    for tok, tag in zip(tokens, tags):
        if tag != "UNK":
            out.append(tag)
            continue
        g = guess_pos8_from_token_via_morph(lang, tok)
        out.append(g if g else "UNK")
    return out




