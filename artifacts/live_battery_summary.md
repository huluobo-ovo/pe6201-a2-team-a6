# D5 Live Model Battery

Only rows marked compatible share the frozen commit and exact case list.

| Model | Descriptor | Trials | Code pass | Negative pass | Judgement | Median turns | Tokens in/out | Cost (USD) | Errors | Compatible |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| openai/gpt-5.4 | v1 | 58 | 34.5% | 47.6% | 0/3 | 2.0 | 234496 / 9653 | 0.7310 | 28 | yes |
| openai/gpt-5.4 | v2 | 58 | 43.1% | 50.0% | 0/3 | 2.0 | 287085 / 10898 | 0.8812 | 22 | yes |

## Paired v1/v2 deltas

| Model | Pass-rate delta | Negative delta | Median-turn delta | Token delta | Cost delta (USD) |
|---|---:|---:|---:|---:|---:|
| openai/gpt-5.4 | +8.6 pp | +2.4 pp | +0.0 | +53834 | +0.1501 |
