# D6 Cost Model — Liu Xuanlin

## Purpose
This folder contains the reproducible D6 cost analysis for PE6201 A2, Team A-6, Problem B.

The current `cost_inputs.csv` contains **dummy data only for formula testing**. Dummy values must be replaced with the team's frozen live-model results and sourced model prices before the final report.

## Files
- `cost_model.py` — reads the cost inputs, calculates the cost ledger, ±10 percentage-point success-rate sensitivity, and break-even success rate.
- `cost_inputs.csv` — input assumptions and live-model totals.
- `cost_summary.csv` — generated output table.

## Input fields
- `model`: live model name/ID.
- `trials`: number of live evaluation trials.
- `input_tokens`, `output_tokens`: measured live token usage across those trials.
- `input_price_per_m`, `output_price_per_m`: USD price per 1 million tokens.
- `successful_tasks`: number of successful tasks in the trials.
- `fallback_rate`: share of tasks routed to human fallback.
- `fallback_cost_per_task`: assumed USD cost of one human fallback.
- `monthly_fixed_cost`: assumed monthly fixed system cost in USD.
- `monthly_volume`: expected tasks per month.
- `manual_task_cost`: USD cost of handling one task manually; used as the break-even comparator.
- `price_source`, `price_date`: source and date for the model price.
- `notes`: assumptions or caveats.

## Calculations
1. **Variable model cost** = input-token cost + output-token cost.
2. **Expected fallback cost** = trials × fallback rate × fallback cost per task.
3. **Allocated fixed cost** = monthly fixed cost × trials / monthly volume.
4. **Cost per successful task** = total trial-set cost / successful tasks.
5. **Monthly cost** scales variable and fallback costs to monthly volume, then adds monthly fixed cost.
6. **Sensitivity** reruns the ledger at success rate −10 percentage points and +10 percentage points. For these sensitivity rows only, fallback rate moves inversely by the same amount.
7. **Break-even success rate** is the AI success rate where expected AI task cost equals the manual-only task cost, assuming unsuccessful AI tasks fall back to a human.

## Run
From the repository root:

```bash
python3 analysis/cost_model.py
```

Expected message:

```text
Wrote 3 rows to .../analysis/cost_summary.csv
IMPORTANT: Replace DUMMY inputs with live results before final reporting.
```

## Before final submission
Replace every dummy value with real or explicitly agreed data:
1. Freeze commit/model ID and live trial count.
2. Measured input/output tokens from the live battery.
3. Model prices in USD per 1M tokens, with source URL/reference and access date.
4. Actual success count and fallback rate from the frozen results.
5. Team-agreed fallback cost, fixed cost, monthly volume, and manual-task comparator.
6. Re-run `python3 analysis/cost_model.py` and use the regenerated `cost_summary.csv` in the report.

Do not use scripted token estimates as live measured usage.
