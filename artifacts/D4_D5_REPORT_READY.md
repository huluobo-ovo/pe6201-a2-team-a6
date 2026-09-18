# D4/D5 Report-Ready Findings — Fan Yupei

Freeze: `e36bb1b2fcad625ed944e7df863165d95c0ef53f`

## Evaluation set and method

The frozen Problem B set contains 30 independently reset cases: 15 supplied,
eight by Fan Yupei (`REF-6401`–`REF-6408`), six by Liu Xuanlin and one clearly
attributed integration case. Fan's cases isolate urgency bands, two-test
requirements, specialties with no mandatory tests, duplicate checks and exact
first-slot booking. The integrated set has 14 negative cases. This is above the
brief's recommended 6–10 because all labelled teammate cases were preserved;
the denominator is disclosed rather than trimmed after seeing results.

Ordinary cases ran once and negative cases three times, producing 58 trials per
arm. The code grader checks the decision, canonical trigger, exact named missing
item, exact clinic/date/time, one approved gated booking and a matching tool
trace. Three cases also enter a separate judgement queue for prose evidence.
Their independently produced sidecar verdicts are reported separately from the
deterministic code rate.

## Results

| Backend/model | Descriptor | Code pass | Negative pass | Judgement | Median/worst turns | Input/output tokens | Cost | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Scripted replay | v2 | 58/58 (100.0%) | 42/42 (100.0%) | 3/3 | 2.0 / 4 | 746,400 / 25,440 estimates | US$0.0848 estimate | 0 |
| OpenAI GPT-5.4 live | v1 | 20/58 (34.5%) | 20/42 (47.6%) | 0/3 | 2.0 / 3 | 234,496 / 9,653 API-reported | US$0.731035 provider | 28 |
| OpenAI GPT-5.4 live | v2 | 25/58 (43.1%) | 21/42 (50.0%) | 0/3 | 2.0 / 5 | 287,085 / 10,898 API-reported | US$0.881183 provider | 22 |

The same-model descriptor pair changed only the `get_clinic_slots` description.
V2 gained 5/58 passes (+8.6 percentage points) and one negative-trial pass
(+2.4 points), while median turns stayed at 2.0. It also used 53,834 more tokens
and cost US$0.150148 more. Six failed v1 trials passed under v2, while one v1
pass failed under v2. Because the endpoint supplies no reproducible sampling
seed and each arm is one battery, this is an observed association, not a claim
that the descriptor guarantees the measured gain.

## Failure analysis and interpretation

The scripted 100% result validates the harness and labelled paths; it is not
evidence of live-model quality. The dominant live defect was response-format
adherence. V1 had 21 plain-text and seven concatenated/invalid-JSON failures;
v2 had 18 and four respectively. The strict parser escalated safely instead of
executing an unverified booking. Among completed but failed trials, 10 in v1 and
11 in v2 omitted the required test identifier from the named missing item. This
points primarily to step/protocol quality, not a step-cap problem: neither arm
hit the eight-turn cap.

The v2 slot descriptor was longer and more expensive, and it did not address
the separate exact-missing-item weakness. A defensible next iteration would
make one precondition-gathering action mandatory per response at the interface
level and constrain missing-item output to the criterion string returned by the
tool, then rerun a new version on a newly declared freeze. The submitted frozen
results must not be silently patched or selectively retried.

## Team handoff

The current table is a complete GPT-5.4 descriptor experiment, not the complete
multi-model battery. The remaining declared v2 models must use this same freeze,
case list, v2 prompt and trial policy; model ID is the only experimental change.
Only compatible raw result files should feed `analysis/aggregate_live_results.py`.
The selected evidence cases were independently graded with
`google/gemini-2.5-flash-lite` using the committed rubric: scripted passed 3/3,
while v1 and v2 each passed 0/3 because the relevant live runs returned no
evidence-bearing final reasons. The sidecar records source hashes, judge prompt
hash, item verdicts, raw responses, tokens and provider cost.
