# Fan Yupei — Self-Appraisal Evidence Input

Use this evidence when the team completes the official self-appraisal form.
It is not a replacement for that form.

- Owned D4 and D5 on `feature/evaluation`.
- Added eight attributed evaluation cases (`REF-6401`–`REF-6408`) with labels,
  isolated purpose, wrong behaviour caught, required evidence and scripted
  moves.
- Integrated teammate safety and cost/case branches without changing `main` or
  deleting supplied fixture rows.
- Built full-set scripted coverage, outcome/gated-action grading, judgement
  queue, negative 3-trial policy, result schema and compatibility validation.
- Published freeze `e36bb1b2fcad625ed944e7df863165d95c0ef53f` with file,
  prompt and descriptor hashes and reproducible commands.
- Ran the declared `openai/gpt-5.4` descriptor-v1 job and an additional v2
  same-model control from clean detached checkouts; retained every failure and
  API-reported token/cost record.
- Ran three selected evidence checks per result with a named different-family
  judge, storing prompt/source hashes and API measurements in an immutable
  sidecar.
- Aggregated report-ready JSON/CSV/Markdown tables, documented defects and
  prepared the D4/D5 demo runbook.

Evidence files: `CONTRIBUTIONS.md`, `artifacts/freeze_manifest.json`,
`artifacts/results.json`, `artifacts/live_results/`,
`artifacts/live_battery_summary.*`, `artifacts/D4_D5_REPORT_READY.md`, and the
git history on `feature/evaluation`.
