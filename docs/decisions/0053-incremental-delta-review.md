---
status: proposed
confirmed_by: ""
date: 2026-09-09
stories: []
---

# Incremental delta review with an accumulated coverage chain

## Context

Decision 0049 gives each task ONE three-lens autoreview pass over its committed
diff, recorded as the task's proof; intermediate fix iterations re-run it until
clean. The close gate (`require_coherent_review_run`) binds the three lens
artifacts to one `review_run_id` = `sha256(brief_sha256 + branch_diff_digest)`
and requires that `branch_diff_digest` to equal the CURRENT committed product
diff. Because `branch_diff_digest` is a whole-branch hash, every fix commit
changes it, so each re-review re-runs all three lenses over the WHOLE task diff
again — even when the fix touched a few lines.

Observed on `platform-base / frontend-shell-login`: closing one stage took 5+
full three-lens rounds over ~3 hours while the code was already reviewed clean;
the cost was dominated by the number of rounds, each a full-diff pass. #3 fixed
the related stamp re-seal churn; this addresses the review passes themselves.

## Decision

`forge review <task>` reviews, by default, only the DELTA since the last
cleanly-reviewed tip, across all three lenses, and accumulates a `coverage`
chain on each lens artifact:

- The first review (no prior clean coverage) reviews the whole task diff and
  records one segment `{from: task_base, to: HEAD}` on each lens.
- After fixes are committed, `forge review` reviews only `last_clean_tip..HEAD`
  (all three lenses) and, when the round comes back clean for all three,
  appends `{from: last_clean_tip, to: HEAD}`. An unclean round records its
  findings but does not advance coverage.
- `--full` forces a whole-diff review again; `--lens <x>` re-runs a single lens
  for iteration and never advances the shared chain.

The per-round coherence check is UNCHANGED: the latest artifacts still bind to
the current whole-branch digest, so a round is still one coherent three-lens
pass at HEAD. A new close-gate check proves the WHOLE diff was reviewed across
rounds: the three lenses' coverage chains must be identical, contiguous, end at
HEAD, and leave no product change before the first reviewed segment. Coverage is
additive — an artifact without it is a single full-diff review (legacy) and the
gate behaves exactly as before.

## Why this preserves the guarantee

The recorded proof still certifies that every committed product change was
reviewed by all three lenses. It splits that review across contiguous segments
instead of re-reading unchanged code every round: segment 1 covers
`base..T1`, segment 2 covers `T1..T2`, and so on, so their union is `base..HEAD`
for each lens. Each delta pass runs in the full current tree, so cross-file
effects of the delta are still visible to the reviewer. What it deliberately
does NOT do is re-read code that has not changed since it was last reviewed
clean — the same thing an incremental human review skips.

## Consequences

- Re-review after a fix is proportional to the fix, not the whole task diff.
- `reviews/{quality,performance,security}.json` gain an optional `coverage`
  array (`factory/schemas/review.json`); `require_coherent_review_run` gains a
  coverage check (`_review_coverage_problems`).
- The three lenses must advance together; a single-lens run is an iteration aid,
  not a sealable proof.
- Legacy proofs (no coverage) and hand-crafted full reviews are unaffected.
- Does not reintroduce nested reviewers or change what the three lenses check
  (0011, 0049); it changes only how much diff each round re-reads.
