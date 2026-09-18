#!/usr/bin/env python3
import csv
from pathlib import Path

INPUT = Path(__file__).with_name("cost_inputs.csv")
OUTPUT = Path(__file__).with_name("cost_summary.csv")
BREAK_EVEN = Path(__file__).with_name("break_even.csv")

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def price_book_total(row):
    return (
        float(row["input_tokens"]) / 1_000_000 * float(row["input_price_per_m"])
        + float(row["output_tokens"]) / 1_000_000 * float(row["output_price_per_m"])
    )

with INPUT.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

summary = []
base_metrics = {}

for row in rows:
    trials = int(row["trials"])
    successes = int(row["successful_tasks"])
    base_success = successes / trials
    failure_cost = float(row["failure_cost_per_task"])
    volume = int(row["monthly_volume"])
    fixed = float(row["monthly_fixed_cost"])

    model_total = price_book_total(row)
    layer1 = model_total / trials

    for scenario, success in [
        ("base", base_success),
        ("success_minus_10pp", clamp(base_success - 0.10)),
        ("success_plus_10pp", clamp(base_success + 0.10)),
    ]:
        fallback = 1 - success
        layer2 = fallback * failure_cost
        cost_to_serve = layer1 + layer2
        monthly_before_fixed = cost_to_serve * volume
        monthly_total = monthly_before_fixed + fixed

        summary.append({
            "model": row["model"],
            "scenario": scenario,
            "trials": trials,
            "success_rate": success,
            "fallback_rate": fallback,
            "layer1_model_cost_per_task_usd": layer1,
            "layer2_expected_fallback_per_task_usd": layer2,
            "cost_to_serve_per_task_usd": cost_to_serve,
            "monthly_before_fixed_usd": monthly_before_fixed,
            "layer3_fixed_monthly_usd": fixed,
            "monthly_total_usd": monthly_total,
            "price_source": row["price_source"],
            "price_date": row["price_date"],
            "notes": "D6 brief formula: Layer1 + (1-success)*failure_cost; monthly = per-task cost × volume + Layer3.",
        })

        if scenario == "base":
            base_metrics[row["model"]] = {
                "layer1": layer1,
                "success": success,
                "failure_cost": failure_cost,
                "cost_to_serve": cost_to_serve,
            }

headers = list(summary[0].keys())
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=headers)
    w.writeheader()
    w.writerows(summary)

# Break-even against GPT-5.4, the highest measured code-pass model.
reference = "openai/gpt-5.4"
ref = base_metrics[reference]
E = ref["cost_to_serve"]
F = ref["failure_cost"]

be_rows = []
for model, m in base_metrics.items():
    C = m["layer1"]
    if C < ref["layer1"]:
        p_be = clamp(1 - ((E - C) / F))
        be_rows.append({
            "cheap_model": model,
            "reference_model": reference,
            "cheap_layer1_cost_per_task_usd": C,
            "reference_expected_cost_per_task_usd": E,
            "failure_cost_usd": F,
            "break_even_success_rate": p_be,
            "measured_cheap_success_rate": m["success"],
            "gap_to_break_even_percentage_points": (m["success"] - p_be) * 100,
            "clears_break_even": m["success"] >= p_be,
            "notes": "Brief formula: p* = 1 - (E - C)/F.",
        })

with BREAK_EVEN.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(be_rows[0].keys()))
    w.writeheader()
    w.writerows(be_rows)

print(f"Wrote {OUTPUT}")
print(f"Wrote {BREAK_EVEN}")
