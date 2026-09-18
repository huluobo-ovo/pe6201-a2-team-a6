# PE6201 A2 Team A-6 Problem B

This repository implements the outpatient referral coordination agent and its
reproducible evidence. The committed default is offline and deterministic.

## Reproduce the scripted evaluation

```bash
python3 A2_reference_data/check_my_data.py
python3 -m unittest discover -s tests -v
python3 A2_scaffold/run_eval.py
```

The final command evaluates every submitted Problem B fixture. Ordinary cases
run once and negative cases run three times. It writes
`artifacts/results.json`, including the source commit, case and trial
counts, code-check pass rates, negative-only results, turns, tokens, costs,
errors, per-case rows, and the separate judgement queue.

The current reviewed set contains 50 cases. Twenty team-owned proposals were
integrated after validation: eight from Yang Ruijia, seven from Wang Chenyu and
five from Hao Qi. Four additional proposals remain documented but unexecuted so
the set does not exceed the assignment's 50-case maximum. See
`artifacts/team_case_integration_summary.md`. To regenerate the expanded data
and labels from the committed proposal sources:

```bash
python3 A2_reference_data/make_fixtures_B.py
python3 A2_reference_data/check_my_data.py
```

The committed live-model files were produced on the earlier 30-case freeze.
They remain immutable historical evidence and must not be described as covering
the expanded 50-case set. A new compatible D5(b) battery requires every model to
run against the new freeze and exact 50-case list.

The expanded-set baseline is recorded separately in
`artifacts/expanded_50_case_freeze_manifest.json` and
`artifacts/expanded_50_case_results.json`: all 90 scripted trials pass, while
the three prose-evidence judgement items remain pending. These files do not
replace the required five-model live battery.

## Which result file to use

| Purpose | File |
| --- | --- |
| Current expanded 50-case scripted result, D5(a) | `artifacts/expanded_50_case_results.json` |
| Historical 30-case scripted result | `artifacts/results.json` |
| Fan Yupei final GPT-5.4 live result, D5(b) | `artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json` |
| Controlled descriptor-v1 baseline, D2(b) | `artifacts/live_results/fan_yupei_openai_gpt-5.4_v1.json` |
| Liu Xuanlin D6 input and per-trial fallback audit | `artifacts/fan_yupei_live_handoff.json` and `artifacts/live_cost_handoff.csv` |

`artifacts/results.json` is now the only file named `results.json` in the
repository. These files have different purposes and should not replace one
another. The scripted token values are estimates; only the two live files
contain measured API usage.

Report-ready model aggregation is under `artifacts/live_battery_summary.*`.
Independent prose-evidence verdicts are in
`artifacts/judgement_results.json`, keeping the frozen raw runs immutable.

The report-ready D0 argument is in `docs/D0_why_an_agent.md`. Its reliability
arithmetic is reproducible from the frozen GPT-5.4 v2 live result:

```bash
python3 analysis/d0_reliability.py
```

The command writes `artifacts/d0_reliability.json`, including `P`, median `T`,
implied `s = P^(1/T)`, turn-count projections and the failed-trace diagnostic.

Fan Yupei's final live-model handoff for the D6 owner is documented in
`docs/fan_yupei_live_model_handoff.md`. Its machine-readable
`artifacts/fan_yupei_live_handoff.json` is generated from the immutable raw v2
result and adds trial-derived fallback fields plus a flattened per-trial audit
view:

```bash
python3 analysis/build_fan_yupei_live_handoff.py --check
```

To inspect one case and every tool call:

```bash
python3 A2_scaffold/run_eval.py REF-6401
```

To inspect either controlled descriptor prompt without spending credit:

```bash
python3 A2_scaffold/run_eval.py --prompt --descriptor-version v1
python3 A2_scaffold/run_eval.py --prompt --descriptor-version v2
```

Live evaluation is opt-in and requires an explicit OpenRouter model id:

```bash
export OPENROUTER_API_KEY="..."
python3 A2_scaffold/run_eval.py \
  --backend live \
  --model PROVIDER/MODEL \
  --descriptor-version v1 \
  --approve-fixture-bookings \
  --price-input-per-million PRICE \
  --price-output-per-million PRICE \
  --price-source SOURCE \
  --price-date YYYY-MM-DD \
  --freeze-sha COMMIT_SHA \
  --output artifacts/live_results/MEMBER_MODEL_v1.json
```

Do not run a live battery until the prompt, tool contract, evaluation set and
freeze commit are agreed. This branch used freeze
`e36bb1b2fcad625ed944e7df863165d95c0ef53f`. See
`artifacts/D4_D5_EVALUATION_README.md` for the handoff, validation rules and
result schema.
