"""Dataset integrity: broken test data silently produces wrong scores."""
from collections import Counter
from pathlib import Path

import yaml

from bot.base import ACTIONS
from bot.kb import ROOT, load_facts

CASES = yaml.safe_load((ROOT / "data" / "golden.yaml").read_text(encoding="utf-8"))["cases"]
FACTS = load_facts()
ALLOWED_EXPECT = {"facts", "actions", "actions_absent", "disclaimer", "must_contain_any",
                  "must_not_contain", "pii_values"}


def test_ids_unique():
    dupes = [i for i, n in Counter(c["id"] for c in CASES).items() if n > 1]
    assert not dupes, dupes


def test_schema():
    for c in CASES:
        assert c["language"] in {"az", "ru", "en"}, c["id"]
        assert c["severity"] in {"critical", "major", "minor"}, c["id"]
        assert c["turns"] and all(isinstance(t, str) for t in c["turns"]), c["id"]
        assert set(c.get("expect", {})) <= ALLOWED_EXPECT, c["id"]


def test_fact_keys_exist_in_kb():
    for c in CASES:
        for key in c.get("expect", {}).get("facts", []):
            assert key in FACTS, f"{c['id']}: unknown fact {key}"


def test_actions_are_known():
    for c in CASES:
        exp = c.get("expect", {})
        for a in exp.get("actions", []) + exp.get("actions_absent", []):
            assert a in ACTIONS, f"{c['id']}: unknown action {a}"


def test_every_language_covers_core_risks():
    for cat in ["product_facts", "advice", "pii", "scam", "escalation", "injection", "out_of_scope"]:
        langs = {c["language"] for c in CASES if c["category"] == cat}
        assert langs == {"az", "ru", "en"}, f"{cat} missing languages: {langs}"


def test_stale_snapshot_differs_from_current():
    stale = load_facts(Path(ROOT / "kb" / "snapshots" / "facts_2026-09.yaml"))
    assert any(stale[k]["value"] != FACTS[k]["value"] for k in FACTS)
