from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, Tuple

from .coarse_pos8 import CoarsePOS8Tagger, POS8Result, default_pos8_rule_paths, heuristic_fallback_pos8, load_pos8_config
from .micro_crf_boundary import MicroCRFBoundary
from .morph_fallback import apply_morph_fallback
from .resources import load_extended_dict, load_extended_dict_force, resolve_microcrf_path
from .role4 import Role4Result, tag_role4_from_pos8
from .morph_pos10 import tag_pos10_lite as _tag_pos10_lite


@lru_cache(maxsize=64)
def get_pos8_tagger(lang: str) -> CoarsePOS8Tagger:
    paths = default_pos8_rule_paths()
    if lang not in paths:
        # Scales to "many languages": we do NOT ship 375 per-language rule files.
        # Instead, we provide a universal, script-gated rule set (high precision, abstaining).
        if "universal" in paths:
            return CoarsePOS8Tagger(load_pos8_config(paths["universal"]), abstain_below=0.80)
        raise FileNotFoundError(
            f"POS8 rules not bundled for lang={lang!r}. Provide --rules path explicitly (or add universal_v1.json)."
        )
    return CoarsePOS8Tagger(load_pos8_config(paths[lang]), abstain_below=0.80)


def tag_pos8(
    text: str,
    *,
    lang: str,
    tokens: Optional[List[str]] = None,
    rules_path: Optional[str] = None,
    morph_fallback: bool = False,
    use_extended_dict: bool = False,
    use_lexicon6: bool = False,
    ko_morph_viterbi: bool = False,
    reduce_unk: bool = True,
) -> List[POS8Result]:
    if tokens is None:
        # IMPORTANT: tokmor-pos must not invent its own tokenization.
        # When tokens are not provided, reuse TokMor's unified_tokenize() output so
        # tokmor + tokmor-pos stay consistent.
        from tokmor import unified_tokenize as _tokmor_unified  # type: ignore

        ut = _tokmor_unified(text, lang=lang, sns=True, include_pos4=False)
        tokens = [t.get("text", "") for t in (ut.get("tokens") or []) if isinstance(t, dict) and t.get("text")]
    tagger = CoarsePOS8Tagger(load_pos8_config(rules_path), abstain_below=0.80) if rules_path else get_pos8_tagger(lang)
    out = tagger.tag_tokens(tokens)

    # Auto-enable helpers when the corresponding packs are present.
    # This keeps the UX simple: users shouldn't have to know which flags to turn on.
    if not use_extended_dict:
        try:
            ext = load_extended_dict(lang)
            if ext:
                use_extended_dict = True
        except Exception:
            pass
    if not use_lexicon6:
        try:
            # If lexicon6 exists, enable it by default.
            from .lexicon6 import load_lexicon6  # lazy import

            import os
            if os.getenv("TOKMORPOS_DISABLE_LEXICON6", "").strip().lower() not in {"1", "true", "yes", "y", "on"}:
                if load_lexicon6(lang):
                    use_lexicon6 = True
        except Exception:
            pass
    if not ko_morph_viterbi and (lang or "").lower().startswith("ko"):
        # Enable Korean morph+Viterbi by default unless explicitly disabled.
        import os

        if os.getenv("TOKMORPOS_DISABLE_KO_MORPH_VITERBI", "").strip().lower() not in {"1", "true", "yes", "y", "on"}:
            ko_morph_viterbi = True

    if use_extended_dict:
        # Fill only UNK tokens using tokmor extended_dict (if available).
        # Map coarse tags -> POS8:
        #   NOUN/PROPN -> N
        #   VERB -> V
        #   ADJ/ADV -> M
        # Explicit opt-in should override TOKMOR_DISABLE_EXTENDED_DICT.
        ext = load_extended_dict_force(lang)
        if ext:
            mapped: List[POS8Result] = []
            for r in out:
                if r.tag != "UNK":
                    mapped.append(r)
                    continue
                t = r.token or ""
                # Prefer lowercase lookup for latin-like tokens.
                key = t.lower()
                v = ext.get(key) or ext.get(t)
                if v in {"NOUN", "PROPN"}:
                    mapped.append(POS8Result(token=t, tag="N", confidence=0.85, rule=f"extended_dict:{v}"))
                elif v == "VERB":
                    mapped.append(POS8Result(token=t, tag="V", confidence=0.85, rule=f"extended_dict:{v}"))
                elif v in {"ADJ", "ADV"}:
                    mapped.append(POS8Result(token=t, tag="M", confidence=0.85, rule=f"extended_dict:{v}"))
                else:
                    mapped.append(r)
            out = mapped

    if use_lexicon6:
        # Fill only UNK tokens using lexicon6 (if available).
        # This is optional and kept conservative to avoid overriding rule hits.
        try:
            from .lexicon6 import map_6pos_to_pos8, tag_lexicon6

            tagged6 = tag_lexicon6(tokens, lang=lang, use_viterbi=True)
            mapped2: List[POS8Result] = []
            for r, t6 in zip(out, tagged6):
                if r.tag != "UNK":
                    mapped2.append(r)
                    continue
                tag6, conf, src = t6
                tag8 = map_6pos_to_pos8(tag6)
                if tag8 in {"N", "V", "M", "F", "O"}:
                    mapped2.append(POS8Result(token=r.token, tag=tag8, confidence=max(0.80, float(conf)), rule=f"lexicon6:{src}:{tag6}"))
                else:
                    mapped2.append(r)
            out = mapped2
        except Exception:
            pass

    if ko_morph_viterbi and (lang or "").lower().startswith("ko"):
        # Kiwi-like: use TokMor Korean morphology to propose candidates + Viterbi, then fill UNK/low-confidence.
        try:
            from .ko_morph_viterbi import viterbi_tag_ko_6pos
            from .lexicon6 import map_6pos_to_pos8

            tagged6 = viterbi_tag_ko_6pos(tokens)
            mapped3: List[POS8Result] = []
            for r, t6 in zip(out, tagged6):
                tag6, conf, src = t6
                tag8 = map_6pos_to_pos8(tag6)
                if r.tag == "UNK" or float(r.confidence) < 0.82:
                    mapped3.append(POS8Result(token=r.token, tag=tag8, confidence=max(0.82, float(conf)), rule=f"ko_morph_viterbi:{src}:{tag6}"))
                else:
                    mapped3.append(r)
            out = mapped3
        except Exception:
            pass
    if morph_fallback:
        # Reduce UNK using tokmor's deterministic morphology labels (no training).
        tags2 = apply_morph_fallback(lang, tokens, [r.tag for r in out])
        out = [
            POS8Result(token=r.token, tag=t, confidence=r.confidence, rule=(r.rule if t == r.tag else "morph_fallback"))
            for r, t in zip(out, tags2)
        ]
    if reduce_unk:
        # Final UX pass: avoid huge UNK ratios by applying a deterministic heuristic fallback.
        # This only touches tokens still tagged as UNK.
        out = [
            (r if r.tag != "UNK" else heuristic_fallback_pos8(r.token, lang=lang))
            for r in out
        ]
    return out


def tag_pos8_with_microcrf(
    text: str,
    *,
    lang: str,
    tokens: Optional[List[str]] = None,
    rules_path: Optional[str] = None,
    microcrf_path: Optional[str] = None,
    morph_fallback: bool = False,
) -> Tuple[List[str], List[POS8Result], List[str]]:
    if tokens is None:
        from tokmor import get_tokenizer  # type: ignore

        tok = get_tokenizer(lang, use_morphology=False)
        tokens = tok.tokenize(text).texts()

    pos8 = tag_pos8(text, lang=lang, tokens=tokens, rules_path=rules_path, morph_fallback=morph_fallback)

    p = microcrf_path
    if not p:
        rp = resolve_microcrf_path(lang)
        p = str(rp) if rp else None
    if not p:
        raise FileNotFoundError("Micro-CRF model not found. Provide microcrf_path or set TOKMORPOS_DATA_DIR.")
    crf = MicroCRFBoundary.load(p)
    bio = crf.predict(tokens, pos8)
    return tokens, pos8, bio


def tag_role4(
    text: str,
    *,
    lang: str,
    tokens: Optional[List[str]] = None,
    rules_path: Optional[str] = None,
    morph_fallback: bool = False,
) -> List[Role4Result]:
    """
    Tag Role4 (ENTITY/ACTION/ATTRIBUTE/FUNCTION/UNK) plus minimal structure hint scores,
    derived deterministically from POS8 (optionally reducing UNK via morphology).
    """
    pos8 = tag_pos8(text, lang=lang, tokens=tokens, rules_path=rules_path, morph_fallback=morph_fallback)
    return tag_role4_from_pos8(pos8)


def tag_pos10_lite(
    text: str,
    *,
    lang: str,
    tokens: Optional[List[str]] = None,
) -> List[str]:
    """
    No-POS-model coarse tagging: derive POS10-ish tags using tokmor's deterministic morphology.
    Returns a list aligned to `tokens`, with items in {N,P,V,A,J,R,F,Q,T,S,O} or "UNK".
    """
    if tokens is None:
        from tokmor import get_tokenizer  # type: ignore

        tok = get_tokenizer(lang, use_morphology=False)
        tokens = tok.tokenize(text).texts()
    return _tag_pos10_lite(lang, tokens)


