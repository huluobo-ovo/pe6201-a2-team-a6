# Contributions

This log records the work visible in the canonical repository history through
`main` commit `66d8a4108aa6eb184405f314af7743d232332ed2`. It distinguishes commits
authored by a member from files delivered off Git and later integrated by
another member. The latter are credited as delivered artifacts, not as authored
Git commits.

## Final contribution record

| Member | Completed contribution | Repository evidence |
|---|---|---|
| Yang Ruijia | Built the D1 ReAct loop and error handling; implemented and measured the D2(c) sequential/grouped calling strategy; recorded live token usage; integrated the final team branches and remaining live-result files; generated the complete independent D4 judgement sidecar; wrote the report-ready D0 argument and reproducible reliability calculation. Ran the Moonshot Kimi K2.6 v2 battery. | Authored commits `a46f1b9`–`84f8799`, `3a3fd94`, `bb0c235`, `d453da9`–`8f799be`, `7053e09`, and `45f59e9`; `analysis/compare_d2c.py`, `artifacts/D2c_dependency_rule.md`, `docs/D0_why_an_agent.md`, `analysis/d0_reliability.py`, `artifacts/judgement_results.json`, and `artifacts/live_results/yang_ruijia_moonshotai_kimi-k2.6_v2.json`. |
| Wang Chenyu | Produced the D2(a) tool-layer and D2(b) descriptor-design input used for the shared six-tool implementation and supplied the Google Gemini 3.7 Flash v2 battery result. The descriptor experiment was adapted to the integrated contract; the original local five-tool prototype was not copied into the final tree. | No Wang-authored commit is visible in the canonical Git history. The off-Git handoff is acknowledged in `artifacts/D2B_CONTROLLED_EXPERIMENT.md` and `artifacts/D4_D5_EVALUATION_README.md`; the delivered live artifact is `artifacts/live_results/wang_chenyu_google_gemini-3.7-flash_v2.json`, integrated by Yang Ruijia in `3a3fd94`. |
| Hao Qi | Implemented D3 guardrails, booking safety and integration tests; built both D7 failure reproductions and the hostile-input guardrail checklist; supplied eight evaluation-case proposals; ran and supplied the Anthropic Claude Sonnet 4.6 v2 battery. | Authored commits `96af6ce`–`cd9ac83`, `0704665`, `660574c`, and `b69f58a`; `A2_scaffold/guardrails.py`, `A2_scaffold/demo_loop_failure.py`, `tests/test_guardrail_cases.py`, `tests/test_guardrails_integration.py`, `artifacts/guardrail_checklist.md`, `artifacts/D7_tool_interface_failure.md`, `evaluation_case_proposals_hao_qi.json`, and `artifacts/live_results/hao_qi_anthropic_claude-sonnet-4.6_v2.json`. |
| Fan Yupei | Built the D4 evaluation set and isolated multi-trial harness; added eight attributed cases and the integration case; produced the reproducible D5(a) scripted result, freeze manifest and independent judgement workflow; coordinated D5(b), ran the GPT-5.4 v1/v2 controlled descriptor experiment, and produced aggregation, defect-analysis, reporting and D6-handoff artifacts. | Authored commits `16afc6f`, `84c60be`, `f6fdf86`–`7492c6d`, `0b40fde`, and `2d7c8c4`; `A2_scaffold/harness.py`, `A2_scaffold/run_eval.py`, `artifacts/results.json`, `artifacts/live_results/fan_yupei_openai_gpt-5.4_v1.json`, `artifacts/live_results/fan_yupei_openai_gpt-5.4_v2.json`, `artifacts/D4_D5_REPORT_READY.md`, and `handoff/fan_yupei/HANDOFF.md`. |
| Liu Xuanlin | Added six labelled D4 evaluation cases; built and finalised the five-model D6 cost-to-serve model, audit ledger, sensitivity analysis, break-even calculation and formatted workbook; ran and supplied the DeepSeek V4 Pro v2 battery. | Authored commits `37549fa`, `db170f1`–`3bcdf82`, `e7c947e`–`938767f`; `analysis/cost_model.py`, `analysis/cost_inputs.csv`, `analysis/cost_summary.csv`, `analysis/model_cost_audit.csv`, `analysis/PE6201_D6_Cost_Model_Final_5Models.xlsx`, and `artifacts/live_results/live_deepseek_v4_v2_liuxuanlin.json`. |

## Evaluation-case status

The frozen 30-case evaluation set contains 15 instructor cases, eight cases
attributed to Fan Yupei, six attributed to Liu Xuanlin, and one D4 integration
case. Yang Ruijia has delivered eight proposals (`REF-6101`–`REF-6108`) outside
the tracked repository, and Hao Qi has eight tracked proposals
(`REF-6301`–`REF-6308`) in `evaluation_case_proposals_hao_qi.json`; neither set
has been converted into the frozen fixtures and labels. No Wang Chenyu
evaluation-case proposal is visible in the canonical repository history. These
proposal files must not be described as executed evaluation cases unless they
are reviewed, integrated and rerun through the harness.

## Live-model status

All five declared v2 live-result files are present and compatible with freeze
`e36bb1b2fcad625ed944e7df863165d95c0ef53f`:

- Yang Ruijia — `moonshotai/kimi-k2.6`
- Wang Chenyu — `google/gemini-3.7-flash`
- Hao Qi — `anthropic/claude-sonnet-4.6`
- Fan Yupei — `openai/gpt-5.4`, plus the required v1 descriptor arm
- Liu Xuanlin — `deepseek/deepseek-v4-pro`

The final report, recorded demonstration and collective team self-appraisal are
team deliverables. They are not credited as completed here because they are not
present in this audited commit.
