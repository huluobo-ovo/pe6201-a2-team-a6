# D5 Live Model Battery

Only rows marked compatible share the frozen commit and exact case list.

| Model | Descriptor | Trials | Code pass | Negative pass | Judgement | Median turns | Tokens in/out | Cost (USD) | Errors | Compatible |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| openai/gpt-5.4 | v1 | 58 | 34.5% | 47.6% | 0/3 | 2.0 | 234496 / 9653 | 0.7310 | 28 | yes |
| openai/gpt-5.4 | v2 | 58 | 43.1% | 50.0% | 0/3 | 2.0 | 287085 / 10898 | 0.8812 | 22 | yes |
| anthropic/claude-sonnet-4.6 | v2 | 58 | 17.2% | 23.8% | - | 1.0 | 233897 / 13221 | 0.9000 | 48 | yes |
| deepseek/deepseek-v4-pro | v2 | 58 | 6.9% | 9.5% | - | 1.0 | 196625 / 24437 | 0.2136 | 50 | yes |
| google/gemini-3.7-flash | v2 | 58 | 10.3% | 9.5% | - | 1.0 | 132992 / 17498 | 0.1654 | 49 | yes |
| moonshotai/kimi-k2.6 | v2 | 58 | 25.9% | 35.7% | - | 2.0 | 263325 / 52112 | 0.3299 | 31 | yes |

## Paired v1/v2 deltas

| Model | Pass-rate delta | Negative delta | Median-turn delta | Token delta | Cost delta (USD) |
|---|---:|---:|---:|---:|---:|
| openai/gpt-5.4 | +8.6 pp | +2.4 pp | +0.0 | +53834 | +0.1501 |
