---
name: dedupe
track: bonus
kind: local
provider: none (pure local logic)
requires_env: []
inputs: [items, merge_fields]
outputs: [items, input_count, item_count, removed_count, duplicates]
side_effect: false
---
# dedupe

Removes duplicate research items from a list the agent has **already
collected**, before handing them to `format`.

Two items are duplicates when their URLs match after normalization
(scheme/`www.`/query string/fragment/trailing slash stripped) or when their
titles match after folding accents, case and punctuation. The first
occurrence is kept and its order preserved; with `merge_fields=true`
(default) any field that is empty on the kept copy is filled in from the
duplicate, so a summary that only the later copy had is not lost.

## When to use

- After merging results from several sources (`lookup` + `social_search` +
  `papers` + `related`), which routinely surface the same article twice.
- Before `format`, so the digest does not repeat an item.

## When NOT to use

- To fetch or search anything — this tool never makes a network call and
  cannot discover new items.
- On a single-source result list that has not been merged; there is nothing
  to deduplicate.

## Notes

No API key, no quota, no side effects. Non-dict entries in `items` are
skipped and reported in `ignored_count` instead of raising.
