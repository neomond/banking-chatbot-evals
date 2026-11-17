from .base import ACTIONS, Bot, BotResponse
from .registry import BotRegistry, default_registry

_REGISTRY: BotRegistry | None = None


def make_bot(name: str, kb: str | None = None) -> Bot:
    """reference | reference-regressed | llm"""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = default_registry()
    return _REGISTRY.create(name, kb)


__all__ = ["ACTIONS", "Bot", "BotResponse", "BotRegistry", "make_bot"]
