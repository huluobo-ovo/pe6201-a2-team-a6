import unittest

from analysis.run_judgement import _decode_json_object, _validate_verdict


MODEL = "different/family"
PROMPT_SHA = "a" * 64
QUEUE_ITEM = {
    "case_id": "REF-1",
    "must_record": ["criterion one", "criterion two"],
}


def valid_verdict():
    return {
        "case_id": "REF-1",
        "item_verdicts": [
            {"criterion": "criterion one", "met": True, "reason": "present"},
            {"criterion": "criterion two", "met": False, "reason": "absent"},
        ],
        "verdict": False,
        "graded_by": "model: " + MODEL,
        "judge_prompt_sha256": PROMPT_SHA,
    }


class JudgementValidationTests(unittest.TestCase):
    def test_decodes_plain_or_fenced_json_object(self):
        self.assertEqual(_decode_json_object('{"a": 1}'), {"a": 1})
        self.assertEqual(
            _decode_json_object('```json\n{"a": 1}\n```'), {"a": 1})

    def test_accepts_exact_criteria_and_consistent_overall_verdict(self):
        value = valid_verdict()
        self.assertIs(
            _validate_verdict(value, QUEUE_ITEM, MODEL, PROMPT_SHA), value)

    def test_rejects_reworded_criterion(self):
        value = valid_verdict()
        value["item_verdicts"][0]["criterion"] = "paraphrased"
        with self.assertRaisesRegex(ValueError, "criteria"):
            _validate_verdict(value, QUEUE_ITEM, MODEL, PROMPT_SHA)

    def test_rejects_inconsistent_overall_verdict(self):
        value = valid_verdict()
        value["verdict"] = True
        with self.assertRaisesRegex(ValueError, "overall"):
            _validate_verdict(value, QUEUE_ITEM, MODEL, PROMPT_SHA)


if __name__ == "__main__":
    unittest.main()
