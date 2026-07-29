---
name: alphaxiv
track: bonus
kind: live_api
provider: AlphaXiv API (api.alphaxiv.org)
requires_env: [ALPHAXIV_API_KEY]
inputs: [arxiv_url, language]
outputs: [title, abstract, ai_overview, url]
side_effect: false
---
# alphaxiv

Given a known arXiv id or URL, resolves the paper on AlphaXiv
(`GET /papers/v3/{id}`) and returns AlphaXiv's AI-generated overview/summary
(`GET /papers/v3/{versionId}/overview/{language}`).

Use when the user already has a specific paper in mind and wants an
AI-written plain-language overview/discussion of it — not for keyword
search (use `papers` for that; AlphaXiv's keyword-search endpoint is
web-session only and rejects API keys) and not for raw full PDF text
(use `paper_text` for that).

Auth: `Authorization: Bearer {ALPHAXIV_API_KEY}`. Read-only, no confirmation
boundary needed.
