#!/usr/bin/env python3
"""Build an auditable Fan Yupei live-model handoff from the frozen raw run.

The canonical paid result under ``artifacts/live_results`` is never modified.
This script validates its aggregate fields against the individual trials and
creates an additive handoff view with flattened per-trial audit fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "artifacts" / "live_results" /
    "fan_yupei_openai_gpt-5.4_v2.json"
)
DEFAULT_OUTPUT = ROOT / "artifacts" / "fan_yupei_live_handoff.json"
OWNER = "Fan Yupei"
MODEL_LABEL = "OpenAI GPT-5.4"
FALLBACK_DEFINITION = (
    "D6 cost-ledger convention: a trial that fails the deterministic code "
    "check requires human fallback; fallback_used = not passed. This is a "
    "derived evaluation/cost field, not a provider-returned field or a "
    "separate tool call."
)


def _load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _close(left, right):
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def _unique_returned_models(record):
    values = []
    for item in record.get("model_identity_trace") or []:
        value = item.get("provider_returned_model_id")
        if value and value not in values:
            values.append(value)
    return values


def derive_handoff(payload, source_path: Path):
    """Return an enriched copy after validating all trial-derived totals."""

    run = payload.get("run") or {}
    summary = payload.get("summary") or {}
    trials = payload.get("trial_results")
    if run.get("backend") != "live":
        raise ValueError("source result is not a live run")
    if run.get("token_measurement") != "api_reported":
        raise ValueError("source result does not use API-reported tokens")
    if not isinstance(trials, list) or not trials:
        raise ValueError("source result has no trial_results")
    model_id = run.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("source result has no exact configured model id")

    audit_trials = []
    seen = set()
    for trial in trials:
        case_id = trial.get("case_id")
        trial_number = trial.get("trial")
        identity = (case_id, trial_number)
        if identity in seen:
            raise ValueError("duplicate trial id: %r" % (identity,))
        seen.add(identity)
        record = trial.get("record") or {}
        tokens_in = int(record.get("tokens_in", 0))
        tokens_out = int(record.get("tokens_out", 0))
        usage = record.get("model_usage") or []
        if sum(int(item.get("prompt_tokens", 0)) for item in usage) != tokens_in:
            raise ValueError("%s trial %s input-token trace mismatch" % identity)
        if sum(int(item.get("completion_tokens", 0)) for item in usage) != tokens_out:
            raise ValueError("%s trial %s output-token trace mismatch" % identity)
        success = trial.get("passed") is True
        failure_reasons = list(trial.get("fails") or [])
        if not success and not failure_reasons:
            failure_reasons = [
                record.get("backend_error") or record.get("stopped_by") or
                "deterministic code check failed"
            ]
        returned_models = _unique_returned_models(record)
        audit_trials.append({
            "case_id": case_id,
            "trial_id": "%s-trial-%s" % (case_id, trial_number),
            "trial_number": trial_number,
            "exact_requested_model_id": model_id,
            "provider_returned_model_ids": returned_models,
            "success": success,
            "failure_reasons": failure_reasons,
            "fallback_used": not success,
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "total_tokens": tokens_in + tokens_out,
            "latency_seconds": record.get("seconds"),
            "turns": record.get("turns"),
            "stopped_by": record.get("stopped_by"),
            "backend_error": record.get("backend_error"),
            "negative": trial.get("negative"),
            "family": trial.get("family"),
            "check_type": trial.get("check_type"),
        })

    total_trials = len(audit_trials)
    successful_trials = sum(item["success"] for item in audit_trials)
    failed_trials = total_trials - successful_trials
    input_tokens = sum(item["input_tokens"] for item in audit_trials)
    output_tokens = sum(item["output_tokens"] for item in audit_trials)
    fallback_count = sum(item["fallback_used"] for item in audit_trials)
    success_rate = successful_trials / total_trials
    fallback_rate = fallback_count / total_trials

    expected = {
        "trials": total_trials,
        "passed": successful_trials,
        "tokens_in": input_tokens,
        "tokens_out": output_tokens,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            raise ValueError(
                "summary.%s is %r, trial-derived value is %r" %
                (field, summary.get(field), value)
            )
    if not _close(summary.get("pass_rate"), success_rate):
        raise ValueError("summary.pass_rate does not match individual trials")
    if fallback_count != failed_trials:
        raise ValueError("fallback count does not equal failed-trial count")
    if not _close(fallback_rate, 1.0 - success_rate):
        raise ValueError("fallback and success rates are not complementary")

    returned_models = []
    for item in audit_trials:
        for value in item["provider_returned_model_ids"]:
            if value not in returned_models:
                returned_models.append(value)
    if returned_models:
        model_evidence = (
            "run.model_id records the requested OpenRouter route; "
            "provider-returned ids are retained per trial"
        )
    else:
        model_evidence = (
            "run.model_id records the exact configured/requested OpenRouter "
            "route; the frozen runner did not persist the provider response "
            "model field"
        )

    handoff_summary = {
        "owner": OWNER,
        "model_label": MODEL_LABEL,
        "exact_model_id": model_id,
        "model_id_evidence": model_evidence,
        "provider_returned_model_ids_observed": returned_models,
        "total_trials": total_trials,
        "successful_trials": successful_trials,
        "failed_trials": failed_trials,
        "success_rate": success_rate,
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "fallback_count": fallback_count,
        "fallback_rate": fallback_rate,
        "fallback_definition": FALLBACK_DEFINITION,
        "freeze_commit": run.get("freeze_commit_sha"),
        "source_commit": run.get("source_commit_sha"),
        "run_completed_at_utc": payload.get("generated_at_utc"),
        "source_result_path": str(source_path.relative_to(ROOT)),
        "source_result_sha256": _sha256(source_path),
    }
    return {
        "handoff_schema_version": "1.0",
        "source_result": {
            "path": str(source_path.relative_to(ROOT)),
            "sha256": _sha256(source_path),
            "run": run,
            "evaluation_set": payload.get("evaluation_set"),
        },
        "handoff_summary": handoff_summary,
        "audit_trials": audit_trials,
    }


def _serialise(payload):
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--check", action="store_true",
        help="validate the source and require the existing output to match",
    )
    args = parser.parse_args(argv)
    source_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    payload = derive_handoff(_load(source_path), source_path)
    rendered = _serialise(payload)

    if args.check:
        if not output_path.exists():
            raise SystemExit("handoff output is missing: %s" % output_path)
        if output_path.read_text(encoding="utf-8") != rendered:
            raise SystemExit("handoff output is stale: %s" % output_path)
        print(
            "Validated %d trials; %d successful; %d fallback; %d tokens."
            % (
                payload["handoff_summary"]["total_trials"],
                payload["handoff_summary"]["successful_trials"],
                payload["handoff_summary"]["fallback_count"],
                payload["handoff_summary"]["total_tokens"],
            )
        )
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print("Wrote %s" % output_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
