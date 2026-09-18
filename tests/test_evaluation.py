"""D4/D5 checks for fixture coverage, trial policy and grading."""

import copy
import os
import sys
import unittest


SCAFFOLD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "A2_scaffold"))
if SCAFFOLD not in sys.path:
    sys.path.insert(0, SCAFFOLD)

import backends
import config
from agent import run_case
from harness import code_check, load_cases, load_key, run_set


YUPEI_CASES = {"REF-640%d" % index for index in range(1, 9)}
LIU_CASES = {"REF-680%d" % index for index in range(1, 7)}
INTEGRATION_CASES = {"REF-6901"}


class EvaluationHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = {
            "BACKEND": config.BACKEND,
            "PROBLEM": config.PROBLEM,
            "AUTONOMY": config.AUTONOMY,
        }
        config.BACKEND = "scripted"
        config.PROBLEM = "B"
        config.AUTONOMY = "confirm"

    @classmethod
    def tearDownClass(cls):
        for name, value in cls.original.items():
            setattr(config, name, value)

    def test_yupei_added_eight_labelled_cases(self):
        cases = set(load_cases("B"))
        key = load_key("B")
        self.assertTrue(YUPEI_CASES.issubset(cases))
        self.assertTrue(YUPEI_CASES.issubset(key))
        self.assertTrue(all(key[case_id]["expected_decision"] == "book"
                            for case_id in YUPEI_CASES))

    def test_scripted_backend_covers_every_current_problem_b_case(self):
        missing = set(load_cases("B")) - set(backends.SCRIPTS)
        self.assertEqual(missing, set())

    def test_merged_set_meets_case_count_and_preserves_teammate_cases(self):
        cases = set(load_cases("B"))
        self.assertGreaterEqual(len(cases), 30)
        self.assertLessEqual(len(cases), 50)
        self.assertTrue(LIU_CASES.issubset(cases))
        self.assertTrue(INTEGRATION_CASES.issubset(cases))

    def test_full_set_uses_one_and_three_trial_policy(self):
        results, judgement_queue = run_set(problem="B")
        key = load_key("B")
        negative_cases = {
            case_id for case_id, expected in key.items()
            if expected["expected_decision"] != "book"
        }
        expected_trials = len(key) + 2 * len(negative_cases)
        self.assertEqual(len(results), expected_trials)
        self.assertTrue(all(result["passed"] for result in results))
        self.assertEqual({item["case_id"] for item in judgement_queue},
                         {"REF-6401", "REF-6405", "REF-6407"})

    def test_missing_item_is_an_exact_code_check(self):
        key = load_key("B")
        record = run_case("REF-5614", problem="B")
        passed, failures = code_check(record, key["REF-5614"])
        self.assertTrue(passed, failures)

        wrong = copy.deepcopy(record)
        wrong["missing"] = "more information"
        passed, failures = code_check(wrong, key["REF-5614"])
        self.assertFalse(passed)
        self.assertTrue(any("missing" in failure for failure in failures))

    def test_booking_requires_one_executed_gated_action(self):
        key = load_key("B")
        record = run_case("REF-6401", problem="B")
        record["guardrails_fired"] = []
        passed, failures = code_check(record, key["REF-6401"])
        self.assertFalse(passed)
        self.assertTrue(any("gate passed" in failure for failure in failures))

    def test_negative_case_rejects_an_accidental_booking(self):
        key = load_key("B")
        record = run_case("REF-5590", problem="B")
        record["tool_trace"].append({
            "tool": "book_slot", "error": None,
            "args": {"referral_id": "REF-5590"},
        })
        passed, failures = code_check(record, key["REF-5590"])
        self.assertFalse(passed)
        self.assertTrue(any("gated action" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
