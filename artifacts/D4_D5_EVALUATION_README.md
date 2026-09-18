# D4 and D5 Evaluation Handoff

Owner: Fan Yupei
Branch: `feature/evaluation`

## Completed on this branch

- Added eight labelled Problem B cases, `REF-6401` to `REF-6408`, through the
  fixture generator rather than by editing generated data.
- Preserved every shipped row. The integrated set contains 30 referrals and 30
  labels: 15 shipped, Fan Yupei's eight, Liu Xuanlin's six, and one explicitly
  labelled D4-owner integration case.
- Added deterministic scripted replays for every current Problem B fixture.
  Replay construction reads fixture records and the Appendix A routing order;
  it never reads `expected_outcomes_B.json`.
- Extended the code check to validate the decision, escalation trigger, named
  missing item, exact booked slot, gated-action count and gate result.
- Limited judgement checks to selected prose-evidence cases, kept the raw queue
  separate from the code pass rate, and stored named different-family verdicts
  in a source-hashed sidecar.
- Added an auditable result schema with commit SHA, prompt and descriptor hashes,
  branch, backend, model id, prompt/tool/descriptor versions, trial policy,
  API-reported token source, price provenance, errors, negative-only performance
  and per-case results.
- Made the committed default run the entire submitted set and fail loudly if a
  case has no scripted replay.

## Current reproducible run

From the repository root:

```bash
python3 A2_reference_data/check_my_data.py
python3 -m unittest discover -s tests -v
python3 A2_scaffold/run_eval.py
```

Integrated freeze-set shape:

| Measure | Value |
|---|---:|
| Cases | 30 |
| Negative cases | 14 |
| Ordinary trials | 16 |
| Negative trials | 42 |
| Total trials | 58 |
| Selected judgement cases | 3 |

Scripted token counts are estimates used only to test instrumentation. They are
explicitly labelled and must not be reported as live measurements.

## Result schema

`artifacts/results.json` contains:

- `run`: freeze/source commit, branch, backend, model, prompt/tool versions,
  token source and the trial policy;
- `evaluation_set`: all case ids and the negative subset;
- `summary`: overall and negative-only code pass rates, trial counts, turns,
  tokens, cost, cap hits and errors;
- `case_results`: one compact row per case, including check type;
- `trial_results`: full decision records and traces;
- `judgement_queue`: only cases selected for human or independent-model review.

The raw result keeps judgement fields null so the measured run is immutable;
completed verdicts live in `artifacts/judgement_results.json` and remain a
separate measure from code pass rate.

The D6-facing file `artifacts/fan_yupei_live_handoff.json` is generated from the
canonical raw v2 result. It records the raw source path and hash, a derived
summary, and one flattened audit row per trial. For this handoff,
`fallback_used` means a
trial failed the deterministic code check and therefore requires human fallback
under D6's escalation-on-failure convention. It is not a provider field or a
separate tool call. Regenerate or validate it with
`analysis/build_fan_yupei_live_handoff.py`.

The raw paid measurements are separate under
`artifacts/live_results/`; `analysis/aggregate_live_results.py` rejects a row
unless the freeze/source SHA, clean-tree flag, exact case list and counts,
trial policy, prompt/descriptor hashes, API token source, approval record and
price provenance all match the manifest. It also verifies that any independent
judgement sidecar names the exact SHA-256 of the source result file.

## Freeze and live-battery procedure

1. Check out the frozen `feature/evaluation` SHA from
   `artifacts/freeze_manifest.json` in a clean clone.
2. Run the checker and tests. Confirm the set has 30-50 cases, every label is
   present, and every new case has a scripted replay.
3. Freeze a side-branch commit. Every runner checks out that exact SHA; only the
   model id or the controlled descriptor version may differ.
4. Four members of this five-person team run the final v2 prompt on four model
   families spanning at least two price tiers. The fifth job is the controlled
   v1 descriptor pass on the same model used by one v2 result.
5. Each runner uses an explicit model id and output filename:

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

6. Commit each result JSON without changing source files, then run
   `python3 analysis/aggregate_live_results.py` to validate and aggregate the
   per-model and negative-only tables.

## Controlled descriptor experiment

Wang Chenyu's experiment design was adapted to the shared six-tool contract. The
only v1/v2 variable is the text of the `get_clinic_slots` descriptor; the callable
and every other frozen control remain identical. See
`artifacts/D2B_CONTROLLED_EXPERIMENT.md`.

The timeline assigns member 4 the descriptor-v1 job. A matching GPT-5.4 v2
control was also run from the same clean freeze, so the descriptor comparison is
available now. The integrated team set contains 14 negatives because Liu's four
negative cases were preserved; this exceeds the brief's recommended 6-10 range
and is reported rather than hidden.

## Frozen measurements currently available

| Run | Overall code pass | Negative code pass | Judgement pass | Median turns | API tokens in/out | Provider cost | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| Scripted v2 | 58/58 (100.0%) | 42/42 (100.0%) | 3/3 | 2.0 | estimates only | estimate only | 0 |
| GPT-5.4 v1 descriptor | 20/58 (34.5%) | 20/42 (47.6%) | 0/3 | 2.0 | 234,496 / 9,653 | US$0.731035 | 28 |
| GPT-5.4 v2 descriptor | 25/58 (43.1%) | 21/42 (50.0%) | 0/3 | 2.0 | 287,085 / 10,898 | US$0.881183 | 22 |

The team-level D5 battery is not complete until the remaining declared v2
model results are placed in `artifacts/live_results/` and pass the aggregator's
compatibility checks. Raw result queues retain their original null verdicts;
the completed, named judgements are in `artifacts/judgement_results.json`.
