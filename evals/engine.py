"""Eval engine: run cases, score, summarise. IO and CLI live in runner.py."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from bot.base import Bot
from bot.kb import load_facts

from .checks import run_checks
from .gate import DEFAULT_GATE, GatePolicy
from .stats import wilson_interval


def load_cases(path: Path, ids: list[str] | None = None, categories: list[str] | None = None) -> list[dict]:
    cases = yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    if categories:
        cases = [c for c in cases if c["category"] in categories]
    return cases


class EvalEngine:
    def __init__(self, bot: Bot, facts: dict, judge=None, gate: GatePolicy = DEFAULT_GATE):
        self.bot = bot
        self.facts = facts
        self.judge = judge
        self.gate = gate

    def run_case(self, case: dict) -> dict:
        history, responses = [], []
        t0 = time.perf_counter()
        for turn in case["turns"]:
            history.append({"role": "user", "content": turn})
            resp = self.bot.reply(history)
            responses.append(resp)
            history.append({"role": "assistant", "content": resp.text})
        latency = time.perf_counter() - t0
        checks = run_checks(case, responses, self.facts)
        passed = all(c.passed for c in checks)
        result = {
            "id": case["id"], "category": case["category"], "language": case["language"],
            "severity": case["severity"], "tags": case.get("tags", []), "turns": case["turns"],
            "expect": case.get("expect", {}),
            "passed": passed, "critical_failure": (not passed) and case["severity"] == "critical",
            "checks": [c.to_dict() for c in checks],
            "response": responses[-1].text, "actions": responses[-1].actions,
            "latency_s": round(latency, 4),
        }
        if self.judge:
            result["judge"] = self.judge.score(result, self.facts)
        return result

    def summarize(self, results: list[dict]) -> dict:
        def rate(rows):
            return round(sum(r["passed"] for r in rows) / len(rows), 4) if rows else None

        by_cat, by_lang, by_check = defaultdict(list), defaultdict(list), defaultdict(lambda: [0, 0])
        for r in results:
            by_cat[r["category"]].append(r)
            by_lang[r["language"]].append(r)
            for c in r["checks"]:
                by_check[c["name"]][0] += c["passed"]
                by_check[c["name"]][1] += 1
        crit = [r["id"] for r in results if r["critical_failure"]]
        pass_rate = rate(results)
        gate_ok = self.gate.passed(len(crit), pass_rate)
        return {
            "total": len(results), "passed": sum(r["passed"] for r in results), "pass_rate": pass_rate,
            "pass_rate_ci95": [round(x, 4) for x in wilson_interval(sum(r["passed"] for r in results), len(results))],
            "critical_failures": crit,
            "by_category": {k: {"n": len(v), "pass_rate": rate(v)} for k, v in sorted(by_cat.items())},
            "by_language": {k: {"n": len(v), "pass_rate": rate(v)} for k, v in sorted(by_lang.items())},
            "by_check": {k: {"passed": p, "total": t, "pass_rate": round(p / t, 4)} for k, (p, t) in sorted(by_check.items())},
            "gate": self.gate.as_dict(passed=gate_ok),
        }

    def run(self, cases: list[dict], dataset_name: str) -> dict:
        results = [self.run_case(c) for c in cases]
        return {
            "bot": self.bot.name,
            "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dataset": dataset_name,
            "summary": self.summarize(results),
            "results": results,
        }


def facts_for_checks(path=None) -> dict:
    """Checks always score against the current source of truth, not the bot's context."""
    return load_facts(path) if path else load_facts()
