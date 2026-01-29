from __future__ import annotations

import argparse
import json
import sys

from .ear import ear_tag_text
from .axes import tag_axes_text
from .install_parson_mini import install_wikiparson_mini


def _cmd_pos8(args: argparse.Namespace) -> int:
    try:
        from .api import tag_pos8  # type: ignore
    except Exception as e:
        print(json.dumps({"error": "pos8_unavailable", "detail": str(e)}), file=sys.stderr)
        return 2
    out = tag_pos8(
        args.text,
        lang=args.lang,
        rules_path=args.rules,
        morph_fallback=bool(getattr(args, "morph_fallback", False)),
        use_extended_dict=bool(getattr(args, "extended_dict", False)),
        use_lexicon6=bool(getattr(args, "lexicon6", False)),
        ko_morph_viterbi=bool(getattr(args, "ko_morph_viterbi", False)),
        reduce_unk=not bool(getattr(args, "keep_unk", False)),
    )
    payload = {"lang": args.lang, "tokens": [{"text": r.token, "pos8": r.tag, "conf": float(r.confidence)} for r in out]}
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_micro(args: argparse.Namespace) -> int:
    try:
        from .api import tag_pos8_with_microcrf  # type: ignore
    except Exception as e:
        print(json.dumps({"error": "micro_unavailable", "detail": str(e)}), file=sys.stderr)
        return 2
    toks, pos8, bio = tag_pos8_with_microcrf(
        args.text, lang=args.lang, rules_path=args.rules, microcrf_path=args.model, morph_fallback=bool(getattr(args, "morph_fallback", False))
    )
    payload = {
        "lang": args.lang,
        "tokens": [{"text": t, "pos8": p.tag, "bio": b} for t, p, b in zip(toks, pos8, bio)],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_role4(args: argparse.Namespace) -> int:
    try:
        from .api import tag_role4  # type: ignore
    except Exception as e:
        print(json.dumps({"error": "role4_unavailable", "detail": str(e)}), file=sys.stderr)
        return 2
    out = tag_role4(args.text, lang=args.lang, rules_path=args.rules, morph_fallback=bool(getattr(args, "morph_fallback", False)))
    # User-facing name: "hints" (avoid leaking internal terminology).
    payload = {
        "lang": args.lang,
        "tokens": [
            {
                "text": r.token,
                "role4": r.role4,
                "hints": {"e": float(r.e), "a": float(r.a), "r": float(r.r)},
                "evidence": {"pos8": r.pos8, "rule": r.pos8_rule},
                "source": r.source,
            }
            for r in out
        ],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_hints(args: argparse.Namespace) -> int:
    # Output-only: deterministic structure hint scores derived from POS8 (optionally with morph fallback).
    try:
        from .api import tag_role4  # type: ignore
    except Exception as e:
        print(json.dumps({"error": "hints_unavailable", "detail": str(e)}), file=sys.stderr)
        return 2
    out = tag_role4(args.text, lang=args.lang, rules_path=args.rules, morph_fallback=bool(getattr(args, "morph_fallback", False)))
    payload = {
        "lang": args.lang,
        "tokens": [
            {"text": r.token, "hints": {"e": float(r.e), "a": float(r.a), "r": float(r.r)}, "evidence": {"pos8": r.pos8, "rule": r.pos8_rule}, "source": r.source}
            for r in out
        ],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_ear(args: argparse.Namespace) -> int:
    out = ear_tag_text(args.text, lang=args.lang, picky=not bool(getattr(args, "no_picky", False)), e_min_conf=float(getattr(args, "e_min_conf", 0.25)))
    payload = {
        "lang": args.lang,
        "tokens": [{"text": t.text, "ear": t.ear, "meta": t.meta} for t in out],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_axes(args: argparse.Namespace) -> int:
    out = tag_axes_text(args.text, lang=args.lang)
    payload = {
        "lang": args.lang,
        "tokens": [{"text": t.text, "axes": t.axes, "method": t.method, "ear_hint": t.ear_hint} for t in out],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def _cmd_install_mini(args: argparse.Namespace) -> int:
    dest = install_wikiparson_mini(src=args.src, sha256=getattr(args, "sha256", None), dest_dir=getattr(args, "dest", None))
    payload = {
        "status": "ok",
        "installed_to": str(dest),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    p = argparse.ArgumentParser(prog="tokmor-pos", description="TokMor POS = EAR (Existence/Action/Relation) + optional ParSon axes")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ear = sub.add_parser("ear", help="TokMor POS = EAR tagging (E/A/R + blank allowed)")
    p_ear.add_argument("--lang", required=True)
    p_ear.add_argument("--text", required=True)
    p_ear.add_argument("--e-min-conf", dest="e_min_conf", type=float, default=0.25, help="min confidence for entity (when PPMIClassifierV2 is available)")
    p_ear.add_argument("--no-picky", action="store_true", help="do not abstain; fall back to E on unknown tokens")
    p_ear.set_defaults(func=_cmd_ear)

    p_axes = sub.add_parser("axes", help="Tag ParSon axes (P/A/R/S/O/N) + derived EAR hint (blank allowed)")
    p_axes.add_argument("--lang", required=True)
    p_axes.add_argument("--text", required=True)
    p_axes.set_defaults(func=_cmd_axes)

    p_inst = sub.add_parser("install-parson-mini", help="Install WikiParSon mini (.parson) bundle into ~/parson_final/wikiparson_mini")
    p_inst.add_argument("--src", required=True, help="Path or URL to wikiparson_mini_*.tar.gz (or .tar.zst)")
    p_inst.add_argument("--sha256", default=None, help="Optional SHA256 to verify")
    p_inst.add_argument("--dest", default=None, help="Override destination directory (default: ~/parson_final/wikiparson_mini)")
    p_inst.set_defaults(func=_cmd_install_mini)

    p_pos8 = sub.add_parser("pos8", help="Tag POS8 structural roles (pattern-based, abstaining)")
    p_pos8.add_argument("--lang", required=True)
    p_pos8.add_argument("--text", required=True)
    p_pos8.add_argument("--rules", default=None, help="optional POS8 rules path; defaults to bundled rules if available")
    p_pos8.add_argument("--morph-fallback", action="store_true", help="reduce UNK using tokmor morphology (deterministic)")
    p_pos8.add_argument(
        "--extended-dict",
        dest="extended_dict",
        action="store_true",
        help="fill UNK using TOKMOR_DATA_DIR/extended_dict/{lang}_extended.json when available",
    )
    p_pos8.add_argument(
        "--lexicon6",
        dest="lexicon6",
        action="store_true",
        help="fill UNK using TOKMOR_DATA_DIR/lexicon6/{lang}.json when available (optional Viterbi)",
    )
    p_pos8.add_argument(
        "--keep-unk",
        dest="keep_unk",
        action="store_true",
        help="do not apply heuristic fallback; keep UNK when the rule tagger abstains",
    )
    p_pos8.add_argument(
        "--ko-morph-viterbi",
        dest="ko_morph_viterbi",
        action="store_true",
        help="Korean-only: use TokMor morphology candidates + Viterbi (Kiwi-like). Enabled by default unless TOKMORPOS_DISABLE_KO_MORPH_VITERBI is set.",
    )
    p_pos8.set_defaults(func=_cmd_pos8)

    p_micro = sub.add_parser("micro", help="Apply POS8 + micro-CRF boundary smoothing (BIO)")
    p_micro.add_argument("--lang", required=True)
    p_micro.add_argument("--text", required=True)
    p_micro.add_argument("--rules", default=None, help="optional POS8 rules path")
    p_micro.add_argument("--model", default=None, help="optional micro-CRF model path")
    p_micro.add_argument("--morph-fallback", action="store_true", help="reduce UNK using tokmor morphology (deterministic)")
    p_micro.set_defaults(func=_cmd_micro)

    p_role4 = sub.add_parser("role4", help="Tag Role4 (ENTITY/ACTION/ATTRIBUTE/FUNCTION) + structure hint scores")
    p_role4.add_argument("--lang", required=True)
    p_role4.add_argument("--text", required=True)
    p_role4.add_argument("--rules", default=None, help="optional POS8 rules path; defaults to bundled rules if available")
    p_role4.add_argument("--morph-fallback", action="store_true", help="reduce UNK using tokmor morphology (deterministic)")
    p_role4.set_defaults(func=_cmd_role4)

    p_hints = sub.add_parser("hints", help="Output structure hint scores (e/a/r) derived from POS8")
    p_hints.add_argument("--lang", required=True)
    p_hints.add_argument("--text", required=True)
    p_hints.add_argument("--rules", default=None, help="optional POS8 rules path; defaults to bundled rules if available")
    p_hints.add_argument("--morph-fallback", action="store_true", help="reduce UNK using tokmor morphology (deterministic)")
    p_hints.set_defaults(func=_cmd_hints)

    args = p.parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as e:
        print(f"[tokmor-pos] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


