#!/usr/bin/env python3
"""Write the D4/D5 freeze manifest without contacting a model or network."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import config
import prompt
from harness import load_cases, load_key


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent


FROZEN_FILES = [
    "A2_reference_data/make_fixtures_B.py",
    "A2_reference_data/expected_outcomes_B.json",
    "A2_reference_data/data_B/as_of.json",
    "A2_reference_data/data_B/clinic_slots.json",
    "A2_reference_data/data_B/contacts.json",
    "A2_reference_data/data_B/patients.json",
    "A2_reference_data/data_B/referrals.json",
    "A2_reference_data/data_B/specialties.json",
    "A2_reference_data/data_B/urgency_bands.json",
    "A2_scaffold/agent.py",
    "A2_scaffold/backends.py",
    "A2_scaffold/config.py",
    "A2_scaffold/evaluation_scripts.py",
    "A2_scaffold/guardrails.py",
    "A2_scaffold/harness.py",
    "A2_scaffold/prompt.py",
    "A2_scaffold/run_eval.py",
    "A2_scaffold/tools.py",
    "artifacts/get_clinic_slots_descriptor_v1.json",
    "artifacts/get_clinic_slots_descriptor_v2.json",
]


def _git(*args):
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], check=True,
        capture_output=True, text=True)
    return completed.stdout.strip()


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _file_hash(relative_path):
    path = REPO_ROOT / relative_path
    return _sha256_bytes(path.read_bytes())


def _prompt_entry(version):
    text = prompt.build_system_prompt("B", version)
    descriptors = json.dumps(
        prompt.descriptors_for("B", version), ensure_ascii=False,
        sort_keys=True, separators=(",", ":"))
    return {
        "prompt_sha256": _sha256_bytes(text.encode("utf-8")),
        "descriptor_bundle_sha256": _sha256_bytes(
            descriptors.encode("utf-8")),
        "characters": len(text),
        "rough_tokens_chars_div_4": len(text) // 4,
    }


def build_manifest(freeze_sha):
    resolved = _git("rev-parse", "--verify", freeze_sha + "^{commit}")
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=normal")
    cases = load_cases("B")
    key = load_key("B")
    negatives = [case_id for case_id in cases
                 if key[case_id]["expected_decision"] != "book"]
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze": {
            "commit_sha": resolved,
            "source_head_sha": head,
            "checkout_state": _git("branch", "--show-current") or "detached",
            "intended_branch": "feature/evaluation",
            "main_base_sha": _git("merge-base", "origin/main", resolved),
            "working_tree_clean_before_generation": status == "",
        },
        "evaluation_set": {
            "problem": "B",
            "case_count": len(cases),
            "negative_case_count": len(negatives),
            "ordinary_trials_per_case": 1,
            "negative_trials_per_case": 3,
            "total_trials": len(cases) + 2 * len(negatives),
            "case_ids": cases,
            "negative_case_ids": negatives,
        },
        "controlled_descriptor_experiment": {
            "tool": prompt.EXPERIMENT_TOOL,
            "versions": {
                "v1": _prompt_entry("v1"),
                "v2": _prompt_entry("v2"),
            },
            "fixed": [
                "tool implementation", "routing rules", "other descriptors",
                "agent loop", "guardrails", "evaluation set", "trial policy",
                "model", "temperature", "max output tokens", "price inputs",
            ],
        },
        "file_sha256": {path: _file_hash(path) for path in FROZEN_FILES},
        "commands": {
            "validate_data": "python3 A2_reference_data/check_my_data.py",
            "tests": "python3 -m unittest discover -s tests -v",
            "scripted": (
                "python3 A2_scaffold/run_eval.py --freeze-sha %s" % resolved
            ),
            "live_v1": (
                "python3 A2_scaffold/run_eval.py --backend live "
                "--model openai/gpt-5.4 --descriptor-version v1 "
                "--approve-fixture-bookings --price-input-per-million 2.50 "
                "--price-output-per-million 15.00 "
                "--price-source https://openrouter.ai/openai/gpt-5.4 "
                "--price-date 2026-09-15 --freeze-sha %s" % resolved
            ),
            "live_v2": (
                "python3 A2_scaffold/run_eval.py --backend live "
                "--model openai/gpt-5.4 --descriptor-version v2 "
                "--approve-fixture-bookings --price-input-per-million 2.50 "
                "--price-output-per-million 15.00 "
                "--price-source https://openrouter.ai/openai/gpt-5.4 "
                "--price-date 2026-09-15 --freeze-sha %s" % resolved
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha", required=True)
    parser.add_argument("--output", default="artifacts/freeze_manifest.json")
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = REPO_ROOT / output
    payload = build_manifest(args.freeze_sha)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("Wrote %s" % output)
    print("Freeze: %s" % payload["freeze"]["commit_sha"])
    print("Cases/trials: %d/%d" % (
        payload["evaluation_set"]["case_count"],
        payload["evaluation_set"]["total_trials"]))


if __name__ == "__main__":
    main()
