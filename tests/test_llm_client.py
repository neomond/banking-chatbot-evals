"""Provider resolution for the free-tier LLM adapters (no network)."""
import pytest

from bot.llm_client import (
    has_credentials, make_completer, resolve_judge_provider, resolve_provider,
)


def test_default_provider_is_gemini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY",
                "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_HOST"):
        monkeypatch.delenv(key, raising=False)
    assert resolve_provider() == "gemini"


def test_detects_groq_when_only_groq_key_present(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    assert resolve_provider() == "groq"


def test_explicit_provider_wins(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert resolve_provider() == "openai"


def test_judge_prefers_other_family_when_two_keys(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("JUDGE_PROVIDER", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("GROQ_API_KEY", "gsk")
    assert resolve_provider() == "gemini"
    assert resolve_judge_provider() == "groq"


def test_gemini_missing_key_is_actionable(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="aistudio.google.com"):
        make_completer("gemini", "gemini-3.5-flash-lite")


def test_unknown_provider():
    with pytest.raises(ValueError, match="unknown provider"):
        make_completer("not-a-vendor", "x")


class _Busy(Exception):
    status_code = 503


def test_retry_then_succeed(monkeypatch):
    from bot.llm_client import call_with_retry

    monkeypatch.setattr("bot.llm_client.time.sleep", lambda _s: None)
    hits = {"n": 0}

    def flaky():
        hits["n"] += 1
        if hits["n"] < 3:
            raise _Busy("high demand")
        return "ok"

    assert call_with_retry(flaky, attempts=4, base_delay=0) == "ok"
    assert hits["n"] == 3


def test_judge_survives_provider_error():
    from evals.judge import LLMJudge

    class Boom:
        def complete(self, **_kwargs):
            raise _Busy("UNAVAILABLE")

    scored = LLMJudge(completer=Boom()).score(
        {"category": "pii", "language": "en", "expect": {}, "turns": ["hi"],
         "response": "hello", "actions": []},
        facts={},
    )
    assert scored["error"] == "provider"


def test_has_credentials(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert not has_credentials("groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk")
    assert has_credentials("groq")
