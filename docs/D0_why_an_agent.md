# D0 - Why an agent at all

This is report-ready wording for Problem B. The numerical evidence is generated
by `analysis/d0_reliability.py` and recorded in
`artifacts/d0_reliability.json`.

## D0(a) - The Class 4 ladder

Outpatient referral coordination belongs on rung 7 only after eliminating the
cheaper workflow rungs.

| Rung | Why it is insufficient or retained |
| --- | --- |
| 1 Single call | Cannot safely retrieve, check, search and conditionally book. |
| 2 Prompt chain | Fixes one path, but red flags stop early while valid referrals continue to booking. |
| 3 Routing | Selects a lane but cannot choose the next query from an observation. |
| 4 Parallelisation | Retained for independent checks; reduces turns but does not direct the workflow. |
| 5 Orchestrator-workers | Adds agents without improving the single governed booking decision and is out of scope. |
| 6 Evaluator-optimiser | Can revise against fixed criteria but cannot replace a changing retrieval-and-action path. |
| 7 Agent | The model selects tools at runtime, re-queries when needed and stops according to the case. |

Our paths genuinely vary: `REF-5590` stops when a red flag is found; a
missing-test case must name the exact item; a valid routine referral continues
through slot validation and booking. Every tool observation returns ground
truth that can correct the next step. The first irreversible action is
`book_slot`, which consumes capacity and records a patient appointment. This
governance cliff requires precondition validation, approval, at-most-once
execution, and step and token caps. Rung 7 therefore buys adaptable sequencing
at the cost of variable calls, latency, tokens and non-enumerable paths.

## D0(b) - The two tests

The ground-truth test passes because machine-speed records can contradict the
model: referral rows provide clinical facts and attached tests; specialty rules
provide red flags, mandatory tests, bands and windows; patient records reveal
duplicates; slot rows provide current capacity; and the booking ledger confirms
the write. Missing or conflicting facts must produce `ask` or `escalate`. Without
these objective records we would use a workflow with a human gate.

For the arithmetic test we use the strongest submitted v2 live result, GPT-5.4,
not the deterministic scripted replay. It passed 25/58 trials, so `P = 0.4310`,
with median `T = 2` turns:

`s = P^(1/T) = 0.4310^(1/2) = 0.6565`.

| Turns | Predicted success at constant s |
| ---: | ---: |
| 1 | 65.7% |
| 2 | 43.1% |
| 3 | 28.3% |
| 4 | 18.6% |
| 5 | 12.2% |

The main weakness is step/protocol quality, not the cap: 22 failures recorded
backend or response-format errors, other failures omitted exact test identifiers,
and no run hit the eight-turn cap. `lookup_patient` was the last logged tool in
25 failed traces, but commonly ran in parallel before final synthesis, so this is
not proof that the lookup failed. We should constrain response structure and
bind reported missing items to tool output while retaining parallel calls. The
calculation is diagnostic only: turns are not independent or equally difficult.

## D0(c) - What good looks like

1. Name the decision and trigger from traceable records, not an unsupported story.
2. Apply red flags, required tests, urgency band and date window exactly.
3. Call `book_slot` at most once, after all preconditions and the gate pass.
4. Return `ask` or `escalate` rather than inventing a fact or slot.
5. Use the shortest dependency-respecting path and beat manual cost after fallback.

These statements are the acceptance criteria measured downstream. They were
formalised after the first agent commits, so we disclose that chronology rather
than claiming the original pre-code D0(c) timing was met.
