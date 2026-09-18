# D2 / Gemini live compatibility

Gemini v2 and the GPT v2 reference agree on problem B, live backend, prompt v2, descriptor v2, main-tool-contract, exact ordered 30-case set, 14 negative cases, ordinary=1 / negative=3 trial policy, API-reported tokens, fixture approval, 1,200 output cap, and freeze/source SHA e36bb1b2fcad625ed944e7df863165d95c0ef53f. Prompt and descriptor SHA256 values were compared directly; source was clean before the run.

Gemini uses google/gemini-3.7-flash via the original OpenRouter endpoint. The external adapter records raw responses and checkpoints without changing prompts, grading, parsing or token-accounting semantics. Model and prices intentionally differ. Reasoning settings were not additionally overridden, and provider defaults may differ across models.

GPT descriptor-v1 belongs only to the controlled D2 comparison. It has the same model and common source controls as GPT descriptor-v2 but deliberately different descriptor/prompt-content fingerprints. Do not mix the v1 result into D6's final-v2 model table.

The earlier DeepSeek Flash run and direct-Google Gemini 3.5 quota-failure batch are not bundled here. Jason's three Gemini independent judgement cases were subsequently completed and scored 0/3. Code pass and judgement remain separate measures.
