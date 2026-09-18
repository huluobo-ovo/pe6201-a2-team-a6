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
