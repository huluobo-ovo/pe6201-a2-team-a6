# D7 second failure: booking tool without precondition validation

This is separate from the action-loop failure in
`A2_scaffold/demo_loop_failure.py`. The controlled deletion removes one
tool-interface check: `validate_booking_slot`. The agent script, referral,
slot data, autonomy mode, and other guards stay the same across runs.

The scripted case is `REF-5602`. Its criteria say `band=routine`, and the
slot query returns routine slots. The deliberately erroneous model move then
proposes `OPH-C1 / 2026-09-15 09:40`, which belongs to the **urgent** band.
With the validator present, the agent stops before seeking approval or
calling `book_slot`. With the validator removed, the same proposal is accepted
and the agent records a wrong-band booking.

## Reproduction

From `A2_scaffold/`, run:

```text
python3 demo_loop_failure.py
```

No API key or network call is needed; the backend remains `scripted`. The
demonstration restores `validate_booking_slot` in a `finally` block.

| run | turns | tool calls | tokens | cost | decision | stopped_by |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| before: validator present | 4 | 4 | 14,880 | US$0.00163 | `escalate` | `booking_invalid` |
| after: validator removed | 4 | 5 | 21,600 | US$0.00234 | `book` | `None` |

The absent validator creates a semantic failure rather than a crash. The
booking would violate the referral's routine band, although the agent's
final decision says `book`. The error is visible by comparing the criteria,
queried slots, booking observation, and `stopped_by` field.

## Diagnosis

The fix belongs at the booking tool boundary: compare the proposed slot with
the referral's specialty, mandatory tests, duplicate history, urgency band,
window from `as_of`, and current slot capacity before executing the action.
The agent checks these preconditions before the approval gate, and
`book_slot` repeats the check so direct tool calls cannot bypass it.

The step cap and action de-duplication are not suitable substitutes. The bad
run uses four turns, below the eight-turn cap, and makes no repeated call.
Neither control can determine that an urgent slot was booked for a routine
referral.
