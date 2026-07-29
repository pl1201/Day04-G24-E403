---
name: cite
track: bonus
kind: live_api
provider: AlphaXiv API (api.alphaxiv.org)
requires_env: [ALPHAXIV_API_KEY]
inputs: [arxiv_url, style]
outputs: [citation, bibtex, apa, title, authors, year]
side_effect: false
---
# cite

Builds a ready-to-paste citation for a known arXiv paper. Resolves the paper
via `GET /papers/v3/{id}`, returns AlphaXiv's official `citationBibtex`, and
derives an APA string from it (author surnames + initials, year, title,
arXiv id, abs URL).

`style` selects which string lands in `citation`: `bibtex` (default) or
`apa`. Both forms are always returned as `bibtex` and `apa` so the caller
never needs a second round-trip. Author lists longer than 6 names are
truncated with `et al.`

## When to use

- The user asks to cite / reference a paper, or wants a BibTeX entry or an
  APA line for a bibliography.
- A digest needs a proper source reference rather than a bare link.

## When NOT to use

- To find a paper by keyword — use `papers`.
- To read or summarize a paper's content — use `paper_text` (full text) or
  `alphaxiv` (AI overview).

## Notes

Read-only, no confirmation boundary. Requires an arXiv id or URL; a bare
topic string is rejected with a clear error.
