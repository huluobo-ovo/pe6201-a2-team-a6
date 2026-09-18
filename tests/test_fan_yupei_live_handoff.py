import copy
import json
import unittest
from pathlib import Path

from analysis.build_fan_yupei_live_handoff import derive_handoff


ROOT = Path(__file__).resolve().parents[1]
RAW_RESULT = (
    ROOT / "artifacts" / "live_results" /
    "fan_yupei_openai_gpt-5.4_v2.json"
)


class FanYupeiLiveHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW_RESULT.read_text(encoding="utf-8"))

    def test_frozen_v2_aggregates_recompute_from_trials(self):
        handoff = derive_handoff(self.raw, RAW_RESULT)
        summary = handoff["handoff_summary"]
        self.assertEqual(summary["exact_model_id"], "openai/gpt-5.4")
        self.assertEqual(summary["total_trials"], 58)
        self.assertEqual(summary["successful_trials"], 25)
        self.assertEqual(summary["failed_trials"], 33)
        self.assertEqual(summary["total_input_tokens"], 287085)
        self.assertEqual(summary["total_output_tokens"], 10898)
        self.assertEqual(summary["total_tokens"], 297983)
        self.assertEqual(summary["fallback_count"], 33)
        self.assertAlmostEqual(summary["success_rate"], 25 / 58)
        self.assertAlmostEqual(summary["fallback_rate"], 33 / 58)
        self.assertEqual(len(handoff["audit_trials"]), 58)

    def test_each_audit_trial_has_required_machine_readable_fields(self):
        handoff = derive_handoff(self.raw, RAW_RESULT)
        required = {
            "case_id", "trial_id", "exact_requested_model_id", "success",
            "failure_reasons", "fallback_used", "input_tokens",
            "output_tokens", "total_tokens", "latency_seconds",
            "stopped_by", "backend_error",
        }
        for trial in handoff["audit_trials"]:
            self.assertTrue(required.issubset(trial))
            self.assertEqual(
                trial["total_tokens"],
                trial["input_tokens"] + trial["output_tokens"],
            )
            self.assertEqual(trial["fallback_used"], not trial["success"])

    def test_rejects_manual_aggregate_drift(self):
        altered = copy.deepcopy(self.raw)
        altered["summary"]["tokens_in"] += 1
        with self.assertRaisesRegex(ValueError, "trial-derived"):
            derive_handoff(altered, RAW_RESULT)


if __name__ == "__main__":
    unittest.main()
