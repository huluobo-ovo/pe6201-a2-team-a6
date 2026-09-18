# Controlled Slot-Descriptor Experiment

Owner of the live v1 arm: Fan Yupei

This adapts Wang Chenyu's isolated `get_clinic_slots` experiment to the shared
six-tool interface already merged into the team agent. The comparison changes
only the text shown to the model for `get_clinic_slots`; the Python function,
routing rules, other five descriptors, cases, agent loop, guardrails, approval
policy, model, temperature and output limit remain identical.

## Variable

- `v1`: short baseline that does not explain when the query is legal, the
  required relationship between band and criteria, or the meaning of an empty
  list.
- `v2`: explicit preconditions, argument provenance, bounded return shape and
  failure semantics, including the required `no_slot_in_window` escalation.

Both descriptors describe the same callable signature and result shape. This
keeps the experiment about descriptor quality rather than confounding it with a
different tool implementation or a different number of public tools.

## Frozen controls

Use the same freeze SHA, `openai/gpt-5.4`, 30-case evaluation set, 58-trial
policy, system rules, other descriptors, `temperature=0`, 1,200-token response
cap, explicit fixture-booking approval and OpenRouter route. Run v1 and v2 into
different result files. Do not compare results produced from different commits.

## Commands

```bash
export OPENROUTER_API_KEY="..."

python3 A2_scaffold/run_eval.py \
  --backend live \
  --model openai/gpt-5.4 \
  --descriptor-version v1 \
  --approve-fixture-bookings \
  --price-input-per-million 2.50 \
  --price-output-per-million 15.00 \
  --price-source https://openrouter.ai/openai/gpt-5.4 \
  --price-date 2026-09-15 \
  --freeze-sha COMMIT_SHA
```

Change only `--descriptor-version v1` to `v2` for the paired comparison.

## Frozen result

Both arms ran from clean detached checkouts of
`e36bb1b2fcad625ed944e7df863165d95c0ef53f`. The same model, evaluation
cases, trial policy, prompt rules, callable implementation, price inputs and
response cap were used.

| Measure | v1 | v2 | v2 minus v1 |
|---|---:|---:|---:|
| Code pass | 20/58 (34.5%) | 25/58 (43.1%) | +5 trials; +8.6 pp |
| Negative code pass | 20/42 (47.6%) | 21/42 (50.0%) | +1 trial; +2.4 pp |
| Median turns | 2.0 | 2.0 | 0.0 |
| Worst-case turns | 3 | 5 | +2 |
| API tokens, input/output | 234,496 / 9,653 | 287,085 / 10,898 | +53,834 total |
| Provider-reported cost | US$0.731035 | US$0.881183 | +US$0.150148 |
| Response-error trials | 28 | 22 | -6 |

At trial level, six v1 failures became v2 passes, one v1 pass became a v2
failure, 19 passed in both arms and 32 failed in both. This is evidence that the
v2 descriptor was associated with a better result on this run, not proof that
the descriptor alone guarantees an 8.6-point improvement: the live endpoint
does not expose a reproducible sampling seed and there is only one frozen
battery per arm. The v2 prompt was 654 characters longer, used 22.0% more API
tokens across the battery and cost 20.5% more.
