# PE6201 A2 — D6 Final Cost Model (5 final-v2 models)

Owner: Liu Xuanlin  
Problem: B — Outpatient Referral Coordination  
Freeze SHA: `e36bb1b2fcad625ed944e7df863165d95c0ef53f`

## Evidence basis

This final ledger uses five compatible descriptor-v2 live batteries. All use the same freeze/source commit, prompt v2, descriptor v2, main tool contract, exact 30-case evaluation set, 58-trial policy and API-reported token measurement.

| Model | Code pass | Fallback | Input tokens | Output tokens | Provider API cost | Monthly cost* | Break-even* |
|---|---:|---:|---:|---:|---:|---:|---:|
| OpenAI GPT-5.4 | 25/58 = 43.1% | 56.9% | 287,085 | 10,898 | US$0.88 | US$3,578.99 | 19.4% |
| Moonshot Kimi K2.6 | 15/58 = 25.9% | 74.1% | 263,325 | 52,112 | US$0.24 | US$4,603.96 | 19.3% |
| Anthropic Claude Sonnet 4.6 | 10/58 = 17.2% | 82.8% | 233,897 | 13,221 | US$0.90 | US$5,131.03 | 19.4% |
| DeepSeek V4 Pro | 4/58 = 6.9% | 93.1% | 196,625 | 24,437 | US$0.18 | US$5,739.89 | 19.2% |
| Google Gemini 3.7 Flash | 6/58 = 10.3% | 89.7% | 132,992 | 17,498 | US$0.17 | US$5,532.16 | 19.2% |

\* Monthly cost and break-even use the explicit business scenario assumptions below.

## Fallback definition

`fallback_rate = (trials - deterministic_code_passes) / trials`

This gives a consistent D6 operational convention across all five models. Pending judgement cases are not silently converted into passes or failures beyond the deterministic code-check result already recorded in each live result.

## Business scenario assumptions

These are scenario assumptions, not observed hospital costs:

- Human fallback cost: US$6.00 per failed task
- Manual-only task cost: US$5.00 per task
- Monthly fixed AI/monitoring cost: US$150
- Monthly task volume: 1,000 referrals

Manual-only monthly baseline = US$5,000.00.

The Gemini handoff's `gemini_cost_inputs_for_D6.csv` uses the same assumption set and explicitly labels them as copied D6 business assumptions rather than observations.

## Costing basis

The reproducible ledger uses exact price-book model cost:

`input_tokens × input_price_per_m / 1,000,000 + output_tokens × output_price_per_m / 1,000,000`

Measured tokens and run-time price metadata come from each final live JSON. `model_cost_audit.csv` also preserves the harness-reported total and provider-reported API cost for audit.

## Sensitivity and break-even

`cost_summary.csv` includes base, success −10 percentage points, and success +10 percentage points. Success is clamped to [0,1], and fallback moves inversely.

Under the stated assumptions, a +10pp success improvement reduces expected fallback spending by:

`1,000 × 10% × US$6 = US$600/month`.

Therefore the success/fallback rate is the main cost lever in this scenario; raw token-price differences are much smaller than the human fallback component.

## Files

- `cost_model.py` — reproducible formulas
- `cost_inputs.csv` — five final-v2 model inputs
- `cost_summary.csv` — base and ±10pp sensitivity
- `model_cost_audit.csv` — source/run/cost audit
- `COMPATIBILITY_CHECK.md` — five-model compatibility evidence
- `D6_report_text.md` — report-ready wording
- `PE6201_D6_Cost_Model_Final_5Models.xlsx` — formatted workbook
