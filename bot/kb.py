"""Knowledge-base loading and value formatting."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KB = ROOT / "kb" / "facts.yaml"

UNIT_WORDS = {
    "days": {"en": "days", "az": "gün", "ru": "дней"},
    "months": {"en": "months", "az": "ay", "ru": "месяцев"},
}


def load_kb(path: str | Path = DEFAULT_KB) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_facts(path: str | Path = DEFAULT_KB) -> dict:
    return load_kb(path)["facts"]


def format_number(value: float | int, lang: str) -> str:
    """en: 30,000 / 10.5   az & ru: 30 000 / 10,5  (exercises number normalisation in checks)."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        s = f"{value:,}"
        return s if lang == "en" else s.replace(",", " ")
    s = f"{value:g}"
    return s if lang == "en" else s.replace(".", ",")


def format_value(fact: dict, lang: str) -> str:
    value, unit = fact["value"], fact.get("unit", "")
    if isinstance(value, str):
        return value
    num = format_number(value, lang)
    if unit == "%":
        return f"{num}%"
    if unit in UNIT_WORDS:
        return f"{num} {UNIT_WORDS[unit][lang]}"
    return f"{num} {unit}".strip()


def render_fact(fact: dict, lang: str) -> str:
    return f"- {fact['label'][lang]}: {format_value(fact, lang)}"


def facts_for_topic(facts: dict, topic: str) -> dict:
    return {k: v for k, v in facts.items() if v["topic"] == topic}


def kb_as_text(facts: dict) -> str:
    """English rendering used as context for the LLM bot."""
    lines = []
    for key, fact in facts.items():
        lines.append(f"[{key}] {fact['label']['en']}: {format_value(fact, 'en')}")
    return "\n".join(lines)
