import os
import sys
import unittest


SCAFFOLD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "A2_scaffold"))
if SCAFFOLD not in sys.path:
    sys.path.insert(0, SCAFFOLD)

from guardrails import GuardrailStop, Guardrails


class GuardrailsTests(unittest.TestCase):
    def assert_stop(self, callback, reason):
        with self.assertRaises(GuardrailStop) as raised:
            callback()
        self.assertEqual(raised.exception.reason, reason)
        self.assertTrue(raised.exception.detail)

    def test_step_cap_allows_limit_and_records_loud_stop(self):
        guards = Guardrails(max_turns=2, max_tokens=100, autonomy="act")
        guards.check_turns(2)
        self.assert_stop(lambda: guards.check_turns(3), "step_cap")
        self.assertEqual(guards.fired[-1]["guardrail"], "step_cap")

    def test_budget_ceiling_allows_limit_and_records_loud_stop(self):
        guards = Guardrails(max_turns=2, max_tokens=100, autonomy="act")
        guards.check_budget(100)
        self.assert_stop(lambda: guards.check_budget(101), "budget_ceiling")
        self.assertEqual(guards.fired[-1]["guardrail"], "budget_ceiling")

    def test_duplicate_action_is_order_independent_and_loud(self):
        guards = Guardrails(max_turns=2, max_tokens=100, autonomy="act")
        first = {"member": {"id": "M-1", "tags": ["a", "b"]},
                 "lines": [{"code": "X", "amount": 2}]}
        second = {"lines": [{"amount": 2, "code": "X"}],
                  "member": {"tags": ["a", "b"], "id": "M-1"}}
        guards.check_duplicate("lookup", first)
        self.assert_stop(lambda: guards.check_duplicate("lookup", second),
                         "duplicate_action")
        self.assertEqual(guards.fired[-1]["guardrail"], "duplicate_action")

    def test_action_arguments_are_snapshot_not_alias(self):
        guards = Guardrails(max_turns=2, max_tokens=100, autonomy="act")
        args = {"items": [1]}
        guards.check_duplicate("lookup", args)
        args["items"].append(2)
        guards.check_duplicate("lookup", {"items": [1, 2]})
        self.assertEqual(len(guards.fired), 0)

    def test_autonomy_gate_modes_are_recorded(self):
        suggest = Guardrails(2, 100, "suggest")
        self.assertFalse(suggest.gate("book", {"slot": "09:00"}))
        self.assertEqual(suggest.fired[-1]["guardrail"], "gate_held")

        confirm = Guardrails(2, 100, "confirm")
        self.assertFalse(confirm.gate("book", {"slot": "09:00"},
                                      approve=lambda *_: False))
        self.assertEqual(confirm.fired[-1]["guardrail"], "gate_held")
        self.assertTrue(confirm.gate("book", {"slot": "10:00"},
                                     approve=lambda *_: True))
        self.assertEqual(confirm.fired[-1]["guardrail"], "gate_passed")
        self.assertFalse(confirm.gate("book", {"slot": "10:30"},
                                      approve=lambda *_: "no"))
        self.assertEqual(confirm.fired[-1]["guardrail"], "gate_held")

        act = Guardrails(2, 100, "act")
        self.assertTrue(act.gate("book", {"slot": "11:00"}))
        self.assertEqual(act.fired[-1]["guardrail"], "gate_passed")

    def test_invalid_configuration_does_not_fail_silently(self):
        with self.assertRaises(ValueError):
            Guardrails(-1, 100, "act")
        with self.assertRaises(ValueError):
            Guardrails(1, 100, "unknown")


if __name__ == "__main__":
    unittest.main()
