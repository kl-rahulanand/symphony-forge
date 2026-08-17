---
issue: FORGE-ACC-1
title: JIT frontier is enforced, not advisory
status: approved
saved: 2026-08-13T17:11:05+00:00
story: FORGE-ACC-1
decisions_reviewed:
  - 0001-determinism-contract
  - 0002-concurrency-one-task-per-branch
  - 0003-model-tiers-terra-explore-sol-implement
  - 0005-recurring-findings-escalation
  - 0006-lessons-ledger
  - 0007-stage-commit-loop
  - 0008-loop-health-audit
  - 0009-frozen-gate-integrity
  - 0010-client-signoff
  - 0011-orchestrator-runs-autoreview
  - 0012-project-level-memory
  - 0013-always-armed-planning-lock
  - 0014-specs-before-signoff
  - 0015-plan-contradiction-gate
  - 0016-machinery-dir-rename
  - 0017-repo-as-system-of-record
  - 0018-delegation-gates
  - 0021-derived-ordering
  - 0022-conflict-free-ledgers
  - 0023-stage-delta-by-ref
  - 0025-evidence-lifetime-contract
  - 0026-bundled-example-validated-by-production-validators
  - 0027-responsive-proof-without-a-browser
  - 0028-path-boundary-invariant
  - 0029-plan-approval-in-plan-mode
  - 0030-harness-source-is-product-in-its-own-repo
  - 0031-workflow-modes-lite
  - 0032-jit-task-planning
  - 0033-gate-a-declares-all-work-records
  - 0034-vendored-docs-are-client-safe
  - 0035-commit-belt-keeps-ledger-fresh
  - 0036-client-gates-arm-on-roadmap
  - 0037-strict-role-split
  - 0038-portable-fail-closed-hooks
  - 0040-windows-user-scope-first-elevation-deferred
  - 0041-sandboxed-workers-default
  - 0042-psutil-cross-platform-process-model
---

# FORGE-ACC-1 — JIT frontier is enforced, not advisory

## Problem

Decision 0032 mandates skeletal decomposition and JIT task contracts, but the
only enforcement is `require_task_grill` inside `forge delegate` — and it is
bypassed for `--read-only` runs and for active stages whose `write_scope` is
empty (which silently degrade to read-only). `stage start` activates a stage
with no grill and no contract-completeness check (`forge_cli/stages.py`,
`_cmd_start_locked`), `forge next`'s implementing branch routes straight to
`stage start`/`delegate` with no contract-authoring or grill step
(`forge_cli/phase.py:197-210`), the decomposition recorder accepts full
execution detail on every future task, and `docs/FACTORY.md:129-138` still
instructs authors to write full upfront contracts. A user following the rail
reaches delegate's refusal blind, and a user not following it can start
implementation with no authored, grilled contract at all.

## Scope / Non-goals

**In scope (spec: docs/specs/accountable-engineering-loop.md, story
FORGE-ACC-1):** skeletal-future-task validation in the decomposition
recorder; a shared `require_ready_task()` gate called by `stage start` and
`delegate`; refusing the silent empty-scope read-only degradation; `forge
next` routing for the four frontier states; doc/prompt alignment.

**Non-goals (FORGE-ACC-2):** grill proof fields, internally derived grounding
digest (`--task-digest` removal), review budgets, board task rows. Story 1
keeps the existing four-field `task_digest` and caller-supplied recorder arg
untouched. Lite, quickfix, and degraded windows are untouched (spec
Non-goals).

## Acceptance Criteria

From the roadmap item (spec-linked):
1. `record_decomposition_from_json.py` refuses execution detail
   (`write_scope`, `required_tests`, `verify_commands`) on any task after the
   earliest pending leaf and accepts it on the frontier task.
2. A shared `require_ready_task()` makes `stage start` and `delegate` both
   refuse an incomplete contract or missing/stale grill; an active stage with
   empty `write_scope` refuses instead of silently degrading to read-only;
   explicit `--read-only` still passes.
3. `forge next` reports author-contract / grill / stage-start / delegate as
   the single next action per task state.
4. `docs/FACTORY.md`, `WORKFLOW.md`, and `factory/prompts/decomposer.md`
   state the enforced JIT contract with no upfront-contract contradiction.

## Technical Approach

- **Recorder (`factory/scripts/record_decomposition_from_json.py`).** After
  existing validation, locate the earliest pending leaf (order-first task not
  marked done in protected stage state). Any later task carrying non-empty
  `write_scope`, `required_tests`, or `verify_commands` is refused with the
  offending task id and field named. Completed tasks are exempt (immutable
  history; frontier-cutover for legacy decompositions). The frontier task MAY
  carry detail (that is JIT authoring).
- **Shared gate (`factory/scripts/factory_lib.py`).** New
  `require_ready_task(base, task_id)`: resolves the task, refuses when it is
  not the earliest pending leaf, when any of `write_scope`, `required_tests`,
  `verify_commands`, `reviewer_focus` is empty, then delegates to the
  existing `require_task_grill` with the existing `task_digest`. One guard,
  two callers — no duplicated logic.
- **`stage start` (`forge_cli/stages.py`, `_cmd_start_locked`).** Call
  `require_ready_task` before activating. This is the first hard refusal
  point; its message names the missing piece and the command that produces
  it.
- **`delegate` (`forge_cli/delegate.py`).** Keep `require_ready_task` as
  defence in depth for write runs. An active stage with empty `write_scope`
  now refuses with "author the contract or pass --read-only" instead of
  silently launching read-only. Explicit `--read-only` bypasses readiness
  (exploration is legitimate before the contract exists).
- **`forge next` (`forge_cli/phase.py` implementing branch).** For the
  earliest unfinished task, report exactly one action: contract incomplete →
  author the JIT contract and re-record the decomposition (decision 0032
  loop); complete but grill missing/stale → run the task griller; fresh pass
  → `forge stage start <id>`; active stage → `forge delegate <id>`. The
  board's next_actions re-parse inherits this unchanged.
- **Docs.** Rewrite `docs/FACTORY.md`'s leaf-task field list as the skeletal
  contract + JIT authoring loop; sweep `WORKFLOW.md` and
  `factory/prompts/decomposer.md` for contradictions (their JIT sections are
  already correct; the fix is removing the stale upfront instruction).

Rejected simpler shape: gating only `delegate` harder (no `stage start`
gate). Rejected because the stage baseline is stamped at `stage start` — an
ungrilled start pollutes measurement state and the user reaches the refusal
one step later than the mistake. The gate belongs where the state changes.

Rejected larger shape: a stored `contract_status` field. Readiness derived
from field presence cannot drift from content; stored status can (spec
Non-goals).

## Decisions

- `docs/decisions/0044-accountable-engineering-loop.md` (proposed; amends
  0032's enforcement, not its substance) — this story implements its
  frontier-enforcement half.
- No other new decisions: all remaining choices derive from the confirmed
  spec and decisions 0032, 0018, 0007.

## Surface Impact

| Surface | Class | Notes |
|---|---|---|
| Runtime behavior | Changed | new refusals at recorder, stage start, delegate; new `forge next` routing |
| API | N-A | no external API |
| Data/schema | Unchanged by design | no schema changes in story 1; grill schema changes are FORGE-ACC-2 |
| CLI/ops | Changed | refusal messages and `forge next` output; no new commands |
| UI | Read-only | board inherits next_actions text; task rows are FORGE-ACC-2 |
| Docs | Changed | FACTORY.md, WORKFLOW.md, decomposer.md alignment |
| Tests | Changed | new gate coverage in factory/tests/test_gates.py; existing fixtures that record full future-task detail must move to frontier-style recording |

## Task Decomposition

Sequential, one worktree (0002), each bounded for a single Codex session:

1. **ACC1-T1 — recorder refuses future execution detail** (AC 1).
   `record_decomposition_from_json.py` + its tests + fixture migration.
2. **ACC1-T2 — shared readiness gate at stage start and delegate** (AC 2).
   `factory_lib.py`, `stages.py`, `delegate.py` + tests, including the
   empty-scope refusal and `--read-only` pass-through.
3. **ACC1-T3 — forge next routing + doc alignment** (AC 3, 4). `phase.py` +
   tests; `docs/FACTORY.md`, `WORKFLOW.md`, `factory/prompts/decomposer.md`.

Per decision 0032 the initial recorded decomposition carries this list
skeletally; each task's full contract is authored JIT at its frontier.

## Risks

- **Fixture fallout:** many existing tests record decompositions with full
  detail on every task. ACC1-T1 migrates them deliberately; the refusal must
  exempt done tasks or legacy re-records would break (frontier cutover).
- **Self-application:** this story runs under the harness it modifies; a
  wrong refusal can wedge the story's own loop. Mitigation: refusals fire
  only on newly recorded decompositions, and `git revert` restores the rail.
- **Evidence-vs-tooling (watch class):** no new evidence formats in story 1;
  tripwire — if review flags a machine-evidence/tooling collision again,
  escalate per WORKFLOW.md Recurring Findings rather than patching.
- **Merge with in-flight stories:** FORGE-WIN-ENC is active on another
  worktree; this branch discarded its inherited state at intake
  (`--discard-active`, ledgered). Roadmap merges heal by union (0022).

## Verify Plan

- `python3 -m pytest factory/tests/test_gates.py -q` — including new cases:
  future-detail refusal, frontier acceptance, ready/unready stage start and
  delegate refusals, empty-scope refusal, `--read-only` pass, `forge next`
  single-action routing per state.
- `python3 factory/scripts/check_dual_runtime.py` green.
- `python3 factory/scripts/verify.py` green.
- Live self-check: this story's own remaining tasks are driven through the
  new rail (`forge next` → author → grill → start → delegate) — the harness
  proves the loop on itself.
