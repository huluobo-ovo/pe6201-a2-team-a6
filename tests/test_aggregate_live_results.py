import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from analysis.aggregate_live_results import _row


FREEZE = "f" * 40
CASES = ["REF-1", "REF-2"]


def manifest():
    return {
        "freeze": {"commit_sha": FREEZE},
        "evaluation_set": {
            "case_count": 2,
            "negative_case_count": 1,
            "ordinary_trials_per_case": 1,
            "negative_trials_per_case": 3,
            "total_trials": 4,
            "case_ids": CASES,
        },
        "controlled_descriptor_experiment": {
            "versions": {
                "v1": {
                    "prompt_sha256": "prompt-v1",
                    "descriptor_bundle_sha256": "descriptor-v1",
                },
                "v2": {
                    "prompt_sha256": "prompt-v2",
                    "descriptor_bundle_sha256": "descriptor-v2",
                },
            },
        },
    }


def payload():
    return {
        "run": {
            "backend": "live",
            "model_id": "provider/model",
            "prompt_version": "v2",
            "prompt_sha256": "prompt-v1",
            "descriptor_version": "v1",
            "descriptor_bundle_sha256": "descriptor-v1",
            "freeze_commit_sha": FREEZE,
            "source_commit_sha": FREEZE,
            "working_tree_clean_before_run": True,
            "token_measurement": "api_reported",
            "trial_policy": {
                "ordinary": 1,
                "negative": 3,
                "negative_definition": "expected decision is not book",
            },
            "fixture_booking_approval":
                "explicit_blanket_approval_for_local_simulation",
            "pricing": {
                "input_usd_per_million": 1.0,
                "output_usd_per_million": 2.0,
                "source": "https://example.test/model",
                "checked_on": "2026-09-15",
            },
        },
        "evaluation_set": {
            "case_count": 2,
            "negative_case_count": 1,
            "case_ids": CASES,
        },
        "summary": {
            "trials": 4,
            "passed": 3,
            "code_pass_rate": 0.75,
            "negative_trials": 3,
            "negative_passed": 2,
            "negative_code_pass_rate": 2 / 3,
            "median_turns": 2,
            "worst_case_turns": 3,
            "tokens_in": 100,
            "tokens_out": 20,
            "cost_usd": 0.01,
            "provider_reported_cost_usd": 0.01,
            "error_trials": 0,
            "judgement_pending": 1,
        },
    }


class AggregateValidationTests(unittest.TestCase):
    def test_accepts_exact_frozen_live_result(self):
        row = _row(Path("result.json"), payload(), manifest())
        self.assertTrue(row["compatible"])
        self.assertEqual(row["issues"], "")

    def test_rejects_dirty_or_hash_mismatched_result(self):
        candidate = copy.deepcopy(payload())
        candidate["run"]["working_tree_clean_before_run"] = False
        candidate["run"]["prompt_sha256"] = "wrong"
        row = _row(Path("result.json"), candidate, manifest())
        self.assertFalse(row["compatible"])
        self.assertIn("source tree was not clean", row["issues"])
        self.assertIn("prompt hash mismatch", row["issues"])

    def test_accepts_judgements_only_for_the_exact_source_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "result.json"
            path.write_text(json.dumps(payload()), encoding="utf-8")
            source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            judgement = {
                "source_file_sha256": source_hash,
                "passed": 2,
                "total": 3,
            }
            row = _row(path, payload(), manifest(), judgement)
            self.assertTrue(row["compatible"])
            self.assertEqual(row["judgement_status"], "complete")
            self.assertEqual(row["judgement_passed"], 2)

            judgement["source_file_sha256"] = "wrong"
            row = _row(path, payload(), manifest(), judgement)
            self.assertFalse(row["compatible"])
            self.assertIn("judgement source hash mismatch", row["issues"])


if __name__ == "__main__":
    unittest.main()
