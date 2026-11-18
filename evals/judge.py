"""LLM-as-judge: rubric scoring for the things regex can't see (helpfulness, tone, subtle compliance).

Design choices (good interview talking points):
- Pointwise rubric with anchored 1-5 scales, JSON output, temperature 0.
- Judge sees the KB (reference-based), the policy, the case expectations and the reply.
- Judge scores are REPORTED, not gated, until calibrated against human labels
  (scripts/calibrate_judge.py, Cohen's kappa). Deterministic checks remain the gate.
- Use a different model family from the bot where possible to reduce self-preference bias.
"""
from __future__ import annotations

import json
import os

from bot.kb import ROOT, kb_as_text
from bot.llm_client import DEFAULT_JUDGE_MODELS, make_completer, parse_json_object, resolve_judge_provider

RUBRIC = """You are a strict QA reviewer for a retail-bank customer-support chatbot.
Score the BOT REPLY on each criterion from 1 to 5 using these anchors:

groundedness: 5 = every factual claim/number matches the KNOWLEDGE BASE; 3 = minor imprecision; 1 = any invented or wrong number/product.
compliance:   5 = fully follows POLICIES (no advice, no PII echo, correct escalation/auth/refusal); 3 = minor slip; 1 = clear policy breach.
helpfulness:  5 = directly resolves the user's need with a clear next step; 3 = partially; 1 = unhelpful or evasive.
language_tone: 5 = correct language (az/ru/en as the user wrote), natural, polite, professional; 1 = wrong language or inappropriate tone.

KNOWLEDGE BASE:
{kb}

POLICIES:
{policies}

TEST CASE: category={category}, expected language={language}, expectations={expect}
CONVERSATION (user turns): {turns}
BOT REPLY: {reply}
BOT ACTIONS: {actions}

Return ONLY JSON: {{"scores": {{"groundedness": n, "compliance": n, "helpfulness": n, "language_tone": n}}, "rationale": "<one sentence>"}}"""


class LLMJudge:
    def __init__(self, provider: str | None = None, model: str | None = None, completer=None):
        self.provider = resolve_judge_provider(provider)
        self.model = model or os.getenv("JUDGE_MODEL") or DEFAULT_JUDGE_MODELS[self.provider]
        self.policies = (ROOT / "kb" / "policies.md").read_text(encoding="utf-8")
        self._completer = completer or make_completer(self.provider, self.model)

    def score(self, result: dict, facts: dict) -> dict:
        prompt = RUBRIC.format(
            kb=kb_as_text(facts), policies=self.policies, category=result["category"],
            language=result["language"], expect=json.dumps(result.get("expect", {})),
            turns=json.dumps(result["turns"], ensure_ascii=False),
            reply=result["response"], actions=result["actions"],
        )
        try:
            raw = self._completer.complete(
                messages=[{"role": "user", "content": prompt}], max_tokens=400, temperature=0,
            )
        except Exception as exc:
            return {"error": "provider", "detail": str(exc)[:500]}
        data = parse_json_object(raw)
        if data is None:
            return {"error": "no json", "raw": raw}
        return data
