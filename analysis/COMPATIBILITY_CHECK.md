# Five-model Final-v2 Compatibility Check

All five D6 base-comparison runs passed the common-control compatibility check.

- freeze_sha: PASS
- source_sha: PASS
- prompt_version: PASS
- prompt_sha256: PASS
- descriptor_version: PASS
- descriptor_sha256: PASS
- tool_version: PASS
- token_measurement: PASS
- case_count: PASS
- negative_case_count: PASS
- case_ids: PASS
- trials: PASS
- trial_policy: PASS
- fixture_approval: PASS
- max_output_tokens: PASS

Common freeze/source SHA: `e36bb1b2fcad625ed944e7df863165d95c0ef53f`  
Common prompt SHA256: `04d0940490d62891c8a8c242344c85dd8dec4a16789fa1e74db336da9c763d6e`  
Common descriptor bundle SHA256: `ca9278e1ba1144a1a0f01042f9e1af51bc37319dae99786311d65b09bdb08733`

Models included:
- openai/gpt-5.4
- moonshotai/kimi-k2.6
- anthropic/claude-sonnet-4.6
- deepseek/deepseek-v4-pro
- google/gemini-3.7-flash

Important: GPT descriptor-v1 is a D2 controlled-experiment artefact and is intentionally excluded from the D6 final-v2 cost comparison. Gemini has 3 judgement cases pending, so its 6/58 figure is a deterministic code-pass rate, not a completed mixed-grader score. D6 consistently uses deterministic code pass/fail to define human fallback.
