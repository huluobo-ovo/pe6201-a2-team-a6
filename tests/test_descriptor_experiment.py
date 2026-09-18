"""Controlled v1/v2 slot-descriptor and live-run safety checks."""

import os
import sys
import unittest
from unittest.mock import patch


SCAFFOLD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "A2_scaffold"))
if SCAFFOLD not in sys.path:
    sys.path.insert(0, SCAFFOLD)

import backends
import prompt
import tools
from backends import LiveBackend, LiveResponseError, _parse_move


class DescriptorExperimentTests(unittest.TestCase):
    def test_only_slot_descriptor_changes_between_v1_and_v2(self):
        v1 = {item["name"]: item for item in prompt.descriptors_for("B", "v1")}
        v2 = {item["name"]: item for item in prompt.descriptors_for("B", "v2")}
        self.assertEqual(set(v1), set(tools.REGISTRY["B"]))
        self.assertEqual(set(v2), set(tools.REGISTRY["B"]))
        changed = {name for name in v1 if v1[name] != v2[name]}
        self.assertEqual(changed, {"get_clinic_slots"})

    def test_descriptor_variants_match_the_same_callable_contract(self):
        for version in ("v1", "v2"):
            descriptor = next(
                item for item in prompt.descriptors_for("B", version)
                if item["name"] == "get_clinic_slots")
            self.assertEqual(
                set(descriptor["args"]), {"specialty", "band", "from/to"})
            self.assertIs(tools.REGISTRY["B"]["get_clinic_slots"],
                          tools.get_clinic_slots)

    def test_prompts_are_distinct_and_contain_selected_failure_semantics(self):
        v1 = prompt.build_system_prompt("B", "v1")
        v2 = prompt.build_system_prompt("B", "v2")
        self.assertNotEqual(v1, v2)
        self.assertIn("Returns an empty list when no slot is found", v1)
        self.assertIn("no_slot_in_window", v2)
        self.assertIn("Never widen the window", v2)
        for text in (v1, v2):
            self.assertIn("red_flag_term", text)
            self.assertIn("duplicate_future_appointment", text)
            self.assertIn("instruction_in_referral_free_text", text)

    def test_live_parser_accepts_one_move_and_rejects_a_trajectory(self):
        move = _parse_move(
            '{"calls":[["get_referral",{"referral_id":"REF-5590"}]]}')
        self.assertEqual(move["calls"][0][0], "get_referral")
        with self.assertRaises(LiveResponseError):
            _parse_move('{"calls": []}\n{"final": {}}')

    def test_live_backend_records_requested_and_returned_model_ids(self):
        payload = {
            "model": "openai/gpt-5.4-2026-09-01",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
            "choices": [{"message": {"content": (
                '{"final":{"decision":"escalate","reason":"test"}}'
            )}}],
        }
        previous_model = backends.config.MODEL
        backends.config.MODEL = "openai/gpt-5.4"
        try:
            backend = LiveBackend("REF-5590", [], "system")
            with patch.object(backends, "_live_call", return_value=payload):
                backend.next_move([])
        finally:
            backends.config.MODEL = previous_model

        self.assertEqual(backend.model_identity_trace, [{
            "requested_model_id": "openai/gpt-5.4",
            "provider_returned_model_id": "openai/gpt-5.4-2026-09-01",
        }])


if __name__ == "__main__":
    unittest.main()
