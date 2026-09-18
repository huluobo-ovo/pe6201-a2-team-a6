# PE6201 A2 Team A-6 Problem B Section 3 Evidence

## 3 What the evidence showed

At freeze `e36bb1b2fcad625ed944e7df863165d95c0ef53f`, 30 independently reset Problem B cases were tested: 15 supplied, eight by Fan Yupei, six by Liu Xuanlin and one integration case. Fourteen negatives—where the right outcome is ask or escalate, not book—were retained, transparently exceeding the brief's 6–10 guidance. They target booking despite red flags, named missing tests, specialty mismatch, a duplicate future appointment, no legal in-window slot, or overt/tool-imitating instructions in referral free text. Sixteen ordinary cases ran once and 14 negatives three times: 58 trials per arm.

Each trial was outcome-graded, not path-graded. Deterministic code checks compared decision, canonical trigger, exact missing item or clinic/date/time, and one approved gated booking with its trace. Three selected cases also received an independent judgement check of whether the recorded evidence justified the result, using a separately specified judge model. This kept fluent prose or a lucky slot match from counting as correctness.

The reproducible scripted v2 replay passed 58/58 code checks, including 42/42 negatives, and passed judgement on 3/3 selected cases. This validates the deterministic paths, labels and harness; it does not show that a live model is reliable.

Five compatible v2 models completed the battery. GPT-5.4 led at 25/58 (43.1%) overall and 21/42 (50.0%) negative; Kimi K2.6 followed at 15/58 (25.9%) and 15/42 (35.7%). The others achieved 4–10/58 overall and 4–10/42 negative (Table 2), a 9.5–50.0% negative spread. Price did not buy reliability: Gemini cost US$0.165362 for 6/58 and 49 errors; Claude cost US$0.900006 for 10/58 and 48 errors. Independent judgement was 0/3 for every live arm, so code rates alone overstate evidence.

With model, freeze and contract fixed, changing only the `get_clinic_slots` descriptor raised GPT-5.4 from 20/58 to 25/58 (+8.6 pp) and 20/42 to 21/42 negatives (+2.4 pp); median turns stayed 2.0 and errors fell 28 to 22. V2 cost 53,834 extra API tokens and US$0.150148. Six v1 failures became v2 passes and one reversed; one unseeded battery per arm means association, not guarantee.

**Table 1. Frozen evaluation design and grading.** A negative case has the correct outcome `ask` or `escalate`; code and judgement are separate measures.

| Element | Measured design |
|---|---|
| Isolated evaluation set | 30 independently reset cases: 15 supplied, 8 Fan Yupei, 6 Liu Xuanlin, 1 integration |
| Ordinary cases | 16 cases × 1 trial = 16 trials per arm |
| Negative cases | 14 cases × 3 trials = 42 trials per arm |
| Trial total | 58 trials per scripted or live arm |
| Deterministic code check | Decision; canonical escalation trigger; exact named missing item; exact clinic/date/time; one approved gated booking and matching trace |
| Independent judgement check | 3 selected cases (`REF-6401`, `REF-6405`, `REF-6407`); evidence/reason judged separately by `google/gemini-2.5-flash-lite` |

**Table 2. Frozen battery results.** Live tokens and costs are API-reported; scripted token and cost values are instrumentation estimates, not live measurements. The five v2 rows share the frozen final prompt, case list and trial policy; the GPT-5.4 v1 row is the declared controlled descriptor comparison. All six live rows passed compatibility checks.

| Backend/model | Arm | Code pass | Negative code pass | Judgement | Median/worst turns | Input/output tokens | Provider cost (US$) | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Scripted replay | v2 | 58/58 (100.0%) | 42/42 (100.0%) | 3/3 | 2.0 / 4 | 746,400 / 25,440* | 0.084816* | 0 |
| OpenAI GPT-5.4 | v1 | 20/58 (34.5%) | 20/42 (47.6%) | 0/3 | 2.0 / 3 | 234,496 / 9,653 | 0.731035 | 28 |
| OpenAI GPT-5.4 | v2 | 25/58 (43.1%) | 21/42 (50.0%) | 0/3 | 2.0 / 5 | 287,085 / 10,898 | 0.881183 | 22 |
| Anthropic Claude Sonnet 4.6 | v2 | 10/58 (17.2%) | 10/42 (23.8%) | 0/3 | 1.0 / 2 | 233,897 / 13,221 | 0.900006 | 48 |
| DeepSeek V4 Pro | v2 | 4/58 (6.9%) | 4/42 (9.5%) | 0/3 | 1.0 / 2 | 196,625 / 24,437 | 0.178641 | 50 |
| Google Gemini 3.7 Flash | v2 | 6/58 (10.3%) | 4/42 (9.5%) | 0/3 | 1.0 / 4 | 132,992 / 17,498 | 0.165362 | 49 |
| Moonshot Kimi K2.6 | v2 | 15/58 (25.9%) | 15/42 (35.7%) | 0/3 | 2.0 / 2 | 263,325 / 52,112 | 0.241000 | 31 |

\* Scripted estimate only.

## Team-leader handoff

- Paste the Section 3 prose and both tables exactly; Tables 1 and 2 are excluded from the 350-word prose budget.
- Keep the scripted row labelled as deterministic and estimated, and keep judgement separate from code pass rates. In particular, do not represent 58/58 scripted correctness as live-agent reliability.
- Use the five final-v2 rows and the GPT-5.4 v1 row together: the full battery is complete, with six compatible live result artifacts at the stated freeze. No model-result placeholders remain.
- Before final submission, retain the six raw JSON results, `artifacts/live_battery_summary.*`, `artifacts/results.json`, `artifacts/judgement_results.json` and `artifacts/freeze_manifest.json` from the current team integration. If any raw result changes, rerun the aggregator and replace the whole table rather than editing a row by hand.
- The controlled conclusion is deliberately limited: descriptor v2 was associated with the observed GPT-5.4 gain, but one unseeded battery per arm does not establish a guaranteed improvement.
