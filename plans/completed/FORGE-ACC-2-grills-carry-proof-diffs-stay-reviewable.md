---
issue: FORGE-ACC-2
title: Grills carry proof, diffs stay reviewable
status: approved
saved: 2026-08-14T06:01:01+00:00
story: FORGE-ACC-2
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
  - 0044-accountable-engineering-loop
  - 0045-conflict-free-story-state
---

# FORGE-ACC-2 story plan — Grills carry proof, diffs stay reviewable

## Problem

FORGE-ACC-1 made the JIT frontier a hard rail, but the grill it gates on is still a self-asserted artifact: `factory/schemas/grill.json` requires no evidence, no criteria coverage, no decision, and no human rounds; `record_grill_from_json.py` accepts a caller-supplied `--task-digest` bound to only four contract fields; nothing bounds a stage diff from above; the board still shows nothing at task level. Decision 0044 (accepted) and the confirmed `accountable-engineering-loop` spec (as amended: human rounds mandatory, frozen skeleton, immutable completed contracts) define the target.

## Scope / Non-goals

**In scope (story FORGE-ACC-2, spec-linked):** task-grill proof fields + human rounds + escalation packets; internally derived grounding digest; frozen task graph and immutable completed contracts; grilled `criteria_map` ↔ `plan_contracts` wiring (FORGE-REV-2); review budget at `stage done` + budget/narration lines in the composed brief; board task rows.

**Non-goals:** everything FORGE-ACC-3 owns (approved-plan digest binding, recorded local review, commit-before-done, coherent one-run branch review, closeout ordering, write-window refusal) and FORGE-CFS-1 (story-scoped state). Lite/quickfix/degraded untouched. Spec/signoff/epics/plan gates keep their existing artifact shape except where noted (rounds).

## Acceptance Criteria

1. A task grill missing `inspected_refs` (existing paths), `current_flow`, a total `criteria_map`, a keep/split/block `decision`, or the declare-or-empty `new_abstractions` field is refused; `pass` with split/block refused; `block` without an escalation packet refused; zero recorded human rounds refused.
2. The recorder derives the grill digest from the full task contract, the approved-plan digest excluding appended assumptions, and a product-tree hash excluding `.factory/` and `plans/`; caller-supplied `--task-digest` is removed; contract, plan, and product-tree changes stale the grill while `.factory/`/`plans/` commits do not.
3. The frontier task's `criteria_map` lands as `plan_contracts` so the existing FORGE-REV-2 quality review verdicts each criterion.
4. `stage done` refuses a diff over the task's review budget (default 8 files / 400 lines excluding `.factory/` and `plans/`; lower free, higher needs a written reason) and the composed brief states the budget.
5. The board renders the in-flight story's task rows (state, grill freshness, budget usage) from the same derivation `forge next` uses.
6. Initial decomposition recording refuses execution detail (including `reviewer_focus`/`plan_contracts`) on every task; later recordings freeze the id/order/dependency skeleton; completed contracts are immutable under a full-contract digest (spec amendment, folded here from the rescue audit).

## Technical Approach

- **Grill proofs (task gate only).** `grill.json` gains task-gate-conditional required fields: `inspected_refs` (list; recorder existence-checks paths), `current_flow` (non-empty str), `criteria_map` (list of {criterion, proof}; recorder checks total coverage of the frontier task's `acceptance_criteria`), `decision` (keep|split|block), `new_abstractions` (list, may be empty but must be present), `rounds` (list of {question, resolution}; ≥1 — the AskUserQuestion round record). `pass` + split/block refused; `block` requires `escalation_packet` {issue, evidence, recommendation, alternatives, rollback}. Validation is existence/coverage-only; prose quality stays the independent griller's job.
- **Internal grounding digest.** New `grounding_digest(root, task)` in `factory_lib.py` beside `task_digest`: sha256 over (full task contract sorted, approved-plan digest computed excluding the `Implementation Assumptions` section, `product_tree_digest(root)` = hash of the index blob list excluding `.factory/` and `plans/`). `record_grill_from_json.py` drops `--task-digest` and derives; `require_task_grill` and `task_frontier_state` re-derive. Evidence commits can't stale a grill; any product/plan/contract change does.
- **Frozen skeleton + immutable completed contracts.** `record_decomposition_from_json.py`: on first recording (no protected authority) refuse execution detail on every task and `reviewer_focus`/`plan_contracts` on non-frontier tasks; on re-records refuse changes to pending task ids/order/dependencies (frontier contract fields exempt) and any change to a done task's full contract (full-dict digest, not four fields).
- **criteria_map ↔ plan_contracts.** The JIT contract declares `plan_contracts`; the task grill recorder refuses when `criteria_map` doesn't cover the acceptance criteria or `plan_contracts` is missing/mismatched with it. Review-side enforcement already shipped (FORGE-REV-2).
- **Review budget.** Task-optional `review_budget` {max_changed_files, max_changed_lines, reason?}; default 8/400 (policy target — recorded p90s 5/256 product-only, 20/672 all-paths); recorder refuses raising without `reason`. `_measure` in `stages.py` counts the stage diff excluding `.factory/`/`plans/` and refuses over-budget with split guidance. `compose_brief` states the budget and the conduct §8 narration line.
- **Board task rows.** `board.py` story drawer: one row per task from `task_frontier_state`-style derivation (extracted so next/board/gates share it) — state skeleton|ready|grilled|active|done, grill fresh/stale, budget used/limit for the active stage.

Reuse: `task_frontier_state` + `require_ready_task` (ACC-1), `plan_contracts` validation (FORGE-REV-2), lesson patterns (assumptions-appendix exclusion; evidence-vs-tooling tripwire — new grill fields must survive the autoreview bundler's secret heuristic and union-free per-file layout).

Rejected shape: proofs on all five gates at once — only the task gate has the enforcement consumers today; widening is a later decision.

## Decisions

- Implements accepted decisions 0044 and the amended confirmed spec; no new decisions expected. If digest derivation forces a deviation (e.g. index-vs-HEAD tree hashing), record it via `forge decision new` before decomposition.

## Surface Impact

| Surface | Class | Notes |
|---|---|---|
| Runtime behavior | Changed | grill recorder refusals, digest derivation, stage-done budget refusal, recorder freeze rules |
| API | N-A | no external API |
| Data/schema | Changed | grill.json task-gate fields; decomposition task `review_budget`; no migration of recorded history |
| CLI/ops | Changed | `record_grill_from_json.py` loses `--task-digest`; refusal messages |
| UI | Changed | board task rows |
| Docs | Changed | WORKFLOW.md digest description, griller.md task-gate payload, decomposer.md budget field |
| Tests | Changed | new gate coverage; existing task-grill fixtures gain proof fields |

## Task Decomposition

1. **ACC2-T1 — task grills carry proof and rounds** (AC 1): grill schema + recorder + escalation packet + tests; fixture migration for existing task-grill tests.
2. **ACC2-T2 — grounding digest derived internally** (AC 2): factory_lib digest helpers, recorder arg removal, gates re-derive, staleness matrix tests.
3. **ACC2-T3 — frozen skeleton, immutable completed contracts, plan_contracts wiring** (AC 3, 6): decomposition recorder rules + grill-recorder coverage check + tests.
4. **ACC2-T4 — review budget at stage done and in the brief** (AC 4): recorder validation, `_measure` refusal, compose_brief lines + tests.
5. **ACC2-T5 — board task rows** (AC 5): shared derivation extraction + board rendering + tests.

## Risks

- **Self-application mid-story:** once ACC2-T1 lands, this story's own remaining grills must carry proofs; once T2 lands, digests re-derive — the in-flight grills for later tasks will stale at each enforcement upgrade and must be re-recorded under the new rules (expected, ledger the repair; it is the dogfooding proof).
- **Fixture fallout:** every existing task-grill fixture needs proof fields after T1; budgeted into T1's scope like ACC-1's migrations.
- **Evidence-vs-tooling (watch class):** new grill fields are machine-generated evidence; tripwire per WORKFLOW Recurring Findings if the bundler/secret-scanner flags them.
- **Open lite window Q-0071 (inherited from upstream):** WIN-ENC's CI-fix window is open in this branch's ledger; `pr_ready` will refuse if it's still open at closeout — resolve upstream or close with its required review before shipping.
- **Stacked base:** branch stacks on FORGE-ACC-1's branch; retarget/rebase after #104 merges.

## Verify Plan

- `python3 -m pytest factory/tests/test_gates.py -q` (full at verify) plus targeted selections per task.
- `python3 factory/scripts/check_dual_runtime.py`; `python3 factory/scripts/verify.py`.
- Staleness matrix proven by tests: contract change / plan-body change / product commit → stale; `.factory/`-only or `plans/`-only commit / `forge plan assume` → fresh.
- Live self-check: the story's own later tasks run under each newly landed gate.
