"""Markdown report for humans (PR comments, stakeholders)."""
from __future__ import annotations

from pathlib import Path


def _pct(x) -> str:
    return "-" if x is None else f"{x:.0%}"


def write_markdown(payload: dict, path: Path) -> None:
    s = payload["summary"]
    gate = "✅ PASS" if s["gate"]["passed"] else "❌ FAIL"
    L = [
        f"# Eval report: `{payload['bot']}`",
        "",
        f"Run: {payload['run_at']} · Dataset: `{payload['dataset']}` · Cases: {s['total']}",
        "",
        f"**Release gate: {gate}** (critical failures {len(s['critical_failures'])} / max "
        f"{s['gate']['max_critical_failures']}, pass rate {_pct(s['pass_rate'])} / min {_pct(s['gate']['min_pass_rate'])})",
        "",
        f"Pass rate 95% CI: {_pct(s['pass_rate_ci95'][0])}–{_pct(s['pass_rate_ci95'][1])} (small set: treat a few points of change as noise)",
        "",
        "## By category",
        "",
        "| Category | Cases | Pass rate |",
        "|---|---:|---:|",
    ]
    L += [f"| {k} | {v['n']} | {_pct(v['pass_rate'])} |" for k, v in s["by_category"].items()]
    L += ["", "## By language", "", "| Language | Cases | Pass rate |", "|---|---:|---:|"]
    L += [f"| {k} | {v['n']} | {_pct(v['pass_rate'])} |" for k, v in s["by_language"].items()]
    L += ["", "## By check", "", "| Check | Passed | Pass rate |", "|---|---:|---:|"]
    L += [f"| {k} | {v['passed']}/{v['total']} | {_pct(v['pass_rate'])} |" for k, v in s["by_check"].items()]

    judged = [r for r in payload["results"] if r.get("judge") and "scores" in r["judge"]]
    if judged:
        crits = list(judged[0]["judge"]["scores"].keys())
        L += ["", "## LLM-judge averages (1-5)", "", "| Criterion | Mean |", "|---|---:|"]
        for c in crits:
            vals = [r["judge"]["scores"][c] for r in judged if c in r["judge"]["scores"]]
            L.append(f"| {c} | {sum(vals) / len(vals):.2f} |")

    fails = [r for r in payload["results"] if not r["passed"]]
    L += ["", f"## Failures ({len(fails)})", ""]
    if not fails:
        L.append("None.")
    for r in sorted(fails, key=lambda r: (not r["critical_failure"], r["id"])):
        flag = "🔴 CRITICAL" if r["critical_failure"] else "🟠"
        L += [f"### {flag} `{r['id']}` ({r['category']}, {r['language']})", "",
              f"**User:** {r['turns'][-1]}", "",
              "**Bot:** " + r["response"].replace("\n", " ⏎ ")[:600], "",
              f"**Actions:** {r['actions']}", ""]
        L += [f"- ❌ `{c['name']}`: {c['detail']}" for c in r["checks"] if not c["passed"]]
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8")
