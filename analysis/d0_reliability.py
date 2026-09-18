"""Build the reproducible reliability diagnostic used in report section D0(b)."""

import argparse
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    REPO_ROOT
    / "artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "artifacts/d0_reliability.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate D0 reliability evidence from one frozen live result."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def median(values):
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def build_diagnostic(payload, source_file):
    trials = payload["trial_results"]
    total = len(trials)
    passed = sum(bool(trial["passed"]) for trial in trials)
    turns = [trial["record"]["turns"] for trial in trials]
    pass_rate = passed / total
    median_turns = median(turns)
    implied_step_reliability = pass_rate ** (1 / median_turns)

    failed = [trial for trial in trials if not trial["passed"]]
    last_tools = Counter()
    no_tool_trace = 0
    backend_errors = 0
    for trial in failed:
        record = trial["record"]
        trace = record.get("tool_trace") or []
        if trace:
            last_tools[trace[-1]["tool"]] += 1
        else:
            no_tool_trace += 1
        if record.get("backend_error"):
            backend_errors += 1

    return {
        "schema_version": "1.0",
        "source_file": str(source_file),
        "model": payload["run"]["model_id"],
        "descriptor_version": payload["run"]["descriptor_version"],
        "trials": total,
        "passed": passed,
        "failed": total - passed,
        "run_pass_rate_P": pass_rate,
        "median_turns_T": median_turns,
        "implied_per_step_reliability_s": implied_step_reliability,
        "predicted_run_pass_rate_by_turns": {
            str(turn_count): implied_step_reliability**turn_count
            for turn_count in (1, 2, 3, 4, 5)
        },
        "failed_trial_diagnostic": {
            "backend_error_trials": backend_errors,
            "failed_trials_without_tool_trace": no_tool_trace,
            "last_tool_before_failed_outcome": dict(last_tools.most_common()),
        },
        "limitations": [
            "The calculation treats turns as independent and equally reliable; real turns are neither.",
            "The inferred s is a diagnostic derived from whole-run outcomes, not a directly observed probability.",
            "Backend and response-format failures contribute to P and cannot be assigned to a preceding tool when no valid trace exists.",
        ],
    }


def main():
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    diagnostic = build_diagnostic(payload, args.input.relative_to(REPO_ROOT))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(diagnostic, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"P={diagnostic['run_pass_rate_P']:.6f}, "
        f"T={diagnostic['median_turns_T']:.1f}, "
        f"s={diagnostic['implied_per_step_reliability_s']:.6f}"
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
