"""LLM provider strategy: one ChatCompleter interface, Anthropic and OpenAI adapters."""
from __future__ import annotations

import json
import re
from typing import Protocol


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
        response = self._client.messages.create(**kwargs)
        return "".join(block.text for block in response.content if getattr(block, "type", "") == "text")


class OpenAICompleter:
    provider = "openai"

    def __init__(self, model: str):
        import openai

        self.model = model
        self._client = openai.OpenAI()

    def complete(
        self,
        *,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        system: str | None = None,
    ) -> str:
        payload = ([{"role": "system", "content": system}] if system else []) + messages
        response = self._client.chat.completions.create(
            model=self.model, temperature=temperature, messages=payload,
        )
        return response.choices[0].message.content or ""


_COMPLETERS = {
    "anthropic": AnthropicCompleter,
    "openai": OpenAICompleter,
}

DEFAULT_BOT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4.1-mini"}
DEFAULT_JUDGE_MODELS = {"anthropic": "claude-opus-5-5", "openai": "gpt-4.1"}


def make_completer(provider: str, model: str) -> ChatCompleter:
    try:
        return _COMPLETERS[provider](model)
    except KeyError as exc:
        raise ValueError(f"unknown provider {provider}") from exc


def parse_json_object(raw: str) -> dict | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None
