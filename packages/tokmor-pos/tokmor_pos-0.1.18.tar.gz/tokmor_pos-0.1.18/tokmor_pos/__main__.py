from __future__ import annotations

import argparse
import json
import sys

from .api import tag_pos8, tag_pos8_with_microcrf, tag_role4


def _cmd_pos8(args: argparse.Namespace) -> int:
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


def main(argv: list[str] | None = None) -> int:
    # Backward-compat alias (silent): allow `tokmor-pos ear ...` but do not expose it in help.
    # We implement this by rewriting argv before argparse sees it, so "ear" never appears
    # in the subcommand list / usage output.
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "ear":
        argv = ["hints"] + argv[1:]

    p = argparse.ArgumentParser(prog="tokmor-pos", description="TokMor POS8 structural hints + optional micro-CRF boundary smoother")
    sub = p.add_subparsers(dest="cmd", required=True)

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


