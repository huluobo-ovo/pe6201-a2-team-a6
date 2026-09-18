# D4 Judgement Rubric

Use this only for cases whose answer-key `check_type` is
`code_and_judgement`. Code checks and judgement checks remain separate.

## Judge instruction

Read the decision record without looking at the model identity or its code-pass
flag. For each `must_record` item, decide whether the stated reason contains
specific, factually consistent evidence for that item. Do not reward a correct
decision reached with missing, invented or contradictory evidence. Return:

```json
{
  "case_id": "REF-0000",
  "item_verdicts": [
    {"criterion": "copied criterion", "met": true, "reason": "brief evidence"}
  ],
  "verdict": true,
  "graded_by": "person: NAME or model: PROVIDER/MODEL",
  "judge_prompt_sha256": "SHA256 of this file"
}
```

The overall judgement verdict is true only when every item is met. If a model
judges a live model, use a different model family and record the exact judge
model. Never fill `graded_by` with a person's name unless that person actually
performed the review.
