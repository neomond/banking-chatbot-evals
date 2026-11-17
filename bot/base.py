"""Shared chatbot contract: every system under test implements Bot.reply."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# Structured actions a bot can emit alongside its text. Real banking bots usually
# return actions like these so the frontend can open a handover / auth flow.
ACTIONS = frozenset({
    "escalate",        # hand over to a human operator
    "security_alert",  # route to fraud / security team
    "require_auth",    # user must authenticate in the app / with an operator
    "pii_warning",     # user shared sensitive data, it was masked
    "clarify",         # bot asked a clarifying question
    "refuse",          # off-topic or policy-violating request declined
})


@dataclass
class BotResponse:
    text: str
    actions: list[str] = field(default_factory=list)
    language: str | None = None
    meta: dict = field(default_factory=dict)


class Bot(ABC):
    """history = [{"role": "user"|"assistant", "content": str}, ...]; last item is the user turn."""

    name = "base"

    @abstractmethod
    def reply(self, history: list[dict]) -> BotResponse:
        raise NotImplementedError
