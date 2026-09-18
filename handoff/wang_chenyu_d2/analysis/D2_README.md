# PE6201 A2 — Wang Chenyu D2 final handoff

Owner: 王晨羽 / Wang Chenyu / Jason. Team A-6, Problem B. Scope: D2(a) tools, D2(b) ACI and descriptor comparison, plus the owner's Gemini live evidence. D2(c) remains Yang Ruijia's responsibility.

Integration note: Wang Chenyu supplied this handoff. Yang Ruijia uploaded it
through the `huluobo-ovo` account; the Git committer is not the original author.

## What to integrate

- D2_report_text.md: compact English text for the group report.
- D2_design_and_evidence.md and D2_TOOL_CONTRACTS.md: detailed design, safeguards, six-field contracts and contribution attribution.
- d2_paired_metrics.csv: GPT-5.4 v1/v2 comparison, supported by original results in artifacts. Fan produced the paired runs.
- gemini_live_summary.csv: Jason's genuine Gemini 3.7/OpenRouter result.
- gemini_cost_inputs_for_D6.csv: one row matching Liu Xuanlin's cost_inputs.csv schema; append once, then rerun his cost model. The US$6 fallback, US$150 fixed monthly cost, 1,000 monthly tasks and US$5 manual task values are Liu's scenario assumptions, not measured facts.
- artifacts/wang_chenyu_google_gemini-3.7-flash_v2.json: original raw result for the evaluation owner.
- D2_demo_script_zh.txt: one-minute explanation.

## Reproduce the offline checks

Run `python analysis/verify_d2.py` from the extracted package. Standard library only; no API key or paid request is required. A full paid live rerun requires the original frozen Git checkout and a newly configured credential. The source_reference adapter is the recorded execution script, not a standalone launcher for this folder.

## Remaining evidence limits

Exact tool-return tokens/call have not been measured: tool_return_size_characters.csv counts compact-JSON characters, not model tokens. The three Gemini judgement checks were subsequently completed and scored 0/3; the integrated sidecar is bundled in `artifacts/judgement_results.json`. Deterministic guardrail tests are not the same metric as negative-case live success. Jason's REF-6201–6208 case proposals were not included in the frozen case set; no merged-case credit is claimed. No credentials or quota-failed alternative-model results are included.

The reference Liu_Xuanlin_D6_final.zip was used for packaging conventions and the D6 input schema only; its workbook or four-model totals have not been overwritten.
