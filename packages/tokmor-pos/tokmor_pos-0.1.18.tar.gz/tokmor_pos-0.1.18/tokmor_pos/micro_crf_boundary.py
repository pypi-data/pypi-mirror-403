from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import sklearn_crfsuite
except Exception:  # pragma: no cover
    sklearn_crfsuite = None

from .coarse_pos8 import CoarsePOS8Tagger, POS8Result, _script


def _shape(tok: str) -> str:
    out = []
    for ch in tok:
        if ch.isdigit():
            out.append("d")
        elif ch.isupper():
            out.append("A")
        elif ch.islower():
            out.append("a")
        elif ch.isalpha():
            out.append("L")
        else:
            out.append("x")
    # compress runs
    s = []
    for c in out:
        if not s or s[-1] != c:
            s.append(c)
    return "".join(s)[:12]


def _token_feats(tok: str, pos8: POS8Result) -> Dict[str, Any]:
    t = tok or ""
    return {
        "w": t,
        "w.lower": t.lower(),
        "len": min(20, len(t)),
        "shape": _shape(t),
        "script": _script(t),
        "has_digit": any(c.isdigit() for c in t),
        "is_upper": t.isupper() if t else False,
        "is_title": (t[:1].isupper() and t[1:].islower()) if t else False,
        "pos8": pos8.tag,
        "pos8_conf_ge_0.9": pos8.confidence >= 0.9,
    }


def _seq_feats(tokens: List[str], pos8_results: List[POS8Result]) -> List[Dict[str, Any]]:
    feats: List[Dict[str, Any]] = []
    for i, tok in enumerate(tokens):
        base = _token_feats(tok, pos8_results[i])
        if i == 0:
            base["BOS"] = True
        else:
            prev = _token_feats(tokens[i - 1], pos8_results[i - 1])
            base.update({f"-1:{k}": v for k, v in prev.items() if k in {"shape", "script", "pos8", "has_digit"}})
            base["script_switch-1"] = prev["script"] != base["script"]
        if i == len(tokens) - 1:
            base["EOS"] = True
        else:
            nxt = _token_feats(tokens[i + 1], pos8_results[i + 1])
            base.update({f"+1:{k}": v for k, v in nxt.items() if k in {"shape", "script", "pos8", "has_digit"}})
            base["script_switch+1"] = nxt["script"] != base["script"]
        feats.append(base)
    return feats


def extract_high_precision_bio(
    tokens: List[str],
    pos8_results: List[POS8Result],
    *,
    span_tags: Tuple[str, ...] = ("N", "T", "Q"),
    min_conf: float = 0.90,
    max_span_len: int = 6,
) -> Optional[List[str]]:
    """
    Auto-label from pattern POS results:
    - keep only spans we are highly confident about
    - everything else is O
    - if the line contains "too ambiguous" areas, return None (discard sample)
    """
    if len(tokens) != len(pos8_results):
        raise ValueError("tokens/pos8_results length mismatch")

    tags = [r.tag for r in pos8_results]
    conf = [r.confidence for r in pos8_results]

    # Discard lines with too many UNK: precision-first
    if sum(1 for t in tags if t == "UNK") / max(1, len(tags)) > 0.60:
        return None

    y = ["O"] * len(tokens)
    i = 0
    while i < len(tokens):
        if tags[i] in span_tags and conf[i] >= min_conf:
            j = i + 1
            while (
                j < len(tokens)
                and tags[j] == tags[i]
                and conf[j] >= min_conf
                and (j - i) < max_span_len
            ):
                j += 1
            y[i] = "B"
            for k in range(i + 1, j):
                y[k] = "I"
            i = j
            continue
        i += 1

    # If no positive spans, skip (keeps training balanced + useful)
    if "B" not in y:
        return None
    return y


@dataclass
class MicroCRFBoundary:
    """
    Micro-CRF used ONLY for boundary smoothing (BIO).
    It is not a POS tagger, not an entity classifier.
    """

    model: Any

    @staticmethod
    def available() -> bool:
        return sklearn_crfsuite is not None

    @classmethod
    def train(
        cls,
        sequences: Sequence[Tuple[List[str], List[POS8Result], List[str]]],
        *,
        c1: float = 0.05,
        c2: float = 0.05,
        max_iterations: int = 80,
    ) -> "MicroCRFBoundary":
        if sklearn_crfsuite is None:
            raise RuntimeError("sklearn-crfsuite is required for MicroCRFBoundary")
        X = [_seq_feats(toks, pos8) for toks, pos8, y in sequences]
        Y = [y for toks, pos8, y in sequences]
        crf = sklearn_crfsuite.CRF(
            algorithm="lbfgs",
            c1=c1,
            c2=c2,
            max_iterations=max_iterations,
            all_possible_transitions=False,
        )
        crf.fit(X, Y)
        return cls(model=crf)

    def predict(
        self,
        tokens: List[str],
        pos8_results: List[POS8Result],
    ) -> List[str]:
        X = _seq_feats(tokens, pos8_results)
        return list(self.model.predict_single(X))

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str) -> "MicroCRFBoundary":
        with open(path, "rb") as f:
            obj = pickle.load(f)
        if not isinstance(obj, cls):
            raise TypeError(f"Not a {cls.__name__}: {type(obj)}")
        return obj


def train_from_corpus_lines(
    lines: Iterable[str],
    *,
    tokenizer: Any,
    pos8_tagger: CoarsePOS8Tagger,
    max_samples: int = 5000,
) -> List[Tuple[List[str], List[POS8Result], List[str]]]:
    out: List[Tuple[List[str], List[POS8Result], List[str]]] = []
    for line in lines:
        if len(out) >= max_samples:
            break
        text = (line or "").strip()
        if not text:
            continue
        try:
            # TokMor TokenizerResult -> List[str]
            tr = tokenizer.tokenize(text)
            tokens = tr.texts() if hasattr(tr, "texts") else tr.tokens
        except Exception:
            tokens = text.split()
        if not tokens or len(tokens) > 80:
            continue
        # Defensive: allow Token objects
        if tokens and not isinstance(tokens[0], str) and hasattr(tokens[0], "text"):
            tokens = [t.text for t in tokens]
        pos8 = pos8_tagger.tag_tokens(tokens)
        y = extract_high_precision_bio(tokens, pos8)
        if not y:
            continue
        out.append((tokens, pos8, y))
    return out


