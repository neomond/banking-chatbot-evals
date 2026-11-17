PY ?= python

.PHONY: install test eval regression-demo eval-llm eval-llm-stale all

install:
	$(PY) -m pip install -r requirements.txt

test:            ## unit tests for the harness + dataset integrity
	$(PY) -m pytest -q

eval:            ## offline baseline run (release gate enforced)
	$(PY) -m evals.runner --bot reference --out reports/baseline

regression-demo: ## simulated regressions: stale KB, dropped disclaimer, PII echo
	$(PY) -m evals.runner --bot reference-regressed --out reports/regressed --no-gate
	$(PY) -m evals.compare reports/baseline.json reports/regressed.json --out reports/comparison.md

eval-llm:        ## real LLM bot + LLM judge (needs ANTHROPIC_API_KEY or OPENAI_API_KEY)
	$(PY) -m evals.runner --bot llm --judge --out reports/llm

eval-llm-stale:  ## same model, stale tariffs in context: does the harness catch it?
	$(PY) -m evals.runner --bot llm --kb kb/snapshots/facts_2026-09.yaml --out reports/llm-stale --no-gate
	$(PY) -m evals.compare reports/llm.json reports/llm-stale.json --out reports/llm-comparison.md

all: test eval regression-demo
