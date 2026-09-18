#!/usr/bin/env python3
"""Validate and aggregate D5 live-result JSON files into report-ready tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row(path, payload, manifest, judgement=None):
    run = payload.get("run", {})
    evaluation = payload.get("evaluation_set", {})
    summary = payload.get("summary", {})
    expected_freeze = manifest["freeze"]["commit_sha"]
    expected_set = manifest["evaluation_set"]
    expected_cases = expected_set["case_ids"]
    case_ids = evaluation.get("case_ids", [])
    issues = []
    if run.get("backend") != "live":
        issues.append("backend is not live")
    if run.get("freeze_commit_sha") != expected_freeze:
        issues.append("freeze SHA mismatch")
    if run.get("source_commit_sha") != expected_freeze:
        issues.append("source SHA mismatch")
    if run.get("working_tree_clean_before_run") is not True:
        issues.append("source tree was not clean")
    if case_ids != expected_cases:
        issues.append("evaluation case list mismatch")
    if evaluation.get("case_count") != expected_set["case_count"]:
        issues.append("case count mismatch")
    if (evaluation.get("negative_case_count") !=
            expected_set["negative_case_count"]):
        issues.append("negative-case count mismatch")
    if summary.get("trials") != expected_set["total_trials"]:
        issues.append("trial count mismatch")
    if run.get("token_measurement") != "api_reported":
        issues.append("tokens are not API-reported")
    if run.get("prompt_version") != "v2":
        issues.append("prompt version is not v2")
    descriptor_version = run.get("descriptor_version")
    expected_versions = manifest["controlled_descriptor_experiment"]["versions"]
    expected_descriptor = expected_versions.get(descriptor_version)
    if expected_descriptor is None:
        issues.append("descriptor version is not frozen")
    else:
        if run.get("prompt_sha256") != expected_descriptor["prompt_sha256"]:
            issues.append("prompt hash mismatch")
        if (run.get("descriptor_bundle_sha256") !=
                expected_descriptor["descriptor_bundle_sha256"]):
            issues.append("descriptor hash mismatch")
    if run.get("trial_policy") != {
            "ordinary": expected_set["ordinary_trials_per_case"],
            "negative": expected_set["negative_trials_per_case"],
            "negative_definition": "expected decision is not book",
    }:
        issues.append("trial policy mismatch")
    if (run.get("fixture_booking_approval") !=
            "explicit_blanket_approval_for_local_simulation"):
        issues.append("fixture booking approval missing")
    pricing = run.get("pricing") or {}
    if any(pricing.get(field) is None for field in (
            "input_usd_per_million", "output_usd_per_million",
            "source", "checked_on")):
        issues.append("price provenance incomplete")
    judgement_passed = judgement_total = None
    judgement_status = "not supplied"
    if judgement is not None:
        if judgement.get("source_file_sha256") != _sha256(path):
            issues.append("judgement source hash mismatch")
            judgement_status = "source mismatch"
        else:
            judgement_passed = judgement.get("passed")
            judgement_total = judgement.get("total")
            judgement_status = "complete"
    return {
        "file": path.name,
        "model": run.get("model_id"),
        "prompt_version": run.get("prompt_version"),
        "descriptor_version": run.get("descriptor_version"),
        "freeze_sha": run.get("freeze_commit_sha"),
        "cases": evaluation.get("case_count"),
        "negative_cases": evaluation.get("negative_case_count"),
        "trials": summary.get("trials"),
        "code_passed": summary.get("passed"),
        "code_pass_rate": summary.get("code_pass_rate"),
        "negative_trials": summary.get("negative_trials"),
        "negative_passed": summary.get("negative_passed"),
        "negative_code_pass_rate": summary.get("negative_code_pass_rate"),
        "median_turns": summary.get("median_turns"),
        "worst_case_turns": summary.get("worst_case_turns"),
        "tokens_in": summary.get("tokens_in"),
        "tokens_out": summary.get("tokens_out"),
        "cost_usd": summary.get("cost_usd"),
        "provider_reported_cost_usd":
            summary.get("provider_reported_cost_usd"),
        "error_trials": summary.get("error_trials"),
        "judgement_pending": summary.get("judgement_pending"),
        "judgement_passed": judgement_passed,
        "judgement_total": judgement_total,
        "judgement_status": judgement_status,
        "compatible": not issues,
        "issues": "; ".join(issues),
    }


def _paired(rows):
    groups = {}
    for row in rows:
        key = (row["model"], row["freeze_sha"])
        groups.setdefault(key, {})[row["descriptor_version"]] = row
    pairs = []
    for (model, freeze_sha), versions in groups.items():
        if "v1" not in versions or "v2" not in versions:
            continue
        v1, v2 = versions["v1"], versions["v2"]
        pairs.append({
            "model": model,
            "freeze_sha": freeze_sha,
            "v2_minus_v1_code_pass_rate": (
                v2["code_pass_rate"] - v1["code_pass_rate"]),
            "v2_minus_v1_negative_code_pass_rate": (
                v2["negative_code_pass_rate"] -
                v1["negative_code_pass_rate"]),
            "v2_minus_v1_median_turns": (
                v2["median_turns"] - v1["median_turns"]),
            "v2_minus_v1_tokens": (
                v2["tokens_in"] + v2["tokens_out"] -
                v1["tokens_in"] - v1["tokens_out"]),
            "v2_minus_v1_cost_usd": v2["cost_usd"] - v1["cost_usd"],
        })
    return pairs


def _fmt_rate(value):
    return "-" if value is None else "%.1f%%" % (100 * value)


def _markdown(rows, pairs):
    lines = [
        "# D5 Live Model Battery",
        "",
        "Only rows marked compatible share the frozen commit and exact case list.",
        "",
        "| Model | Descriptor | Trials | Code pass | Negative pass | Judgement | Median turns | Tokens in/out | Cost (USD) | Errors | Compatible |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s / %s | %.4f | %s | %s |" % (
                row["model"] or "-", row["descriptor_version"] or "-",
                row["trials"], _fmt_rate(row["code_pass_rate"]),
                _fmt_rate(row["negative_code_pass_rate"]),
                ("%s/%s" % (row["judgement_passed"],
                             row["judgement_total"])
                 if row["judgement_status"] == "complete" else "-"),
                row["median_turns"], row["tokens_in"], row["tokens_out"],
                row["cost_usd"] or 0.0, row["error_trials"],
                "yes" if row["compatible"] else "no: " + row["issues"]))
    lines += ["", "## Paired v1/v2 deltas", ""]
    if not pairs:
        lines.append("No same-model v1/v2 pair is available yet.")
    else:
        lines += [
            "| Model | Pass-rate delta | Negative delta | Median-turn delta | Token delta | Cost delta (USD) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for pair in pairs:
            lines.append(
                "| %s | %+.1f pp | %+.1f pp | %+.1f | %+d | %+.4f |" % (
                    pair["model"],
                    100 * pair["v2_minus_v1_code_pass_rate"],
                    100 * pair["v2_minus_v1_negative_code_pass_rate"],
                    pair["v2_minus_v1_median_turns"],
                    pair["v2_minus_v1_tokens"],
                    pair["v2_minus_v1_cost_usd"]))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="artifacts/live_results")
    parser.add_argument("--freeze-manifest", default="artifacts/freeze_manifest.json")
    parser.add_argument("--output-json", default="artifacts/live_battery_summary.json")
    parser.add_argument("--output-csv", default="artifacts/live_battery_summary.csv")
    parser.add_argument("--output-md", default="artifacts/live_battery_summary.md")
    parser.add_argument("--judgements", default="artifacts/judgement_results.json")
    args = parser.parse_args()

    input_dir = ROOT / args.input_dir
    manifest = _load(ROOT / args.freeze_manifest)
    expected_freeze = manifest["freeze"]["commit_sha"]
    paths = sorted(input_dir.glob("*.json")) if input_dir.exists() else []
    judgement_path = ROOT / args.judgements
    judgement_payload = _load(judgement_path) if judgement_path.exists() else {}
    judgements = {
        item["source_file"]: item
        for item in judgement_payload.get("results", [])
    }
    rows = [_row(
        path, _load(path), manifest,
        judgements.get(str(path.relative_to(ROOT))))
            for path in paths]
    pairs = _paired([row for row in rows if row["compatible"]])
    payload = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_sha": expected_freeze,
        "result_count": len(rows),
        "compatible_result_count": sum(row["compatible"] for row in rows),
        "rows": rows,
        "paired_descriptor_deltas": pairs,
    }

    json_path = ROOT / args.output_json
    csv_path = ROOT / args.output_csv
    md_path = ROOT / args.output_md
    for path in (json_path, csv_path, md_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    fields = list(rows[0]) if rows else [
        "file", "model", "prompt_version", "descriptor_version",
        "freeze_sha", "cases", "negative_cases", "trials", "code_passed",
        "code_pass_rate", "negative_trials", "negative_passed",
        "negative_code_pass_rate", "median_turns", "worst_case_turns",
        "tokens_in", "tokens_out", "cost_usd",
        "provider_reported_cost_usd", "error_trials", "judgement_pending",
        "judgement_passed", "judgement_total", "judgement_status",
        "compatible", "issues",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    md_path.write_text(_markdown(rows, pairs), encoding="utf-8")
    print("Aggregated %d live result(s), %d compatible." % (
        len(rows), payload["compatible_result_count"]))


if __name__ == "__main__":
    main()
