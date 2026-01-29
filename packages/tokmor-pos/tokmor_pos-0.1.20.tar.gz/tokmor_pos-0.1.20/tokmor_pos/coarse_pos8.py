from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# Coarse structural POS tags (NOT linguistic POS)
POS8: Tuple[str, ...] = ("N", "V", "M", "F", "Q", "T", "S", "O")


def _is_punct(tok: str) -> bool:
    return bool(tok) and all(not ch.isalnum() for ch in tok)


def _is_number(tok: str) -> bool:
    if not tok:
        return False
    t = tok.replace(",", "").replace("_", "")
    t = t.replace("-", "", 1)
    t = t.replace(".", "", 1)
    return t.isdigit()


def _script(tok: str) -> str:
    if not tok:
        return "other"
    c = tok[0]
    if "\uac00" <= c <= "\ud7af":
        return "hangul"
    if "\u4e00" <= c <= "\u9fff":
        return "han"
    if "\u3040" <= c <= "\u309f":
        return "hiragana"
    if "\u30a0" <= c <= "\u30ff":
        return "katakana"
    if "\u0600" <= c <= "\u06ff":
        return "arabic"
    if "\u1200" <= c <= "\u137f":
        return "ethiopic"
    # Use Unicode names to detect common scripts without misclassifying (e.g., Devanagari).
    # This stays lightweight and avoids external deps.
    try:
        nm = unicodedata.name(c, "")
        if nm.startswith("LATIN "):
            return "latin"
        if nm.startswith("CYRILLIC "):
            return "cyrillic"
        if nm.startswith("GREEK "):
            return "greek"
        if nm.startswith("HEBREW "):
            return "hebrew"
        if nm.startswith("ETHIOPIC "):
            return "ethiopic"
        if nm.startswith("DEVANAGARI "):
            return "devanagari"
        if nm.startswith("BENGALI "):
            return "bengali"
        if nm.startswith("GUJARATI "):
            return "gujarati"
        if nm.startswith("TAMIL "):
            return "tamil"
        if nm.startswith("TELUGU "):
            return "telugu"
        if nm.startswith("THAI "):
            return "thai"
    except Exception:
        pass
    return "other"


def heuristic_fallback_pos8(tok: str, *, lang: str = "auto") -> POS8Result:
    """
    Deterministic, dependency-free fallback to avoid UNK explosion.

    This is intentionally *low confidence* and only meant to be used when the rule tagger abstains.
    """
    t = tok or ""
    if not t:
        return POS8Result(token=t, tag="O", confidence=0.50, rule="fallback:empty")

    # These should already be handled by deterministic globals, but keep them here for safety.
    if _is_punct(t):
        return POS8Result(token=t, tag="S", confidence=0.80, rule="fallback:punct")
    if _is_number(t):
        return POS8Result(token=t, tag="Q", confidence=0.80, rule="fallback:number")
    if _RX_DATE.match(t):
        return POS8Result(token=t, tag="T", confidence=0.80, rule="fallback:time")

    sc = _script(t)
    tl = t.lower()

    # Latin heuristics (very lightweight; avoids obvious failures like "running"/"visited").
    if sc == "latin":
        if t[:1].isupper():
            return POS8Result(token=t, tag="N", confidence=0.80, rule="fallback:latin:title")
        if len(tl) >= 4 and (tl.endswith("ing") or tl.endswith("ed")):
            return POS8Result(token=t, tag="V", confidence=0.80, rule="fallback:latin:verb_suffix")
        if len(tl) >= 4 and tl.endswith("ly"):
            return POS8Result(token=t, tag="M", confidence=0.80, rule="fallback:latin:adv_suffix")
        if len(tl) >= 3 and (tl.endswith("ous") or tl.endswith("ive") or tl.endswith("al") or tl.endswith("ic")):
            return POS8Result(token=t, tag="M", confidence=0.80, rule="fallback:latin:adj_suffix")

    # Script-based fallback: most "word-like" tokens become N; symbols/emoji become O.
    # We detect "word-like" by Unicode category of characters.
    has_letter = False
    has_mark = False
    for ch in t:
        cat = unicodedata.category(ch)
        if cat and cat[0] == "L":
            has_letter = True
        elif cat and cat[0] == "M":
            has_mark = True
    if has_letter or has_mark:
        return POS8Result(token=t, tag="N", confidence=0.80, rule=f"fallback:{sc}:word")

    return POS8Result(token=t, tag="O", confidence=0.80, rule=f"fallback:{sc}:other")


# ISO-like date or time token (deterministic global)
# Examples:
#   - 2026-01-15
#   - 2026/1/5
#   - 12:30
#   - 12:30:59
_RX_DATE = re.compile(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}:\d{2}(:\d{2})?)$")


def _is_year(tok: str) -> bool:
    return bool(tok) and tok.isdigit() and len(tok) == 4


def _is_1_2_digit(tok: str) -> bool:
    return bool(tok) and tok.isdigit() and (1 <= len(tok) <= 2)


def _apply_time_sequence(tokens: List[str], results: List["POS8Result"]) -> List["POS8Result"]:
    """
    Sequence-aware time/date tagging.

    UD tokenization often splits ISO dates:
      2025 - 01 - 10
    This post-pass marks the digit components as T (time/date) deterministically.
    Delimiters stay as punctuation S (already handled by tag_token).
    """
    if not tokens or not results or len(tokens) != len(results):
        return results

    out = list(results)

    i = 0
    n = len(tokens)
    while i < n:
        # Date: YYYY - MM - DD  (also allow /)
        if i + 4 < n:
            t0, t1, t2, t3, t4 = tokens[i : i + 5]
            if _is_year(t0) and t1 in {"-", "/"} and _is_1_2_digit(t2) and t3 in {"-", "/"} and _is_1_2_digit(t4):
                for j in (i, i + 2, i + 4):
                    out[j] = POS8Result(token=tokens[j], tag="T", confidence=0.92, rule="time_seq")
                i += 5
                continue

        # Time: HH : MM  (and optional : SS) with colon tokenized separately
        if i + 2 < n:
            t0, t1, t2 = tokens[i : i + 3]
            if _is_1_2_digit(t0) and t1 == ":" and _is_1_2_digit(t2):
                out[i] = POS8Result(token=t0, tag="T", confidence=0.92, rule="time_seq")
                out[i + 2] = POS8Result(token=t2, tag="T", confidence=0.92, rule="time_seq")
                # optional seconds
                if i + 4 < n and tokens[i + 3] == ":" and _is_1_2_digit(tokens[i + 4]):
                    out[i + 4] = POS8Result(token=tokens[i + 4], tag="T", confidence=0.92, rule="time_seq")
                    i += 5
                else:
                    i += 3
                continue

        i += 1

    return out


@dataclass(frozen=True)
class POS8Rule:
    """
    One high-precision rule.

    type:
      - exact: token.lower() == value
      - suffix/prefix: token.lower().endswith/startswith(value)
      - regex: regex.match(token)
      - title: token is title-cased (first letter upper, rest lower)
      - allcaps: token is all-uppercase (latin script only; high precision)
    """

    type: str
    value: str
    tag: str  # one of POS8
    score: float = 1.0
    min_len: int = 1
    scripts: Optional[List[str]] = None  # if set, only apply when token script in this list


@dataclass(frozen=True)
class POS8Config:
    lang: str
    rules: Sequence[POS8Rule]


@dataclass
class POS8Result:
    token: str
    tag: str  # POS8 or "UNK"
    confidence: float
    rule: str


def _resolve_include_path(base_dir: Path, inc: str) -> Path:
    """
    Resolve an include reference from a POS8 rule JSON.

    Supported:
      - absolute paths
      - relative paths (relative to the including file)
      - "@rulesets/<name>.json" (bundled under tokmor_pos/pos8_rulesets/)
    """
    s = (inc or "").strip()
    if not s:
        raise ValueError("empty include entry")
    if s.startswith("@rulesets/"):
        here = Path(__file__).resolve().parent
        return (here / "pos8_rulesets" / s[len("@rulesets/") :]).resolve()
    p = Path(s)
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def load_pos8_config(path: str, *, _seen: Optional[Set[str]] = None) -> POS8Config:
    """
    Load a POS8Config JSON.

    The JSON may optionally include:
      - include: ["@rulesets/latin_v1.json", "./extra_rules.json", ...]

    Included files are loaded first, then local rules are appended.
    """
    p = Path(path).resolve()
    seen = set(_seen or set())
    key = str(p)
    if key in seen:
        raise ValueError(f"cycle detected in POS8 rule includes: {key}")
    seen.add(key)

    data = json.loads(p.read_text("utf-8"))
    lang = str(data.get("lang", "auto"))

    rules: List[POS8Rule] = []
    base_dir = p.parent
    for inc in data.get("include", []) or []:
        ip = _resolve_include_path(base_dir, str(inc))
        cfg_inc = load_pos8_config(str(ip), _seen=seen)
        rules.extend(list(cfg_inc.rules))

    rules.extend([POS8Rule(**r) for r in data.get("rules", [])])

    # Light de-dupe to prevent accidental bloat when composing rule sets.
    # Keeps first occurrence to preserve intended precedence.
    out: List[POS8Rule] = []
    seen_rule = set()
    for r in rules:
        sig = (
            r.type,
            r.value,
            r.tag,
            float(r.score),
            int(r.min_len),
            tuple(r.scripts) if r.scripts else None,
        )
        if sig in seen_rule:
            continue
        seen_rule.add(sig)
        out.append(r)

    return POS8Config(lang=lang, rules=out)


class CoarsePOS8Tagger:
    """
    Pattern-based POS8 tagger. High precision, abstains (returns UNK) when uncertain.
    """

    def __init__(self, cfg: POS8Config, *, abstain_below: float = 0.80):
        self.cfg = cfg
        self.abstain_below = float(abstain_below)
        self._rx: Dict[str, re.Pattern] = {}
        for r in cfg.rules:
            if r.type == "regex" and r.value not in self._rx:
                self._rx[r.value] = re.compile(r.value)

    def tag_token(self, tok: str) -> POS8Result:
        t = tok or ""
        tl = t.lower()
        sc = _script(t)

        # Deterministic globals
        if _is_punct(t):
            return POS8Result(token=t, tag="S", confidence=0.99, rule="punct")
        if _is_number(t):
            return POS8Result(token=t, tag="Q", confidence=0.95, rule="number")
        if _RX_DATE.match(t):
            return POS8Result(token=t, tag="T", confidence=0.92, rule="time")

        best = POS8Result(token=t, tag="UNK", confidence=0.0, rule="")
        best_score = 0.0

        for r in self.cfg.rules:
            if len(t) < int(r.min_len):
                continue
            if r.scripts and sc not in set(r.scripts):
                continue
            ok = False
            if r.type == "exact":
                ok = (tl == r.value)
            elif r.type == "suffix":
                ok = tl.endswith(r.value) and len(tl) > len(r.value)
            elif r.type == "prefix":
                ok = tl.startswith(r.value) and len(tl) > len(r.value)
            elif r.type == "regex":
                ok = bool(self._rx[r.value].match(t))
            elif r.type == "title":
                ok = bool(t) and t[:1].isupper() and t[1:].islower()
            elif r.type == "allcaps":
                ok = bool(t) and t.isupper()
            if not ok:
                continue
            score = float(r.score)
            if score > best_score:
                best_score = score
                conf = min(0.99, 0.5 + 0.5 * score)
                best = POS8Result(token=t, tag=r.tag, confidence=conf, rule=f"{r.type}:{r.value}")

        if best.tag != "UNK" and best.confidence < self.abstain_below:
            return POS8Result(token=t, tag="UNK", confidence=0.0, rule="")
        return best

    def tag_tokens(self, tokens: List[str]) -> List[POS8Result]:
        # 1) per-token tagging
        out = [self.tag_token(t) for t in tokens]
        # 2) lightweight sequence-aware fixups (date/time)
        return _apply_time_sequence(tokens, out)

    @staticmethod
    def tags_only(results: List[POS8Result]) -> List[str]:
        return [r.tag for r in results]


def default_pos8_rule_paths() -> Dict[str, str]:
    """
    Dev helper: locate bundled rules when running from source tree.
    """
    here = Path(__file__).resolve().parent
    d = here / "pos8_rules"
    out: Dict[str, str] = {}
    if not d.exists():
        return out

    # Discover all bundled rule packs dynamically (scales beyond a hard-coded list).
    # Expected filenames: {lang}_v1.json and universal_v1.json.
    for p in d.glob("*_v1.json"):
        name = p.stem  # e.g. "en_v1", "universal_v1"
        lang = name.split("_")[0]
        if not lang:
            continue
        out[lang] = str(p.resolve())
    return out


