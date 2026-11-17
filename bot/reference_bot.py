"""Rule-based reference chatbot for Lumen Bank.

Why it exists: it lets the whole eval pipeline run offline, in CI, with no API key,
and gives a known-good baseline. The `regressed` variant simulates three realistic
production regressions so we can prove the harness catches them:

  1. context/retrieval regression - bot answers from a STALE tariff snapshot
  2. prompt regression            - advice disclaimer dropped, bot recommends products
  3. guardrail regression         - PII masking removed, card numbers echoed back

The real system under test is `bot/llm_bot.py`; same harness, same dataset.
"""
from __future__ import annotations

from .base import Bot, BotResponse
from .kb import load_facts
from .lang import detect_language
from .reference_handlers import HandlerChain, POLICIES, TurnContext


class ReferenceBot(Bot):
    def __init__(self, variant: str = "baseline", chain: HandlerChain | None = None):
        try:
            self.policy = POLICIES[variant]
        except KeyError as exc:
            raise ValueError(f"unknown reference variant: {variant}") from exc
        self.variant = variant
        self.name = f"reference-{variant}"
        self.facts = load_facts(self.policy.kb_path)
        self.hotline = self.facts["contacts.hotline"]["value"]
        self._chain = chain or HandlerChain()

    def reply(self, history: list[dict]) -> BotResponse:
        user_msgs = [m["content"] for m in history if m["role"] == "user"]
        raw = user_msgs[-1]
        ctx = TurnContext(
            policy=self.policy,
            facts=self.facts,
            hotline=self.hotline,
            raw=raw,
            text=raw.lower(),
            lang=detect_language(raw),
            user_msgs=user_msgs,
        )
        return self._chain.dispatch(ctx)
