# D6 Cost Model — corrected to the official Problem B brief

Owner: Liu Xuanlin

This version replaces the earlier scenario baseline that used 1,000 tasks/month and US$6 fallback cost.

## Official Problem B inputs used

- Monthly volume: 4,000 referrals
- Triage nurse hourly rate: US$55/hour
- Escalation handling time: 10 minutes
- Failure cost: 55 × 10 / 60 = US$9.1667 (reported as US$9.17)

These values come from the PE6201 A2 brief, Problem B.

## Layer 3

The assignment brief defines the fixed monthly layer (storage, infrastructure, evaluation, monitoring, maintenance) but does not provide a numeric Problem B amount. We therefore retain US$150/month only as a transparent, editable team scenario assumption.

The CSV and workbook show:
1. monthly cost before fixed Layer 3; and
2. monthly total after adding the US$150 scenario assumption.

## Brief-aligned formulas

Layer 1 = measured input/output tokens × recorded list prices / trials

Layer 2 = (1 − measured success rate) × failure cost

Cost-to-serve per task = Layer 1 + Layer 2

Monthly cost = cost-to-serve per task × 4,000 + Layer 3

Sensitivity = measured success rate ±10 percentage points

Break-even = 1 − (E − C) / F

where:
- C = token-only cost per run of the cheaper model
- E = Layer 1 + Layer 2 of the higher-performing reference model
- F = US$9.1667 failure cost

GPT-5.4 is used as the reference because it has the highest measured deterministic code-pass rate among the five final-v2 batteries.

## Important grading note

The 30-case frozen set produced 58 trials per model because negative cases were repeated three times. Three judgement cases remain pending in each battery, so the cost model consistently uses deterministic code-pass rates for the success/fallback calculation.

## Files

- `cost_model.py`
- `cost_inputs.csv`
- `cost_summary.csv`
- `break_even.csv`
- `model_cost_audit.csv`
- `D6_report_text_400_words.md`
- `PE6201_D6_Cost_Model_Official_Brief.xlsx`
