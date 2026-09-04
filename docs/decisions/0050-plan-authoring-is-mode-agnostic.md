---
status: accepted
confirmed_by: "Nandu"
date: 2026-09-03
stories: [upgrade-preserves-doc-contracts]
---

# Plan authoring is mode-agnostic; the grill is the provenance

## Context
<!-- Why this decision was needed; the forces at play. -->

Decision 0048 required a **plan-mode marker** before a plan or task plan could
be saved or approved: the `post_tool_use` hook records a marker whenever a
Claude session writes a plan file while in plan mode, and
`require_plan_mode_marker` refused the save or approve unless a marker's
`sha256_body` matched the plan body exactly.

The intent was provenance — evidence that a plan was authored deliberately
rather than produced in passing. It does not deliver that, and it costs
something real:

- **It dictates the operator's session mode.** Someone working in auto mode is
  pushed into plan mode purely to get a file written, then pushed back. The
  harness has no business deciding which mode an editor is in.
- **It is trivially satisfiable, so it proves nothing.** Entering plan mode and
  touching the file produces a marker. The marker attests to a mode, not to
  thought.
- **It is redundant.** The real provenance is stronger and already enforced:
  the task grill is bound to the plan's exact digest, requires a floor of
  recorded `AskUserQuestion` rounds that only the hook can write, and must be
  fresh — recorded against the current plan text — before the board will show
  the plan. A plan that survives that has demonstrably been examined.
- **Its digest is fragile across platforms.** `plan_body_digest` exists only so
  that a marker written on Windows still matches a plan checked out under
  `core.autocrlf` — complexity nothing else needs.

## Decision
<!-- What was decided, in one or two sentences. -->

**Plan authoring is mode-agnostic.** The plan-mode marker is no longer required
to save or approve a plan or task plan; `require_plan_mode_marker` and its four
call sites in `plans.py` and `tasks.py` are removed. This replaces 0048's
plan-mode provision only — 0048's grill-round provenance and ledger-matched
round floors stay in force.

**The grill becomes the enforced gate where it was only implied.** `task
approve` carried a comment claiming a fresh passing grill was required and
checked nothing, so a stale or failing grill could approve a plan the board was
refusing to display. Approval now applies the board's own predicate: verdict
`pass`, recorded against the current plan digest.

**A task plan must carry `## Workflow` and `## Manual Verification`.** It is
read by the human approving it and by whoever confirms the thing works, and a
file-by-file work order serves neither. Heading level is not enforced. A
```mermaid diagram is asked for in words, not mechanically — demanding one
would produce box-and-arrow filler.

## Consequences
<!-- What follows: tradeoffs accepted, doors closed, work implied. -->

- An operator in auto mode stays in auto mode.
- The board and the approval gate can no longer disagree about whether the same
  plan is ready.
- `post_tool_use` keeps recording plan-mode markers as event-log provenance;
  nothing gates on them. `plan_body_digest` and the marker schema stay for that
  recording, but no gate now depends on their cross-platform stability.
- Trades a cheap mechanical check for one that cannot be satisfied by ritual.
  A plan can now be authored in any mode — including badly — and the grill is
  what has to catch that. That is the intended shift, not a gap.
