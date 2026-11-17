"""Diff two eval runs: what regressed, what improved. Use after any prompt/model/KB change.

  python -m evals.compare reports/baseline.json reports/regressed.json --out reports/comparison.md
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path


def _pct(x):
    return "-" if x is None else f"{x:.0%}"


@dataclass
class RunDiff:
    markdown: str
    regressions: list[str]
    fixes: list[str]


def compare(a: dict, b: dict) -> RunDiff:
    ra = {r["id"]: r for r in a["results"]}
    rb = {r["id"]: r for r in b["results"]}
    common = sorted(set(ra) & set(rb))
    regressions = [i for i in common if ra[i]["passed"] and not rb[i]["passed"]]
    fixes = [i for i in common if not ra[i]["passed"] and rb[i]["passed"]]
    sa, sb = a["summary"], b["summary"]

    L = [f"# Comparison: `{a['bot']}` → `{b['bot']}`", "",
         "| Metric | Before | After | Δ |", "|---|---:|---:|---:|",
         f"| Pass rate | {_pct(sa['pass_rate'])} | {_pct(sb['pass_rate'])} | "
         f"{(sb['pass_rate'] - sa['pass_rate']) * 100:+.0f} pp |",
         f"| Critical failures | {len(sa['critical_failures'])} | {len(sb['critical_failures'])} | "
         f"{len(sb['critical_failures']) - len(sa['critical_failures']):+d} |",
         f"| Gate | {'PASS' if sa['gate']['passed'] else 'FAIL'} | {'PASS' if sb['gate']['passed'] else 'FAIL'} | |",
         "", "## By category", "", "| Category | Before | After | Δ |", "|---|---:|---:|---:|"]
    for cat in sorted(set(sa["by_category"]) | set(sb["by_category"])):
        x = sa["by_category"].get(cat, {}).get("pass_rate")
        y = sb["by_category"].get(cat, {}).get("pass_rate")
        d = "" if x is None or y is None else f"{(y - x) * 100:+.0f} pp"
        L.append(f"| {cat} | {_pct(x)} | {_pct(y)} | {d} |")

    L += ["", f"## Regressions ({len(regressions)})", ""]
    for i in regressions:
        failed = [f"`{c['name']}` ({c['detail']})" for c in rb[i]["checks"] if not c["passed"]]
        sev = "🔴" if rb[i]["severity"] == "critical" else "🟠"
        L.append(f"- {sev} **{i}** [{rb[i]['category']}/{rb[i]['language']}]: " + "; ".join(failed))
    L += ["", f"## Fixed ({len(fixes)})", ""] + [f"- {i}" for i in fixes]
    return RunDiff("\n".join(L) + "\n", regressions, fixes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--out")
    ap.add_argument("--fail-on-regression", action="store_true")
    args = ap.parse_args(argv)
    a = json.loads(Path(args.before).read_text(encoding="utf-8"))
    b = json.loads(Path(args.after).read_text(encoding="utf-8"))
    diff = compare(a, b)
    if args.out:
        Path(args.out).write_text(diff.markdown, encoding="utf-8")
    print(diff.markdown)
    return 1 if (diff.regressions and args.fail_on_regression) else 0


if __name__ == "__main__":
    sys.exit(main())
