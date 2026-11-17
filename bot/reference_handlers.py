"""Chain of responsibility for the reference bot, plus baseline vs regressed policy."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .base import BotResponse
from .kb import DEFAULT_KB, ROOT, facts_for_topic, render_fact
from .reference_catalog import (
    CARD_EMERGENCY, CARD_RE, FIN_RE, FIN_TRIGGER, KW, T,
    contains_any, detect_topic, mask_card,
)

STALE_KB = ROOT / "kb" / "snapshots" / "facts_2026-09.yaml"


@dataclass(frozen=True)
class ReferencePolicy:
    """Strategy object: which KB to quote and which guardrails are on."""
    name: str
    kb_path: Path
    echo_pii: bool
    recommend_on_advice: bool


POLICIES = {
    "baseline": ReferencePolicy("baseline", DEFAULT_KB, echo_pii=False, recommend_on_advice=False),
    "regressed": ReferencePolicy("regressed", STALE_KB, echo_pii=True, recommend_on_advice=True),
}


@dataclass
class TurnContext:
    policy: ReferencePolicy
    facts: dict
    hotline: str
    raw: str
    text: str
    lang: str
    user_msgs: list[str]

    def say(self, key: str, **kwargs) -> str:
        return T[key][self.lang].format(hotline=self.hotline, **kwargs)


class IntentHandler(Protocol):
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        """Return a response if this intent matches, otherwise None to try the next handler."""
        ...


class InjectionHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        if contains_any(ctx.text, KW["injection"]):
            return BotResponse(ctx.say("refuse_injection"), ["refuse"], ctx.lang)
        return None


class PiiHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        cards = CARD_RE.findall(ctx.raw)
        fins = FIN_RE.findall(ctx.raw) if FIN_TRIGGER.search(ctx.raw) else []
        if not (cards or fins):
            return None
        if ctx.policy.echo_pii:
            return BotResponse(
                ctx.say("pii_echo", raw=", ".join(cards + fins)), ["require_auth"], ctx.lang,
            )
        masked = ", ".join(
            [mask_card(m) for m in CARD_RE.finditer(ctx.raw)] + ["*******" for _ in fins]
        )
        parts, actions = [ctx.say("pii", masked=masked)], ["pii_warning", "require_auth"]
        if contains_any(ctx.text, KW["scam"]) or "cvv" in ctx.text:
            parts.append(ctx.say("scam"))
            actions += ["security_alert", "escalate"]
        return BotResponse(" ".join(parts), actions, ctx.lang)


class ScamHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        if contains_any(ctx.text, KW["scam"]):
            return BotResponse(ctx.say("scam"), ["security_alert", "escalate"], ctx.lang)
        return None


class EscalationHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        if not contains_any(ctx.text, KW["escalation"]):
            return None
        key = "escalate_card" if contains_any(ctx.text, CARD_EMERGENCY) else "escalate_general"
        return BotResponse(ctx.say(key), ["escalate"], ctx.lang)


class AuthHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        if contains_any(ctx.text, KW["auth"]):
            return BotResponse(ctx.say("auth"), ["require_auth"], ctx.lang)
        return None


class OutOfScopeHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        if contains_any(ctx.text, KW["out_of_scope"]):
            return BotResponse(ctx.say("refuse_oos"), ["refuse"], ctx.lang)
        return None


class ProductFactsHandler:
    def handle(self, ctx: TurnContext) -> BotResponse | None:
        topic = detect_topic(ctx.text)
        if topic is None:
            for prev in reversed(ctx.user_msgs[:-1]):
                topic = detect_topic(prev.lower())
                if topic:
                    break
        if not topic:
            return None
        lines = [T["facts_intro"][topic][ctx.lang]]
        lines += [render_fact(fact, ctx.lang) for fact in facts_for_topic(ctx.facts, topic).values()]
        if contains_any(ctx.text, KW["advice"]):
            if ctx.policy.recommend_on_advice:
                lines.append(ctx.say("bad_recommendation"))
            else:
                lines += [ctx.say("advice_compare"), ctx.say("disclaimer")]
        return BotResponse("\n".join(lines), [], ctx.lang, {"topic": topic})


class ClarifyHandler:
    def handle(self, ctx: TurnContext) -> BotResponse:
        return BotResponse(ctx.say("clarify"), ["clarify"], ctx.lang)


DEFAULT_CHAIN: tuple[IntentHandler, ...] = (
    InjectionHandler(),
    PiiHandler(),
    ScamHandler(),
    EscalationHandler(),
    AuthHandler(),
    OutOfScopeHandler(),
    ProductFactsHandler(),
    ClarifyHandler(),
)


class HandlerChain:
    def __init__(self, handlers: tuple[IntentHandler, ...] = DEFAULT_CHAIN):
        self._handlers = handlers

    def dispatch(self, ctx: TurnContext) -> BotResponse:
        for handler in self._handlers:
            response = handler.handle(ctx)
            if response is not None:
                return response
        raise RuntimeError("handler chain produced no response")
