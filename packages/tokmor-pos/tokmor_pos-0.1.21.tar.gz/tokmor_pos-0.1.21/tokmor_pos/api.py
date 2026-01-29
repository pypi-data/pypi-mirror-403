from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, Tuple

from .coarse_pos8 import CoarsePOS8Tagger, POS8Result, _script, default_pos8_rule_paths, heuristic_fallback_pos8, load_pos8_config
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
    def _dominant_lang_from_text(_text: str, _lang: str) -> str:
        """
        Best-effort language override for Wikipedia/UGC where the declared language code
        often does not match the actual script of the content.

        We only switch when the script signal is very strong.
        """
        ll = (_lang or "").lower()
        if not _text:
            return _lang
        # Count alphabetic characters by script.
        total = 0
        by = {}
        for ch in _text:
            if not ch.isalpha():
                continue
            total += 1
            sc = _script(ch)
            by[sc] = int(by.get(sc, 0)) + 1
        if total < 12:
            return _lang
        def _r(sc: str) -> float:
            return float(by.get(sc, 0)) / float(max(1, total))
        # Prefer major taggers for major scripts.
        # Wikipedia messages often mix script with short Latin codes (e.g., "zh-cn", "U4C"),
        # so we use a slightly lower threshold plus an absolute-count guard.
        if not ll.startswith("zh") and (_r("han") >= 0.75) and (int(by.get("han", 0)) >= 20):
            return "zh"
        if not ll.startswith("ko") and (_r("hangul") >= 0.75) and (int(by.get("hangul", 0)) >= 12):
            return "ko"
        if not ll.startswith("ja") and ((_r("hiragana") + _r("katakana")) >= 0.75) and (int(by.get("hiragana", 0) + by.get("katakana", 0)) >= 12):
            return "ja"
        if not ll.startswith("ar") and (_r("arabic") >= 0.75) and (int(by.get("arabic", 0)) >= 12):
            return "ar"
        # Latin-heavy: treat as English for RC/UI text (best UX baseline)
        if ll not in {"en", "simple"} and _r("latin") >= 0.90:
            return "en"
        return _lang

    lang_tok = lang
    if tokens is None:
        # IMPORTANT: tokmor-pos must not invent its own tokenization.
        # When tokens are not provided, reuse TokMor's unified_tokenize() output so
        # tokmor + tokmor-pos stay consistent.
        from tokmor import unified_tokenize as _tokmor_unified  # type: ignore

        # If the declared lang doesn't match the script (common in Wikipedia RC),
        # tokenize using the dominant-script language for better segmentation + downstream tagging.
        lang_tok = _dominant_lang_from_text(text, lang)
        ut = _tokmor_unified(text, lang=lang_tok, sns=True, include_pos4=False)
        tokens = [t.get("text", "") for t in (ut.get("tokens") or []) if isinstance(t, dict) and t.get("text")]

    # If the incoming "lang" is a low-resource wiki language but the content is overwhelmingly one script,
    # it's often "copied" UI / template / RC metadata in a major language (English/Chinese/Japanese/Korean/Arabic).
    # In that scenario, tagging with the corresponding major-language rule pack yields far better UX than
    # collapsing to N via per-lang fallbacks.
    # If we already overrode tokenization language due to strong script signal,
    # reuse that for tagging as well (otherwise lexicon6/rules will still use the wrong lang).
    lang_eff = lang_tok or lang
    try:
        ll = (lang or "").lower()
        if ll and tokens:
            # Count only "word-like" tokens (must contain at least one letter).
            # Wikipedia RC text often includes lots of numbers/punct/ids; those should not block an English override.
            n_words = 0
            n_by_script = {}
            for t in tokens:
                if not isinstance(t, str) or not t:
                    continue
                if not any(ch.isalpha() for ch in t):
                    continue
                n_words += 1
                sc = _script(t)
                n_by_script[sc] = int(n_by_script.get(sc, 0)) + 1

            if n_words >= 2:
                def _ratio(sc: str) -> float:
                    return float(n_by_script.get(sc, 0)) / float(max(1, n_words))

                # Latin-heavy -> English (best effort for mixed Latin content; protects UX on RC strings)
                if ll not in {"en", "simple"} and _ratio("latin") >= 0.82:
                    lang_eff = "en"
                # Han-heavy -> Chinese
                elif not ll.startswith("zh") and _ratio("han") >= 0.82:
                    lang_eff = "zh"
                # Hangul-heavy -> Korean
                elif not ll.startswith("ko") and _ratio("hangul") >= 0.82:
                    lang_eff = "ko"
                # Kana-heavy -> Japanese
                elif not ll.startswith("ja") and (_ratio("hiragana") + _ratio("katakana")) >= 0.82:
                    lang_eff = "ja"
                # Arabic-heavy -> Arabic
                elif not ll.startswith("ar") and _ratio("arabic") >= 0.82:
                    lang_eff = "ar"
    except Exception:
        lang_eff = lang

    tagger = CoarsePOS8Tagger(load_pos8_config(rules_path), abstain_below=0.80) if rules_path else get_pos8_tagger(lang_eff)
    out = tagger.tag_tokens(tokens)

    # Auto-enable helpers when the corresponding packs are present.
    # This keeps the UX simple: users shouldn't have to know which flags to turn on.
    if not use_extended_dict:
        try:
            ext = load_extended_dict(lang_eff)
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
                if load_lexicon6(lang_eff):
                    use_lexicon6 = True
        except Exception:
            pass
    if not ko_morph_viterbi and (lang or "").lower().startswith("ko") and (lang_eff or "").lower().startswith("ko"):
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
        ext = load_extended_dict_force(lang_eff)
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

            tagged6 = tag_lexicon6(tokens, lang=lang_eff, use_viterbi=True)
            mapped2: List[POS8Result] = []
            for r, t6 in zip(out, tagged6):
                if r.tag != "UNK":
                    mapped2.append(r)
                    continue
                tag6, conf, src = t6
                tag8 = map_6pos_to_pos8(tag6)
                if tag8 in {"N", "V", "M", "F", "O"}:
                    mapped2.append(POS8Result(token=r.token, tag=tag8, confidence=max(0.80, float(conf)), rule=f"lexicon6[{lang_eff}]:{src}:{tag6}"))
                else:
                    mapped2.append(r)
            out = mapped2
        except Exception:
            pass

    # Mixed-language UX pass:
    # If we're tagging a non-English language but the text contains Latin-script words,
    # it's usually English names/phrases. For low-resource languages, the per-lang lexicon6
    # coverage may be sparse, causing English tokens to collapse to N.
    # Re-tag only Latin-script tokens using the English rule pack + English lexicon6.
    if tokens and (lang or "").lower() not in {"en", "simple"}:
        try:
            idx = [i for i, t in enumerate(tokens) if isinstance(t, str) and t and _script(t) == "latin"]
            if idx:
                toks_lat = [tokens[i] for i in idx]

                # 1) English rule pack (high precision, abstaining)
                try:
                    en_rule = get_pos8_tagger("en").tag_tokens(toks_lat)
                except Exception:
                    en_rule = [POS8Result(token=t, tag="UNK", confidence=0.0, rule="") for t in toks_lat]

                # 2) English lexicon6 (coverage)
                try:
                    from .lexicon6 import map_6pos_to_pos8, tag_lexicon6

                    en6 = tag_lexicon6(toks_lat, lang="en", use_viterbi=True)
                    en_lex = []
                    for t, (tag6, conf, src) in zip(toks_lat, en6):
                        tag8 = map_6pos_to_pos8(tag6)
                        en_lex.append(
                            POS8Result(
                                token=t,
                                tag=tag8 if tag8 in {"N", "V", "M", "F", "O"} else "UNK",
                                confidence=max(0.82, float(conf)),
                                rule=f"mixed_en_lexicon6:{src}:{tag6}",
                            )
                        )
                except Exception:
                    en_lex = [POS8Result(token=t, tag="UNK", confidence=0.0, rule="") for t in toks_lat]

                # 3) Apply improvements conservatively (avoid overriding strong existing hits)
                out2: List[POS8Result] = list(out)
                for j, i in enumerate(idx):
                    cur = out2[i]
                    r_rule = en_rule[j]
                    r_lex = en_lex[j]

                    # pick best candidate
                    # Prefer high-precision English rules for FUNCTION/ACTION/ATTRIBUTE signals.
                    cand = r_rule
                    try:
                        rule_conf = float(getattr(r_rule, "confidence", 0.0) or 0.0)
                        lex_conf = float(getattr(r_lex, "confidence", 0.0) or 0.0)
                    except Exception:
                        rule_conf = 0.0
                        lex_conf = 0.0

                    if r_rule.tag in {"V", "M", "F"} and rule_conf >= 0.90:
                        cand = r_rule
                    elif r_rule.tag == "UNK" and r_lex.tag != "UNK":
                        cand = r_lex
                    elif r_lex.tag == "UNK":
                        cand = r_rule
                    elif (r_rule.tag != r_lex.tag) and (r_rule.tag in {"V", "M", "F"}) and (r_lex.tag == "N"):
                        # Avoid lexicon collapsing function/content cues back to N (common in noisy lexicons).
                        cand = r_rule
                    elif lex_conf > rule_conf + 0.08:
                        cand = r_lex

                    if cand.tag == "UNK":
                        continue

                    cur_conf = float(getattr(cur, "confidence", 0.0) or 0.0)
                    cand_conf = float(getattr(cand, "confidence", 0.0) or 0.0)

                    # Override conditions:
                    # - UNK always gets filled
                    # - N/O from weak heuristics may be replaced by stronger V/M/F signals
                    # - Do not override very confident tags (rule hits / ko_morph_viterbi, etc.)
                    if cur.tag == "UNK":
                        out2[i] = POS8Result(token=cur.token, tag=cand.tag, confidence=cand_conf, rule=cand.rule)
                        continue
                    if cur_conf >= 0.90:
                        continue
                    if cur.tag in {"N", "O"} and cand.tag in {"V", "M", "F"} and cand_conf >= 0.82:
                        out2[i] = POS8Result(token=cur.token, tag=cand.tag, confidence=max(cur_conf, cand_conf), rule=cand.rule)
                        continue
                    if (cand.tag != cur.tag) and (cand.tag != "N") and (cand_conf - cur_conf >= 0.10):
                        out2[i] = POS8Result(token=cur.token, tag=cand.tag, confidence=cand_conf, rule=cand.rule)
                        continue

                out = out2
        except Exception:
            # Never fail tagging due to this UX-only pass.
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


