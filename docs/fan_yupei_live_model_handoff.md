# Fan Yupei Live Model Handoff

This is the frozen OpenAI GPT-5.4 prompt-v2 result for Liu Xuanlin's D6 cost
ledger. It reports measured API token usage and trial-derived evaluation
outcomes only; it does not perform or replace Liu's cost, sensitivity, or
break-even analysis.

| Field | Value |
| --- | --- |
| Owner | Fan Yupei |
| Model | OpenAI GPT-5.4 |
| Exact model ID | `openai/gpt-5.4` |
| Freeze/reproducible commit | `e36bb1b2fcad625ed944e7df863165d95c0ef53f` |
| Results file | `artifacts/fan_yupei_live_handoff.json` |
| Canonical raw result | `artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json` |
| Total trials | 58 |
| Successful trials | 25 |
| Failed trials | 33 |
| Success rate | 25/58 = 43.1034482759% |
| Total input tokens | 287,085 |
| Total output tokens | 10,898 |
| Total tokens | 297,983 |
| Fallback count | 33 |
| Fallback rate | 33/58 = 56.8965517241% |
| Final run completed | 2026-09-14 19:16:20 UTC / 2026-09-15 03:16:20 SGT |
| Required environment variable | `OPENROUTER_API_KEY` |
| Runtime | Python 3, standard library only; audited with Python 3.14.6 |

## Exact reproducibility command

Run from the repository root at the frozen commit in a clean checkout. The API
key must exist in the environment; never place its value in the command, source,
or result file.

```bash
python3 A2_scaffold/run_eval.py \
  --backend live \
  --model openai/gpt-5.4 \
  --descriptor-version v2 \
  --approve-fixture-bookings \
  --price-input-per-million 2.50 \
  --price-output-per-million 15.00 \
  --price-source https://openrouter.ai/openai/gpt-5.4 \
  --price-date 2026-09-15 \
  --freeze-sha e36bb1b2fcad625ed944e7df863165d95c0ef53f \
  --output artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json
```

The frozen JSON did not preserve the literal shell history. The command above
is the exact reproducibility command reconstructed from its recorded run
metadata and the committed freeze manifest, with the canonical output path made
explicit.

## Cases and trial protocol

The run used all 30 frozen Problem B cases listed in
`artifacts/freeze_manifest.json`. Ordinary cases ran once and the 14 negative
cases ran three times, for 58 total trials. Fan Yupei's eight contributed cases
are `REF-6401` through `REF-6408`; their labels and purposes are documented in
`artifacts/yupei_evaluation_cases.md`.

Relevant configuration and code paths:

- `A2_scaffold/config.py`
- `A2_scaffold/run_eval.py`
- `A2_scaffold/harness.py`
- `A2_scaffold/backends.py`
- `A2_scaffold/prompt.py`
- `A2_reference_data/expected_outcomes_B.json`
- `artifacts/freeze_manifest.json`

## Audit and fallback definition

The canonical raw result is immutable. `artifacts/fan_yupei_live_handoff.json`
is a compact generated sidecar containing `handoff_summary`, the raw source
path and hash, and 58 flattened `audit_trials`. Each audit row contains the
case and trial IDs, exact requested model ID, success, failure reasons, derived
fallback flag, API input/output/total tokens, latency, turns, stop reason, and
backend error.

For D6 only, a failed deterministic code-check trial is treated as requiring
human fallback: `fallback_used = not passed`. Therefore fallback count is 33 and
fallback rate is 33/58. This is the assignment's escalation-on-failure cost
convention, not a separate provider field or observed fallback tool call.

The frozen runner recorded the exact configured/requested OpenRouter route as
`openai/gpt-5.4`, but it did not persist the response-side provider model field.
The current runner now records both requested and provider-returned model IDs for
future live runs. No provider-resolved historical ID is invented here.

Regenerate and verify the handoff view with:

```bash
python3 analysis/build_fan_yupei_live_handoff.py
python3 analysis/build_fan_yupei_live_handoff.py --check
```

The live experiment's legitimate freeze commit is
`e36bb1b2fcad625ed944e7df863165d95c0ef53f`. Later commits package, document,
and validate that immutable evidence; they are not replacement experimental
freeze commits. Use `git rev-parse HEAD` to identify the current packaging
checkout.
