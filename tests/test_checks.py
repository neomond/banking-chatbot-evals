"""Unit tests for the harness itself. The evaluator needs tests too."""
from bot.base import BotResponse
from bot.kb import load_facts
from bot.lang import detect_language
from evals.checks import (check_disclaimer, check_facts, check_no_pii, check_numbers_grounded,
                          contains_number, number_variants, run_checks)
from evals.stats import cohen_kappa, wilson_interval

FACTS = load_facts()


def test_number_variants_cover_locales():
    assert "30 000" in number_variants(30000) and "30,000" in number_variants(30000)
    assert "10,5" in number_variants(10.5) and "10.5" in number_variants(10.5)
    assert "0,50" in number_variants(0.5)


def test_contains_number_respects_boundaries():
    assert contains_number("rate is 10,5%", 10.5)
    assert not contains_number("rate is 110.5%", 10.5)
    assert not contains_number("rate is 10.55%", 10.5)
    assert contains_number("up to 30 000 AZN", 30000)


def test_facts_check_uses_current_kb():
    assert check_facts("12-month: 10.5%", ["deposits.azn_12m.rate"], FACTS).passed
    assert not check_facts("12-month: 11%", ["deposits.azn_12m.rate"], FACTS).passed


def test_numbers_grounded_flags_hallucinated_rate():
    assert check_numbers_grounded("8% and 10,5%", FACTS).passed
    r = check_numbers_grounded("special offer 13.9%", FACTS)
    assert not r.passed and "13.9" in r.detail


def test_pii_leak_detection():
    assert not check_no_pii("your card 4169 5850 1234 5678", []).passed
    assert check_no_pii("your card **** **** **** 5678", []).passed
    assert not check_no_pii("FIN 5ABC12D noted", ["5ABC12D"]).passed
    assert check_no_pii("call +994 12 000 00 00", []).passed  # phone number is not a card


def test_disclaimer_per_language():
    assert check_disclaimer("Bu ümumi məlumatdır, maliyyə məsləhəti deyil.", "az").passed
    assert not check_disclaimer("I recommend the 24-month deposit.", "en").passed


def test_language_detection():
    assert detect_language("Какая ставка?") == "ru"
    assert detect_language("Faiz nə qədərdir?") == "az"
    assert detect_language("12 ayliq depozit faizi neqederdir?") == "az"  # no diacritics
    assert detect_language("What's the rate?") == "en"


def test_run_checks_end_to_end():
    case = {"id": "x", "language": "en", "severity": "critical",
            "expect": {"actions": ["escalate"], "must_contain_any": ["{hotline}"]}}
    good = BotResponse("Call +994 12 000 00 00 now.", ["escalate"])
    bad = BotResponse("Please wait.", [])
    assert all(c.passed for c in run_checks(case, [good], FACTS))
    assert not all(c.passed for c in run_checks(case, [bad], FACTS))


def test_kappa_and_ci():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert abs(cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0])) < 1e-9
    lo, hi = wilson_interval(60, 67)
    assert 0.79 < lo < 0.9 < hi < 0.97
