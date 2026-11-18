# TODOs — banking-chatbot-evals

Checklist of what is already in the repo and what to do next. Repo: https://github.com/neomond/banking-chatbot-evals

---

## Done

### Core eval harness
- [x] Fictional Lumen Bank KB (`kb/facts.yaml`) with az/ru/en labels; tests store keys, not hardcoded rates
- [x] Stale tariff snapshot for retrieval/context regressions (`kb/snapshots/facts_2026-09.yaml`)
- [x] Behavioural policies mapped to test categories (`kb/policies.md`)
- [x] Golden set: 67 cases, 11 categories, 3 languages, severity tags (`data/golden.yaml`)
- [x] Dataset integrity tests (unique ids, fact keys exist, az/ru/en coverage of core risks)
- [x] Deterministic checks as the **release gate** (`evals/checks.py`): facts, grounded numbers, PII, canary, language, actions, disclaimer
- [x] Gate: 0 critical failures **and** pass rate ≥ 90% (`evals/gate.py`)
- [x] Eval engine + CLI (`evals/engine.py`, `evals/runner.py`) with JSON + Markdown reports
- [x] Run-vs-run regression diff (`evals/compare.py`)
- [x] Wilson 95% CI on pass rates (`evals/stats.py`)
- [x] Offline reference bot (known-good control, no API key) (`bot/reference_bot.py`)
- [x] Regressed reference bot: stale KB + dropped disclaimer + PII echo
- [x] LLM bot with structured JSON `{text, actions}` (`bot/llm_bot.py`)
- [x] LLM-as-judge rubric (groundedness, compliance, helpfulness, tone) — **reported, not gated** (`evals/judge.py`)
- [x] Judge–human calibration script + Cohen’s kappa (`scripts/calibrate_judge.py`)
- [x] Makefile targets: `test`, `eval`, `regression-demo`, `eval-llm`, `eval-llm-stale`
- [x] CI: pytest + reference-bot golden gate; LLM job skipped unless a provider key is set (`.github/workflows/evals.yml`)
- [x] Baseline vs regressed demo reports committed (`reports/baseline.*`, `reports/regressed.*`, `reports/comparison.md`)

### Design-pattern refactor
- [x] `Bot` ABC + `BotResponse` contract (`bot/base.py`)
- [x] Bot registry / factory (`bot/registry.py`, `make_bot`)
- [x] LLM provider strategy + injectable completer (`bot/llm_client.py`)
- [x] Reference bot as chain of responsibility + baseline/regressed policy (`bot/reference_handlers.py`)
- [x] Check pipeline (`Check` / `DEFAULT_CHECKS` in `evals/checks.py`)
- [x] Split CLI from scoring (`evals/runner.py` vs `evals/engine.py`)
- [x] Extra unit tests for registry, routing, fake LLM client (`tests/test_bots.py`)
- [x] Confirmed behaviour unchanged: reference 67/67, regressed 36/67 with 20 critical fails

### Free LLM path + first live run
- [x] Free providers: Gemini (default), Groq, Ollama; paid OpenAI/Anthropic still work
- [x] Load `GEMINI_API_KEY` from gitignored `.env` (`bot/dotenv.py`, `.env.example`)
- [x] Retry 429/503 with backoff; fallback models; judge errors do not abort the run
- [x] Per-case progress logging (`[n/67] case-id`)
- [x] LLM CI is **informational** (`--no-gate`) so free-tier limits do not fail the merge
- [x] Ran `make eval-llm` locally on Gemini 3.5 Flash-Lite: **55/67 (82%)**, 11 critical, gate FAIL
- [x] Finding: facts/PII/canary/grounded-% at 100%; fails are almost all **en/ru replies in Azerbaijani**
- [x] Retired `gemini-2.5-flash` fallback (404); now `gemini-3.8-flash` / `gemini-3.6-flash`

### GitHub
- [x] Public repo `neomond/banking-chatbot-evals`
- [x] About text + topics (`llm`, `evaluation`, `chatbot`, `llmops`, `safety`, `multilingual`)

---

## Remaining

### 1. Wire real LLM evals in CI
- [ ] Add GitHub Actions secret `GEMINI_API_KEY` (do **not** commit `.env`)
- [ ] Run `make eval-llm-stale` and confirm `numbers_grounded` catches the September snapshot on Gemini
- [ ] Optional: tighten the bot prompt so English/Russian users are not answered in Azerbaijani, then re-run `make eval-llm`

### 2. Calibrate the judge before using it as a gate
- [ ] Copy `data/human_labels_template.csv` → `data/human_labels.csv` (already gitignored)
- [ ] Label ~20–30 cases by hand (`case_id,criterion,human_score`)
- [ ] Run `python scripts/calibrate_judge.py reports/llm.json data/human_labels.csv`
- [ ] Only if Cohen’s κ ≥ 0.6 on a criterion, consider adding that criterion to `evals/gate.py` (keep regex/KB checks as the source of truth)

### 3. Tighten “correct but unhelpful” answers
- [ ] Add a check that the reply answers **what was asked**, not the whole tariff sheet (`facts_correct` currently passes on over-answering)
- [ ] Optionally fail if extra unsolicited product numbers appear outside `expect.facts`

### 4. Grow the golden set
- [ ] Add cases from the Gemini language misses (en/ru answered in az)
- [ ] Keep `tests/test_dataset.py` green: every core risk still in az, ru, and en
- [ ] Recompute Wilson CI; small set ≈ ±7pp around 90%, so treat tiny swings as noise until the set is larger

### 5. Measure LLM flakiness
- [ ] Run each case N times at temperature 0 (and maybe a small T > 0)
- [ ] Report pass@k and per-case flakiness in `evals/engine.py` / reports
- [ ] Fail CI on newly flaky **critical** cases, not only on mean pass rate

### 6. Retrieval / RAG (KB no longer fits in one prompt)
- [ ] Add a retriever; stop stuffing the full KB into the system prompt
- [ ] Eval context precision/recall (RAGAS-style) as extra checks, not a replacement for `numbers_grounded`
- [ ] Keep the stale-snapshot experiment: retrieved chunks vs current `kb/facts.yaml`

### 7. Export to other eval frameworks
- [ ] Script: `data/golden.yaml` → Promptfoo and/or DeepEval
- [ ] Keep Python checks as the portable gate (they do not depend on those tools)

### 8. Production monitoring
- [ ] Sample live conversations and run the same global checks (PII, canary, grounded `%`, language)
- [ ] Dashboard: incident rate by language and category, escalation rate, gate trend over time

---

## Out of scope (unless the goal changes)

- Fine-tuning / RLHF
- A real bank integration or live customer data
- Replacing the reference bot with the LLM as the CI control (the reference bot exists so CI runs with no key)
- Committing `.env` or `reports/llm*` (secrets and local Gemini reports stay private)
