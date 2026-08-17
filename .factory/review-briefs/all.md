# Branch-wide plan-contract review brief

For each contract, emit a verdict — implemented | partial | missing — with file:line evidence, recorded as contract_verdicts in the quality artifact. Then review the diff normally; the contract check does not replace the quality/performance/security lenses.

## Task ACC2-T1

### Plan contracts

- **ACC2-C1**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: a task grill missing inspected_refs/current_flow/criteria_map/decision/new_abstractions, with an unmapped criterion, a gap covered by neither a {question, options, chosen} rounds entry nor a source-named citation, or pass+split/block is refused
- **ACC2-C2**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: block without escalation_packet {issue, evidence, recommendation, alternatives, rollback} is refused
- **ACC2-C3**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: existing task-grill fixtures migrate via the shared helper and the suite stays green

### Reviewer focus

Task-gate-only conditionality is the risky seam: spec/signoff/epics/plan grill payloads must keep recording unchanged - regression risk across every existing gate fixture. inspected_refs existence-checking accepts path and path:symbol refs (validate the path part; a missing path refuses). Criteria coverage compares against the frontier task's acceptance_criteria in the PROTECTED decomposition, never the caller payload. Per-finding accountability is deterministic: every gap maps to a rounds entry ({question, options, chosen} - shape-checked) or a citation with a named source; the recorder refuses uncovered gaps - this encodes the operator's per-finding-choice protocol, not blanket sanction. New fields are machine evidence: keep values free of secret-shaped strings (evidence-vs-tooling watch class).

## Task ACC2-T2

### Plan contracts

- **ACC2-C4**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: contract, plan-body, and product-tree changes each stale a grill; .factory/ and plans/ commits and forge plan assume do not
- **ACC2-C5**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: caller-supplied --task-digest is gone; recorder and gates derive the same grounding digest

### Reviewer focus

The staleness matrix is the contract: contract-field change, plan-body change (excluding the appended Implementation Assumptions section - recorded lesson), and any product commit each stale a grill; commits touching only .factory/ or plans/ do NOT, or the regrill treadmill returns. product_tree_digest hashes the index blob list (path+sha) excluding those prefixes - deterministic, no mtime. Stage measurement's task_sha256 (four-field) is UNCHANGED - grounding_digest is the grill binding only; do not couple the two (decision 0023 no-rebaseline). --task-digest removal breaks callers: the refusal message tells them the digest is now derived. Self-application: the very next grill (ACC2-T3's) records under this derivation.

## Task ACC2-T3

### Plan contracts

- **ACC2-C6**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: the task grill refuses when criteria_map does not cover the protected acceptance criteria or plan_contracts statements mismatch it
- **ACC2-C7**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: first recording is fully skeletal; pending graph edits refuse; done contracts are immutable under a full-contract digest

### Reviewer focus

Three seams. (1) First-recording detection is 'no protected authority exists'; the legacy-migration fixture flow becomes record-skeletal -> re-record frontier detail -> drop authority; prepare_legacy_stage_migration and stage-migrate tests must survive (recorded lesson: migrate before re-recording). (2) The freeze must not break the sanctioned mid-stage scope repair: re-recording the ACTIVE frontier task's contract fields stays legal; only pending id/order/dependency edits and done-task contract changes refuse. (3) plan_contracts binding is deterministic: the set of plan_contract statements equals the set of criteria_map keys (= protected acceptance criteria); the grill recorder refuses a mismatch; review-side verdicts are already FORGE-REV-2's.

## Task ACC2-T4

### Plan contracts

- **ACC2-C8**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: default, lowered, justified-higher, and exceeded budgets behave as specified at stage done
- **ACC2-C9**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: the brief carries the budget and narration lines

### Reviewer focus

Counting is the risky seam: files and lines (additions+deletions) measured over the SAME diff _measure already computes (baseline to now, commits plus working tree), excluding .factory/ and plans/ exactly as measurement's evidence exclusions do - two different diff computations would let the budget and the measurement disagree. Default 8 files/400 lines is a policy target (recorded p90s 5/256 product-only, 20/672 all-paths) - state it in the refusal. Raising needs a non-empty written reason validated at record time; lowering is free. The over-budget refusal names the split path (grill decision=split, prefix-freeze appends from T3). Brief additions are two lines in compose_brief - budget and the conduct s8 narration line - no new sections. Lite/quickfix/degraded windows untouched.

## Task ACC2-T5

### Plan contracts

- **ACC2-C10**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: board task rows match task_frontier_state for every state
- **ACC2-C11**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: existing board tests green

### Reviewer focus

One derivation, two consumers: extend factory_lib with task_rows(root) returning ALL tasks' states (skeleton|ready|grilled|active|done, grill fresh/stale via the same grounding_digest compare, budget used/limit for the active stage via the same _measure-consistent counting), built ON TOP of the pieces task_frontier_state uses so routing and board can never disagree; task_frontier_state stays the single-action authority. Board renders rows in the story drawer read-only - no new endpoints, no approval affordances (the board never approves). Budget usage calls the same counting helper stages.py uses - do not reimplement the diff walk. Board redundancy watch-class: keep row derivation one call per render.

## Task ACC2-T6

### Plan contracts

- **ACC2-C12**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: test_full_lifecycle_and_archive passes under the skeletal-first rule
- **ACC2-C13**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: full gate suite green via verify.py

### Reviewer focus

One fixture, one pattern: migrate test_full_lifecycle_and_archive to record-skeletal-then-re-record exactly as the eight prior migrations did; assert the lifecycle's later phases are untouched. No rule weakening.

## Task ACC2-T7

### Plan contracts

- **ACC2-C14**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: every fixture recording execution detail as a first recording uses record_skeleton_then_frontier
- **ACC2-C15**
  - Source: plans/active/FORGE-ACC-2-grills-carry-proof-diffs-stay-reviewable.md#acceptance-criteria
  - Statement: the full gate suite passes via verify.py

### Reviewer focus

Sixteen known failures, one class: first-recording detail refused by the skeletal rule. Known names: test_user_facing_artifacts_must_attest_design_skills, test_lockout_denies_product_write_under_approved_plan, test_registered_hook_path_keeps_recorder_and_lockout_armed, test_harness_repo_locks_machinery_writes_without_a_plan, test_story_timeline_is_recorded_and_archived_with_its_story, test_review_hardening_guards, test_structured_findings_recorded_and_malformed_refused, test_stage_tasks_are_sequential_and_parallel_flag_is_refused, test_delegate_derives_write_from_stage_state, plus seven more - run the full suite to enumerate, migrate EVERY instance to record_skeleton_then_frontier, and re-run the full suite to prove zero remain. No rule weakening; tests asserting refusal semantics keep their original assertions. review_budget note: this task may exceed 400 changed lines only because migrations are mechanical single-pattern rewrites - if so, raise with that written reason rather than splitting sixteen identical edits.
