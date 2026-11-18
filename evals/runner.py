"""CLI for the golden-set eval.

  python -m evals.runner --bot reference
  python -m evals.runner --bot reference-regressed --out reports/regressed
  python -m evals.runner --bot llm --judge          # needs API key(s)
  python -m evals.runner --bot llm --kb kb/snapshots/facts_2026-09.yaml   # stale-context experiment

Exit code 1 if the gate fails -> CI blocks the merge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bot import make_bot
from bot.dotenv import load_dotenv
from bot.kb import DEFAULT_KB, ROOT

from .engine import EvalEngine, facts_for_checks, load_cases
from .report import write_markdown


def main(argv=None) -> int:
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", default="reference", help="reference | reference-regressed | llm")
    ap.add_argument("--kb", default=None, help="KB file the BOT sees (checks always use the current KB)")
    ap.add_argument("--data", default=str(ROOT / "data" / "golden.yaml"))
    ap.add_argument("--out", default=None, help="output prefix, e.g. reports/baseline")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--category", nargs="*")
    ap.add_argument("--judge", action="store_true", help="add LLM-as-judge rubric scores (needs API key)")
    ap.add_argument("--no-gate", action="store_true", help="always exit 0 (for demo runs)")
    args = ap.parse_args(argv)

    bot = make_bot(args.bot, args.kb)
    judge = None
    if args.judge:
        from .judge import LLMJudge
        judge = LLMJudge()

    engine = EvalEngine(bot=bot, facts=facts_for_checks(DEFAULT_KB), judge=judge)
    cases = load_cases(Path(args.data), args.ids, args.category)
    payload = engine.run(cases, Path(args.data).name)

    out = Path(args.out or ROOT / "reports" / bot.name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(payload, out.with_suffix(".md"))

    s = payload["summary"]
    print(f"[{bot.name}] {s['passed']}/{s['total']} passed ({s['pass_rate']:.1%}), "
          f"critical failures: {len(s['critical_failures'])}, gate: {'PASS' if s['gate']['passed'] else 'FAIL'}")
    print(f"  -> {out.with_suffix('.md')}")
    return 0 if (s["gate"]["passed"] or args.no_gate) else 1


if __name__ == "__main__":
    sys.exit(main())
