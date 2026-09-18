# D2 — Tool Set and Agent–Computer Interface
Wang Chenyu (Jason) · Team A-6 · PE6201 A2 · Problem B

## D2(a): tool design and scope

The frozen outpatient-referral agent exposes six tools. It retrieves evidence progressively rather than placing the entire reference dataset in the initial prompt. The model decides the routing outcome from the returned facts; booking is checked again by executable validation and an approval gate.

| Tool | Role and design rationale | Main boundary |
|---|---|---|
| `get_referral(referral_id)` | Retrieves the referral, including patient ID, specialty, attached tests and clinical summary. This establishes the identifiers needed by subsequent lookups. | Must precede dependent lookups; an unknown ID is a broken case, not a routing outcome. |
| `lookup_patient(patient_id)` | Returns patient history and contact details together, avoiding a separate contact lookup. | A duplicate requires a future appointment in the same specialty; a past appointment is not a duplicate. |
| `check_referral_criteria(specialty, referral_id)` | Returns red-flag evidence, department match, missing mandatory tests, urgency band and window length in one response. | These facts support ordered routing checks; the tool does not book or issue a final decision. |
| `as_of()` | Supplies the common fixture date used for future-appointment checks and urgency windows. | Use this date rather than the referral receipt date or the computer clock. |
| `get_clinic_slots(specialty, band, from, to)` | Filters by specialty, urgency band, date window and positive capacity. | An empty list requires `no_slot_in_window` escalation; it does not authorize changing the band or widening the window. |
| `book_slot(clinic, date, time, referral_id)` | Validates the proposed appointment and returns a booking confirmation. | This is the gated action. In the scaffold it returns a fixture confirmation, not a real appointment. |

Combining patient and contact retrieval reduces unnecessary lookup steps. Combining protocol facts avoids repeated retrieval of the same referral and specialty data, although it couples several checks into one tool. Keeping slot search separate from booking allows evidence gathering without committing an action. Keeping `as_of` explicit makes the time basis inspectable. The integrated design retains six tools; an earlier local five-tool prototype was not the final team interface.

All six descriptors are included in the system prompt even when a particular tool is not called. The prompt is sent again on subsequent model requests, so unused tool descriptions still contribute to input-token usage. Tool count alone is therefore an incomplete cost metric: descriptor length, returned observations and the number of model requests also matter.

## Two implemented error-prevention mechanisms

1. **Mandatory urgency band and filtered slot results.** `get_clinic_slots` requires `band` and filters out wrong-band, out-of-window and full slots. For the routine referral REF-5602, earlier urgent or soon slots must not be selected merely because they occur sooner. Requiring the argument prevents omission; it does not prevent a model supplying the wrong band. That remaining risk is addressed by booking validation.
2. **Booking validation against source records.** `validate_booking_slot` recomputes the referral criteria and window, rejects red flags, department mismatches, missing mandatory tests and future same-specialty duplicates, and verifies the proposed clinic/date/time against eligible slots. The guardrail layer also checks that the referral matches the current case and that a final booking claim has a matching successful gated action. This prevents fabricated confirmations and invalid slot selection from being accepted merely because the model says “book”.

These are properties of the integrated frozen system. Jason's contribution is the tool/ACI design and isolated descriptor-experiment proposal; the team's integration and guardrail implementation should retain their existing attribution.

## D2(b): controlled descriptor comparison

The experiment changes only the `get_clinic_slots` descriptor. The v1 description omits important calling preconditions, argument provenance and empty-result semantics. The v2 description states when slot lookup is legal, requires the band supplied by `check_referral_criteria`, and directs the agent to escalate with `no_slot_in_window` when the result is empty. The function signature, returned schema and the other five descriptors remain unchanged. Exact six-field contracts (`name`, `purpose`, `when`, `args`, `returns`, `failure`) are supplied in the appendix.

Both live arms use `openai/gpt-5.4` at freeze `e36bb1b2fcad625ed944e7df863165d95c0ef53f`, with 30 cases and 58 trials (16 ordinary trials plus 14 negative cases repeated three times). Temperature is 0, the response cap is 1,200 tokens, the turn cap is 8, the per-run token ceiling is 60,000, and autonomy is `confirm` with explicit fixture-booking approval. Both records use prompt version v2; descriptor versions v1 and v2 identify the experimental arms. The live evidence was produced by Fan Yupei and is analysed here for Jason's D2 section; it is not represented as Jason's own model run.

| Measure | Descriptor v1 | Descriptor v2 | Observed change |
|---|---:|---:|---:|
| Code-check passes | 20/58 (34.48%) | 25/58 (43.10%) | +8.62 percentage points |
| Negative code-check passes | 20/42 (47.62%) | 21/42 (50.00%) | +2.38 percentage points |
| API input tokens | 234,496 | 287,085 | +52,589 |
| API output tokens | 9,653 | 10,898 | +1,245 |
| Total API tokens | 244,149 | 297,983 | +22.05% |
| Median turns | 2 | 2 | Unchanged |
| Worst-case turns | 3 | 5 | +2 |
| Error trials | 28 | 22 | −6 |
| Recorded baseline cost (USD) | 0.731030 | 0.881178 | +20.54% |
| Separate evidence judgement | 0/3 | 0/3 | No improvement |

The descriptor rewrite improved observed code-check performance at higher token expenditure and cost. It did not demonstrate cost savings. The full system prompt increased from 5,422 to 6,076 characters (+12.06%); these are character counts, not tokenizer measurements. The unchanged median turn count does not mean all trajectories were unchanged, as the worst-case count increased. Repeated negative trials are not independent unique cases, and this small comparison does not establish statistical significance or a general model ranking. The separate judgement scores must not be combined informally with the 58-trial code-check rate.

## Guardrail and return-size evidence

The frozen `test_guardrail_cases.py` battery was rerun locally during this handoff: **15/15 tests passed**. The full frozen suite had also passed 45/45 tests during environment preparation. These are deterministic code checks, not live model guardrail-pass rates. Because descriptor changes do not alter guardrail code, this battery validates the shared implementation rather than proving a difference between the two live arms. Negative live passes are reported separately above and should not be relabelled as a dedicated guardrail score.

The raw result files report aggregate API input/output tokens and tool observations, but do not isolate the tokenizer charge for each tool return. Therefore **exact tokens returned per tool call remain unmeasured**. The companion return-size CSV reports mean/min/max compact-JSON characters per successful tool call as a clearly labelled size diagnostic, not API tokens. Model completion tokens are not a substitute for tool-return tokens. The descriptor experiment keeps the return schema unchanged; actual return sizes can still differ because the model chooses different calls. A tokenizer-specific follow-up is required if the final rubric needs per-call return tokens.

## Contribution and integration statement

Wang Chenyu proposed the isolated slot-tool/ACI experiment, developed earlier local tool prototypes and submitted REF-6201–REF-6208 case proposals. The team adapted the descriptor experiment to the final six-tool interface, as recorded in `D2B_CONTROLLED_EXPERIMENT.md`. The 620x proposals are not present in the frozen 30-case set and are not claimed as merged cases. The paired live runs are attributed to Fan Yupei; D2(c) orchestration remains with Yang Ruijia and D3 guardrails with Hao Qi.

## Completed individual live battery

Jason completed the assigned `google/gemini-3.7-flash` model through OpenRouter on the common freeze, prompt v2 and descriptor v2. It passed 6/58 code checks (10.34%) and 4/42 negative trials (9.52%). API-reported usage was 132,992 input and 17,498 output tokens. There were 49 error trials: 47 strict-JSON parsing failures and two empty assistant responses; no HTTP quota or service failures occurred in this batch. The three separate judgement cases were subsequently completed and scored 0/3. The result therefore describes this model–harness combination and is not a general model-quality ranking.

The exact price-book calculation is US$0.1653615, which matches the summed provider-reported cost. The harness summary reports US$0.165363 because it sums trial costs rounded to six decimals. Keep these fields separate. No selective retry was performed. Earlier direct-Google quota-limited attempts and the separate DeepSeek run are excluded from this package.

## Evidence and reproduction

`artifacts/` contains original live results, API responses, checkpoints, descriptor variants, experiment attribution, available paired judgement evidence and the guardrail-test log. `source_reference/` contains frozen source extracts and the actual external run adapter for audit; it is not a standalone source checkout. Use the team's common Git freeze to reproduce the application. `analysis/verify_d2.py` verifies bundled result totals and regenerates the two-arm metrics CSV offline. `analysis/D2_README.md` describes limitations and integration steps. No credential is included.
