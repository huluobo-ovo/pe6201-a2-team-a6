"""PE6201 A2 D6 cost model.

This module converts live-model evaluation totals into a reproducible cost
ledger. The example CSV bundled with it is explicitly dummy data and must be
replaced by real live results before the final report.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


INPUT_COLUMNS = [
    "model",
    "trials",
    "input_tokens",
    "output_tokens",
    "input_price_per_m",
    "output_price_per_m",
    "successful_tasks",
    "fallback_rate",
    "fallback_cost_per_task",
    "monthly_fixed_cost",
    "monthly_volume",
    "manual_task_cost",
    "price_source",
    "price_date",
    "notes",
]

OUTPUT_COLUMNS = [
    "model",
    "scenario",
    "trials",
    "success_rate",
    "fallback_rate",
    "model_cost_total_usd",
    "model_cost_per_task_usd",
    "expected_fallback_cost_total_usd",
    "allocated_fixed_cost_total_usd",
    "total_cost_usd",
    "cost_per_successful_task_usd",
    "monthly_cost_usd",
    "break_even_success_rate",
    "manual_task_cost_usd",
    "price_source",
    "price_date",
    "notes",
]


def _as_float(row: Dict[str, str], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for '{key}': {row.get(key)!r}") from exc


def _clamp_rate(value: float) -> float:
    return max(0.0, min(1.0, value))


def token_cost_usd(
    input_tokens: float,
    output_tokens: float,
    input_price_per_m: float,
    output_price_per_m: float,
) -> float:
    """Return total model cost when prices are quoted per 1M tokens."""
    return (
        (input_tokens / 1_000_000.0) * input_price_per_m
        + (output_tokens / 1_000_000.0) * output_price_per_m
    )


def break_even_success_rate(
    model_cost_per_task: float,
    fixed_cost_per_task: float,
    fallback_cost_per_task: float,
    manual_task_cost: float,
) -> float:
    """Success rate where AI expected task cost equals manual-only cost.

    Assumption for this sensitivity/break-even view: an AI task that is not
    successfully completed falls back to a human at fallback_cost_per_task.
    The returned value is clamped to [0, 1].
    """
    if fallback_cost_per_task <= 0:
        return 0.0 if model_cost_per_task + fixed_cost_per_task <= manual_task_cost else 1.0

    rate = 1.0 - (
        (manual_task_cost - model_cost_per_task - fixed_cost_per_task)
        / fallback_cost_per_task
    )
    return _clamp_rate(rate)


def compute_row(
    row: Dict[str, str],
    *,
    scenario: str = "base",
    success_rate_override: float | None = None,
) -> Dict[str, float | str]:
    """Compute one ledger row from one model's aggregate live results."""
    trials = _as_float(row, "trials")
    successful_tasks = _as_float(row, "successful_tasks")
    if trials <= 0:
        raise ValueError("trials must be greater than 0")
    if successful_tasks < 0 or successful_tasks > trials:
        raise ValueError("successful_tasks must be between 0 and trials")

    input_tokens = _as_float(row, "input_tokens")
    output_tokens = _as_float(row, "output_tokens")
    input_price = _as_float(row, "input_price_per_m")
    output_price = _as_float(row, "output_price_per_m")
    base_fallback_rate = _clamp_rate(_as_float(row, "fallback_rate"))
    fallback_cost_per_task = _as_float(row, "fallback_cost_per_task")
    monthly_fixed_cost = _as_float(row, "monthly_fixed_cost")
    monthly_volume = _as_float(row, "monthly_volume")
    manual_task_cost = _as_float(row, "manual_task_cost")
    if monthly_volume <= 0:
        raise ValueError("monthly_volume must be greater than 0")

    base_success_rate = successful_tasks / trials
    success_rate = (
        base_success_rate
        if success_rate_override is None
        else _clamp_rate(success_rate_override)
    )

    # For ±10pp sensitivity only, assume failures routed to human move in the
    # opposite direction to success rate. The base scenario uses the measured
    # fallback_rate exactly as supplied by the team.
    if success_rate_override is None:
        fallback_rate = base_fallback_rate
    else:
        fallback_rate = _clamp_rate(
            base_fallback_rate + (base_success_rate - success_rate)
        )

    model_cost_total = token_cost_usd(
        input_tokens, output_tokens, input_price, output_price
    )
    model_cost_per_task = model_cost_total / trials
    expected_fallback_cost_total = trials * fallback_rate * fallback_cost_per_task
    allocated_fixed_cost_total = monthly_fixed_cost * (trials / monthly_volume)
    total_cost = (
        model_cost_total
        + expected_fallback_cost_total
        + allocated_fixed_cost_total
    )

    scenario_successful_tasks = trials * success_rate
    cost_per_successful_task = (
        total_cost / scenario_successful_tasks
        if scenario_successful_tasks > 0
        else float("inf")
    )

    fixed_cost_per_task = monthly_fixed_cost / monthly_volume
    monthly_cost = (
        model_cost_per_task * monthly_volume
        + fallback_rate * fallback_cost_per_task * monthly_volume
        + monthly_fixed_cost
    )

    be_rate = break_even_success_rate(
        model_cost_per_task=model_cost_per_task,
        fixed_cost_per_task=fixed_cost_per_task,
        fallback_cost_per_task=fallback_cost_per_task,
        manual_task_cost=manual_task_cost,
    )

    return {
        "model": row["model"],
        "scenario": scenario,
        "trials": int(trials) if trials.is_integer() else trials,
        "success_rate": success_rate,
        "fallback_rate": fallback_rate,
        "model_cost_total_usd": model_cost_total,
        "model_cost_per_task_usd": model_cost_per_task,
        "expected_fallback_cost_total_usd": expected_fallback_cost_total,
        "allocated_fixed_cost_total_usd": allocated_fixed_cost_total,
        "total_cost_usd": total_cost,
        "cost_per_successful_task_usd": cost_per_successful_task,
        "monthly_cost_usd": monthly_cost,
        "break_even_success_rate": be_rate,
        "manual_task_cost_usd": manual_task_cost,
        "price_source": row.get("price_source", ""),
        "price_date": row.get("price_date", ""),
        "notes": row.get("notes", ""),
    }


def _round_output(row: Dict[str, float | str]) -> Dict[str, str | float | int]:
    rounded: Dict[str, str | float | int] = {}
    for key, value in row.items():
        if isinstance(value, float):
            rounded[key] = round(value, 6)
        else:
            rounded[key] = value
    return rounded


def run_cost_model(input_csv: Path, output_csv: Path) -> List[Dict[str, float | str]]:
    """Read cost inputs, produce base and ±10pp success sensitivity rows."""
    with input_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in INPUT_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing input columns: {', '.join(missing)}")
        input_rows = list(reader)

    results: List[Dict[str, float | str]] = []
    for row in input_rows:
        if not row.get("model", "").strip():
            continue
        trials = _as_float(row, "trials")
        successful_tasks = _as_float(row, "successful_tasks")
        base_success = successful_tasks / trials
        results.extend([
            compute_row(row, scenario="base"),
            compute_row(
                row,
                scenario="success_minus_10pp",
                success_rate_override=base_success - 0.10,
            ),
            compute_row(
                row,
                scenario="success_plus_10pp",
                success_rate_override=base_success + 0.10,
            ),
        ])

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(_round_output(result))

    return results


def main() -> None:
    here = Path(__file__).resolve().parent
    input_csv = here / "cost_inputs.csv"
    output_csv = here / "cost_summary.csv"
    rows = run_cost_model(input_csv, output_csv)
    print(f"Wrote {len(rows)} rows to {output_csv}")
    print("IMPORTANT: Replace DUMMY inputs with live results before final reporting.")


if __name__ == "__main__":
    main()
