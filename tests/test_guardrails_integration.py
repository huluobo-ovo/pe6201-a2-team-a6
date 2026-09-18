"""D3 integration checks for guardrails in the complete scripted agent loop.

These tests deliberately exercise ``agent.run_case`` rather than calling the
Guardrails class directly.  Each test supplies a temporary scripted backend
case or configuration and restores all shared state before returning.
"""

import copy
import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch


SCAFFOLD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "A2_scaffold"))
if SCAFFOLD not in sys.path:
    sys.path.insert(0, SCAFFOLD)

import agent
import backends
import config
import harness
import tools


@contextmanager
def isolated_runtime(scripts=None, **config_overrides):
    """Temporarily change run_case inputs, restoring every shared object."""
    original_scripts = dict(backends.SCRIPTS)
    original_registry = {
        problem: dict(registry)
        for problem, registry in tools.REGISTRY.items()
    }
    original_config = {
        name: getattr(config, name)
        for name in ("BACKEND", "PROBLEM", "MAX_TURNS",
                     "MAX_TOKENS_PER_RUN", "AUTONOMY")
    }
    try:
        if scripts is not None:
            backends.SCRIPTS.update(copy.deepcopy(scripts))
        for name, value in config_overrides.items():
            setattr(config, name, value)
        yield
    finally:
        backends.SCRIPTS.clear()
        backends.SCRIPTS.update(original_scripts)
        tools.REGISTRY.clear()
        tools.REGISTRY.update(original_registry)
        for name, value in original_config.items():
            setattr(config, name, value)


def action_script(*calls):
    """Build a script whose calls each occupy a separate agent turn."""
    return [
        {"thought": "integration test action %d" % (index + 1),
         "calls": [call]}
        for index, call in enumerate(calls)
    ] + [{"final": {"decision": "test_complete"},
          "thought": "integration test conclusion"}]


class GuardrailsIntegrationTests(unittest.TestCase):
    """Verify that each D3 stop is observable through a full run_case."""

    def test_duplicate_action_stops_full_run_case(self):
        repeated = ("get_referral", {"referral_id": "REF-5602"})
        scripts = {"TEST-DUPLICATE": action_script(repeated, repeated)}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B",
                              MAX_TURNS=8, MAX_TOKENS_PER_RUN=60000,
                              AUTONOMY="act"):
            record = agent.run_case("TEST-DUPLICATE", problem="B")

        self.assertEqual(record["stopped_by"], "duplicate_action")
        self.assertEqual(record["turns"], 2)
        self.assertEqual(record["evidence"], ["get_referral"])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "duplicate_action")

    def test_step_cap_stops_full_run_case(self):
        scripts = {"TEST-STEP-CAP": action_script(
            ("get_referral", {"referral_id": "REF-5602"}),
            ("lookup_patient", {"patient_id": "P-1180"}),
        )}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B",
                              MAX_TURNS=1, MAX_TOKENS_PER_RUN=60000,
                              AUTONOMY="act"):
            record = agent.run_case("TEST-STEP-CAP", problem="B")

        self.assertEqual(record["stopped_by"], "step_cap")
        self.assertEqual(record["turns"], 2)
        self.assertEqual(record["evidence"], ["get_referral"])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "step_cap")

    def test_budget_ceiling_stops_full_run_case(self):
        scripts = {"TEST-BUDGET": action_script(
            ("get_referral", {"referral_id": "REF-5602"}),
            ("lookup_patient", {"patient_id": "P-1180"}),
        )}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B",
                              MAX_TURNS=8, MAX_TOKENS_PER_RUN=4000,
                              AUTONOMY="act"):
            record = agent.run_case("TEST-BUDGET", problem="B")

        self.assertEqual(record["stopped_by"], "budget_ceiling")
        self.assertEqual(record["turns"], 1)
        self.assertEqual(record["evidence"], ["get_referral"])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "budget_ceiling")

    def test_confirm_gate_holds_real_booking_before_book_slot(self):
        """The shipped multi-step booking flow must stop at its gate."""
        with isolated_runtime(BACKEND="scripted", PROBLEM="B",
                              MAX_TURNS=8, MAX_TOKENS_PER_RUN=60000,
                              AUTONOMY="confirm"):
            record = agent.run_case(
                "REF-5602", problem="B",
                approve=lambda action, payload: False)

        self.assertEqual(record["stopped_by"], "gate_held")
        self.assertNotIn("book_slot", record["evidence"])
        self.assertNotIn("book_slot",
                         [entry["tool"] for entry in record["tool_trace"]])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "gate_held")

    def test_live_confirm_needs_explicit_approval(self):
        class OfflineLiveBackend(backends.ScriptedBackend):
            name = "live"

        with isolated_runtime(BACKEND="live", PROBLEM="B", AUTONOMY="confirm"):
            with patch.object(agent, "make_backend",
                              side_effect=lambda case_id, **_: OfflineLiveBackend(case_id)):
                record = agent.run_case("REF-5602", problem="B")

        self.assertEqual(record["stopped_by"], "gate_held")
        self.assertNotIn("book_slot", record["evidence"])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "gate_held")

    def test_scripted_booking_still_passes_confirm_gate(self):
        with isolated_runtime(BACKEND="scripted", PROBLEM="B",
                              AUTONOMY="confirm"):
            record = agent.run_case("REF-5602", problem="B")

        self.assertEqual(record["decision"], "book")
        self.assertIsNone(record["stopped_by"])
        self.assertIn("book_slot", record["evidence"])
        self.assertIn("gate_passed", [event["guardrail"]
                                      for event in record["guardrails_fired"]])

    def test_invalid_slot_is_stopped_before_approval(self):
        args = {"clinic": "NONEXISTENT", "date": "2026-01-01",
                "time": "00:00", "referral_id": "REF-5602"}
        scripts = {"TEST-INVALID-BOOKING": action_script(("book_slot", args))}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B",
                              AUTONOMY="confirm"):
            record = agent.run_case("TEST-INVALID-BOOKING", problem="B")

        self.assertEqual(record["stopped_by"], "booking_invalid")
        self.assertEqual(record["evidence"], [])
        self.assertEqual(record["tool_trace"], [])
        self.assertEqual(record["guardrails_fired"][-1]["guardrail"],
                         "booking_invalid")

    def test_booking_another_referral_is_stopped_before_approval(self):
        args = {"clinic": "OPH-C2", "date": "2026-10-14",
                "time": "11:20", "referral_id": "REF-5602"}
        scripts = {"TEST-WRONG-CASE": action_script(("book_slot", args))}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B",
                              AUTONOMY="confirm"):
            record = agent.run_case("TEST-WRONG-CASE", problem="B")

        self.assertEqual(record["stopped_by"], "booking_invalid")
        self.assertEqual(record["evidence"], [])
        self.assertEqual(record["tool_trace"], [])

    def test_tool_rejects_invalid_booking_when_called_directly(self):
        with self.assertRaisesRegex(ValueError, "slot is not available"):
            tools.book_slot("NONEXISTENT", "2026-01-01", "00:00", "REF-5602")

    def test_booking_preconditions_follow_referral_protocol(self):
        attempts = [
            ("red flag", "REF-5590", "OPH-C2", "2026-10-14", "11:20"),
            ("mandatory tests", "REF-5614", "OPH-C2", "2026-10-14", "11:20"),
            ("specialty mismatch", "REF-5671", "OPH-C2", "2026-10-14", "11:20"),
            ("future same-specialty", "REF-5684", "OPH-C2", "2026-10-14", "11:20"),
            ("required band and window", "REF-5602", "OPH-C1", "2026-09-15", "09:40"),
            ("required band and window", "REF-5602", "OPH-C2", "2026-11-10", "09:40"),
            ("required band and window", "REF-5602", "OPH-C2", "2026-09-23", "11:20"),
        ]
        for reason, referral_id, clinic, date, time in attempts:
            with self.subTest(referral_id=referral_id, clinic=clinic, date=date):
                with self.assertRaisesRegex(ValueError, reason):
                    tools.validate_booking_slot(clinic, date, time, referral_id)

    def test_final_book_without_action_is_rejected(self):
        scripts = {"TEST-FINAL-ONLY": [{"final": {
            "decision": "book",
            "booked": {"clinic": "OPH-C2", "date": "2026-10-14",
                       "time": "11:20"},
        }}]}
        with isolated_runtime(scripts, BACKEND="scripted", PROBLEM="B"):
            record = agent.run_case("TEST-FINAL-ONLY", problem="B")

        self.assertEqual(record["stopped_by"], "booking_unverified")
        self.assertEqual(record["decision"], "escalate")
        self.assertEqual(record["tool_trace"], [])

    def test_code_check_requires_a_real_booking_trace(self):
        expected = harness.load_key("B")["REF-5602"]
        forged = {"case_id": "REF-5602", "decision": "book",
                  "booked": expected["booked"], "tool_trace": [],
                  "guardrails_fired": []}
        passed, fails = harness.code_check(forged, expected)
        self.assertFalse(passed)
        self.assertIn("no matching approved book_slot result in tool trace",
                      fails)

        real = agent.run_case("REF-5602", problem="B")
        passed, fails = harness.code_check(real, expected)
        self.assertTrue(passed, fails)

    def test_final_book_must_match_actual_booking(self):
        script = copy.deepcopy(backends.SCRIPTS["REF-5602"])
        script[-1]["final"]["booked"]["time"] = "14:00"
        with isolated_runtime({"REF-5602": script}, BACKEND="scripted",
                              PROBLEM="B", AUTONOMY="confirm"):
            record = agent.run_case("REF-5602", problem="B")

        self.assertEqual(record["stopped_by"], "booking_unverified")
        self.assertEqual(record["decision"], "escalate")
        self.assertIn("book_slot", record["evidence"])


if __name__ == "__main__":
    unittest.main()
