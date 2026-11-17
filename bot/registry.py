"""Registry of bots under test. Adding a bot is a register() call, not another if/else."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .base import Bot

BotFactory = Callable[[str | Path | None], Bot]


class BotRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, BotFactory] = {}

    def register(self, name: str, factory: BotFactory) -> None:
        self._factories[name] = factory

    def create(self, name: str, kb: str | Path | None = None) -> Bot:
        try:
            return self._factories[name](kb)
        except KeyError as exc:
            known = ", ".join(sorted(self._factories)) or "(none)"
            raise ValueError(f"unknown bot: {name}. known: {known}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


def default_registry() -> BotRegistry:
    from .llm_bot import LLMBot
    from .reference_bot import ReferenceBot

    registry = BotRegistry()
    registry.register("reference", lambda _kb: ReferenceBot("baseline"))
    registry.register("reference-regressed", lambda _kb: ReferenceBot("regressed"))
    registry.register("llm", lambda kb: LLMBot(kb_path=kb) if kb else LLMBot())
    return registry
