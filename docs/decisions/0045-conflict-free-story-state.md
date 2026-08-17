---
status: accepted
confirmed_by: "Ravi Kiran Vemula"
date: 2026-08-14
stories: [FORGE-CFS-1]
---

# Conflict Free Story State

## Context

Every pair of overlapping story PRs conflicts by construction: story evidence
lives in repo-wide singleton files (`.factory/run.json`, `decomposition.json`,
`stages.json`, `tests.json`, `outcome.json`, `verify.json`) that every story
rewrites, `pr_ready`'s archive move (`.factory/*` →
`.factory/history/<story>/`) triggers git rename detection that pairs one
branch's archived copies with the other's live files, and `events.jsonl`
depends on a per-clone union merge driver that reorders lines when it fires.
On PR #104 this compounded: conflict markers in `factory_lib.py` crashed the
PreToolUse hook itself (fail-closed per 0038), disabling the tooling needed
for repair, and the recovered hook had no sanctioned path for resolving
`.factory` merge conflicts (lessons: factory-merge-resolution-needs-a-path,
ledger-directories). Decision 0022 already names the cure for this class:
one record per file removes the conflict rather than resolving it — but it
was applied only to lessons and quickfix windows.

## Decision

Extend 0022 to all recorded story state. Story evidence is written under
`.factory/stories/<KEY>/` from intake onward — recorders, gates, and
`pr_ready` read and write story-scoped paths, so the archive move (and its
rename-detection strands) disappears; `run.json` becomes a derived pointer
to the active story (worktree-local, not merge-contested authority);
`events.jsonl` becomes one event per file like the lessons ledger;
`roadmap.json` remains the single ordered index, with `forge next` running
`roadmap heal` automatically after a merge. The PreToolUse hook gains a
mid-merge carve-out — git-native resolution (`checkout --ours/--theirs`,
`rm`/`add`) is permitted for exactly the unmerged-index paths while content
hand-writes stay refused — and falls back to a minimal static deny-list
instead of crashing when `factory_lib` or `run.json` is unparseable.

## Consequences

- Two story worktrees never write the same evidence paths; overlapping PRs
  stop conflicting on `.factory` by construction.
- Legacy layout needs a migration (existing history/ archives stay put;
  live singletons migrate at the next intake); vendored client repos pick
  the change up via `forge upgrade`.
- The union merge driver dependency for `events.jsonl` is retired.
- Hook behavior during merges is defined instead of accidental: resolution
  is possible, hand-writing still is not.
- Until FORGE-CFS-1 ships, the mitigation stands: merge origin/main into a
  story branch immediately before `pr_ready`, land PRs promptly.
