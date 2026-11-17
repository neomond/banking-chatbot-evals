# Eval report: `reference-baseline`

Run: 2026-11-16T10:23:19+00:00 · Dataset: `golden.yaml` · Cases: 67

**Release gate: ✅ PASS** (critical failures 0 / max 0, pass rate 100% / min 90%)

Pass rate 95% CI: 95%–100% (small set: treat a few points of change as noise)

## By category

| Category | Cases | Pass rate |
|---|---:|---:|
| advice | 6 | 100% |
| ambiguous | 3 | 100% |
| auth_boundary | 3 | 100% |
| code_switching | 3 | 100% |
| escalation | 7 | 100% |
| injection | 6 | 100% |
| multi_turn | 4 | 100% |
| out_of_scope | 6 | 100% |
| pii | 4 | 100% |
| product_facts | 19 | 100% |
| scam | 6 | 100% |

## By language

| Language | Cases | Pass rate |
|---|---:|---:|
| az | 22 | 100% |
| en | 24 | 100% |
| ru | 21 | 100% |

## By check

| Check | Passed | Pass rate |
|---|---:|---:|
| actions_required | 36/36 | 100% |
| disclaimer | 7/7 | 100% |
| facts_correct | 27/27 | 100% |
| language | 67/67 | 100% |
| must_contain_any | 9/9 | 100% |
| must_not_contain | 15/15 | 100% |
| no_canary_leak | 67/67 | 100% |
| no_pii_leak | 67/67 | 100% |
| numbers_grounded | 67/67 | 100% |

## Failures (0)

None.