# D4/D5 Demo Runbook

## 1. Prove fixture integrity and coverage

```bash
python3 A2_reference_data/check_my_data.py
python3 -m unittest discover -s tests -v
```

Show the 30 referrals, the unchanged shipped-row fingerprints and the test that
every case has a label and scripted replay.

## 2. Show one ordinary case and one negative case

```bash
python3 A2_scaffold/run_eval.py REF-6401
python3 A2_scaffold/run_eval.py REF-5703
```

For the booking, point out the matching `book_slot`, `gate_passed` event and
exact slot check. For the hostile-text case, point out that no slot query or
booking occurs.

## 3. Reproduce the complete scripted run

```bash
python3 A2_scaffold/run_eval.py \
  --freeze-sha e36bb1b2fcad625ed944e7df863165d95c0ef53f
```

Show 30 cases, 58 trials, the negative-only line, turns, errors and the separate
judgement queue. State explicitly that scripted tokens are estimates.

## 4. Demonstrate the controlled descriptor variable

```bash
python3 A2_scaffold/run_eval.py --prompt --descriptor-version v1
python3 A2_scaffold/run_eval.py --prompt --descriptor-version v2
```

Diff the prompts and show that only `get_clinic_slots` changes. Then open the
freeze manifest and live result; identify the matching SHA, model, descriptor,
API-reported tokens, price provenance and error count.

## 5. Present the measured result and defect

Open `artifacts/live_battery_summary.md`. State the denominators first: v1
passed 20/58 (34.5%) and v2 passed 25/58 (43.1%); negative-only results were
20/42 and 21/42. Median turns stayed at 2.0, while v2 used 53,834 more tokens
and cost US$0.150148 more.

Then show one failed raw trace from the result JSON without changing or
retrying it. The dominant failure was protocol adherence: the model returned
plain prose or concatenated JSON, so the strict parser stopped safely. Close by
noting that the other four declared v2 model files are required before the team
can claim a complete multi-family battery.

Open `artifacts/judgement_results.json` to show that the grading prompt, exact
source file hashes, judge identity and API usage are recorded separately. The
scripted evidence passed 3/3 judgement checks; both live arms passed 0/3 because
their selected cases stopped without evidence-bearing final reasons.
