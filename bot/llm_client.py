"""LLM provider strategy: Anthropic native API plus OpenAI-compatible endpoints.

Free defaults (no paid OpenAI/Anthropic account required):
  gemini  — Google AI Studio free tier  (GEMINI_API_KEY)   [default]
  groq    — Groq free tier              (GROQ_API_KEY)
  ollama  — local, no cloud key         (optional OLLAMA_BASE_URL)

Paid:
  openai, anthropic
"""
from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from .dotenv import load_dotenv

T = TypeVar("T")
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


class ChatCompleter(Protocol):
    provider: str
    model: str

    def complete(
        self,
        *,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        system: str | None = None,
    ) -> str:
        ...


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    kind: str  # "anthropic" | "openai_compat"
    default_bot: str
    default_judge: str
    api_key_envs: tuple[str, ...]
    base_url: str | None = None
    fallback_api_key: str | None = None
    fallback_models: tuple[str, ...] = field(default_factory=tuple)


PROVIDERS: dict[str, ProviderSpec] = {
    "gemini": ProviderSpec(
        name="gemini",
        kind="openai_compat",
        default_bot="gemini-3.5-flash-lite",
        default_judge="gemini-3.5-flash-lite",
        api_key_envs=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        fallback_models=("gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"),
    ),
    "groq": ProviderSpec(
        name="groq",
        kind="openai_compat",
        default_bot="llama-3.3-70b-versatile",
        default_judge="llama-3.1-8b-instant",
        api_key_envs=("GROQ_API_KEY",),
        base_url="https://api.groq.com/openai/v1",
    ),
    "ollama": ProviderSpec(
        name="ollama",
        kind="openai_compat",
        default_bot="llama3.1",
        default_judge="llama3.1",
        api_key_envs=("OLLAMA_API_KEY",),
        base_url="http://localhost:11434/v1",
        fallback_api_key="ollama",
    ),
    "openai": ProviderSpec(
        name="openai",
        kind="openai_compat",
        default_bot="gpt-4.1-mini",
        default_judge="gpt-4.1",
        api_key_envs=("OPENAI_API_KEY",),
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        kind="anthropic",
        default_bot="claude-sonnet-5-5",
        default_judge="claude-opus-5-5",
        api_key_envs=("ANTHROPIC_API_KEY",),
    ),
}

# Preferred when LLM_PROVIDER is unset: free keys first.
_DETECT_ORDER = ("gemini", "groq", "ollama", "anthropic", "openai")

DEFAULT_BOT_MODELS = {name: spec.default_bot for name, spec in PROVIDERS.items()}
DEFAULT_JUDGE_MODELS = {name: spec.default_judge for name, spec in PROVIDERS.items()}


def _status_code(exc: BaseException) -> int | None:
    return getattr(exc, "status_code", None)


def is_retryable(exc: BaseException) -> bool:
    code = _status_code(exc)
    if code in RETRY_STATUS:
        return True
    text = str(exc).lower()
    return any(token in text for token in ("high demand", "unavailable", "overloaded", "rate limit", "429", "503"))


def call_with_retry(fn: Callable[[], T], *, attempts: int = 5, base_delay: float = 2.0) -> T:
    last: BaseException | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last = exc
            if not is_retryable(exc) or i == attempts - 1:
                raise
            delay = min(base_delay * (2 ** i), 40)
            print(f"  provider busy (HTTP {_status_code(exc) or '?'}); retry {i + 1}/{attempts - 1} in {delay:.0f}s",
                  flush=True)
            time.sleep(delay)
    raise last  # pragma: no cover


def _env(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def has_credentials(provider: str) -> bool:
    spec = PROVIDERS[provider]
    if spec.fallback_api_key:
        return bool(_env(spec.api_key_envs) or os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST"))
    return _env(spec.api_key_envs) is not None


def resolve_provider(explicit: str | None = None) -> str:
    """LLM_PROVIDER wins; otherwise the first provider that has a key (Gemini first)."""
    load_dotenv()
    if explicit:
        return explicit
    named = os.getenv("LLM_PROVIDER")
    if named:
        return named
    for name in _DETECT_ORDER:
        if has_credentials(name):
            return name
    return "gemini"


def resolve_judge_provider(explicit: str | None = None) -> str:
    """Prefer a different family from the bot when a second free key is present."""
    load_dotenv()
    if explicit:
        return explicit
    named = os.getenv("JUDGE_PROVIDER")
    if named:
        return named
    bot = resolve_provider()
    for name in _DETECT_ORDER:
        if name != bot and has_credentials(name):
            return name
    return bot


class AnthropicCompleter:
    provider = "anthropic"

    def __init__(self, model: str):
        import anthropic

        self.model = model
        self._client = anthropic.Anthropic()

    def complete(
        self,
        *,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        system: str | None = None,
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        def _call():
            response = self._client.messages.create(**kwargs)
            return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")

        return call_with_retry(_call)


class OpenAICompatibleCompleter:
    def __init__(
        self, provider: str, model: str, *, api_key: str, base_url: str | None,
        fallback_models: tuple[str, ...] = (),
    ):
        import openai

        self.provider = provider
        self.model = model
        self._fallbacks = fallback_models
        kwargs: dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**kwargs)

    def complete(
        self,
        *,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        system: str | None = None,
    ) -> str:
        payload = ([{"role": "system", "content": system}] if system else []) + messages
        models = [self.model, *[m for m in self._fallbacks if m != self.model]]
        last: BaseException | None = None
        for index, model in enumerate(models):
            attempts = 5 if index == 0 else 2

            def _call(active=model):
                response = self._client.chat.completions.create(
                    model=active, temperature=temperature, max_tokens=max_tokens, messages=payload,
                )
                return response.choices[0].message.content or ""

            try:
                text = call_with_retry(_call, attempts=attempts)
                self.model = model
                return text
            except Exception as exc:
                last = exc
                if is_retryable(exc) and index < len(models) - 1:
                    print(f"  switching to fallback model {models[index + 1]}", flush=True)
                    continue
                raise
        raise last  # pragma: no cover


def _api_key(spec: ProviderSpec) -> str:
    key = _env(spec.api_key_envs) or spec.fallback_api_key
    if key:
        return key
    names = " or ".join(spec.api_key_envs)
    hint = ""
    if spec.name == "gemini":
        hint = " Get a free key at https://aistudio.google.com/apikey"
    elif spec.name == "groq":
        hint = " Get a free key at https://console.groq.com/keys"
    raise ValueError(f"{spec.name} needs {names}.{hint}")


def make_completer(provider: str, model: str) -> ChatCompleter:
    load_dotenv()
    try:
        spec = PROVIDERS[provider]
    except KeyError as exc:
        known = ", ".join(PROVIDERS)
        raise ValueError(f"unknown provider {provider}. known: {known}") from exc
    if spec.kind == "anthropic":
        return AnthropicCompleter(model)
    base_url = spec.base_url
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", spec.base_url)
    elif provider == "openai":
        base_url = os.getenv("OPENAI_BASE_URL") or spec.base_url
    return OpenAICompatibleCompleter(
        provider, model, api_key=_api_key(spec), base_url=base_url,
        fallback_models=spec.fallback_models,
    )


def parse_json_object(raw: str) -> dict | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None
