---
name: related
track: bonus
kind: live_api
provider: AlphaXiv API (api.alphaxiv.org)
requires_env: [ALPHAXIV_API_KEY]
inputs: [arxiv_url, max_results]
outputs: [items, item_count, total_available]
side_effect: false
---
# related

Given one known arXiv paper, returns other papers AlphaXiv considers similar
(`GET /papers/v3/{id}/similar-papers`) — the "what else should I read"
step of a literature review.

Each item follows the same shape the other research tools emit
(`title`, `summary`, `url`, `date`, `source`) plus `arxiv_id`, `authors` and
`topics`, so results can be piped straight into `dedupe` and `format`.
Summaries prefer AlphaXiv's AI paper summary and fall back to the abstract,
trimmed to 400 characters.

`max_results` is clamped to 1–10; `total_available` reports how many the API
actually returned so the caller knows the list was truncated.

## When to use

- The user already has a paper and wants related / similar / follow-up work.
- Expanding a reading list outward from one seed paper.

## When NOT to use

- Searching by keyword or topic with no seed paper — use `papers`.
- Summarizing the seed paper itself — use `alphaxiv` or `paper_text`.

## Notes

Read-only, no confirmation boundary. Needs an arXiv id or URL as the seed.
