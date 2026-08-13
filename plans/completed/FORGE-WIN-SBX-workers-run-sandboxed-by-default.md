---
issue: FORGE-WIN-SBX
title: Workers run sandboxed by default
status: approved
saved: 2026-08-13T05:57:54+00:00
story: FORGE-WIN-SBX
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
---

# FORGE-WIN-SBX — Workers run sandboxed by default

## Problem

The vendored `.codex/config.toml` ships `sandbox_mode =
"danger-full-access"` (line 15) to every client, so any Codex session a
client runs against the repo config gets full machine access by default.
Exploration established the delegation path itself is already safer than
the config implies: `forge delegate` never passes a sandbox flag, and the
installed companion hardcodes `--write` → `workspace-write`
(codex-companion.mjs:485), with read-only as the thread default. The
dangerous default is therefore a dormant liability in the vendored
surface, not the delegation behavior — and nothing freezes
`.codex/hooks.json`, the fail-closed hook config decision 0038 armed:
`check_vendor_integrity.py` hashes only factory/scripts, factory/schemas,
factory/prompts, `forge`, and `.claude/settings.json`, so a client edit
that disarms a vendored Codex hook is invisible to the frozen-gate audit
(decision 0009).

## Scope / Non-goals

In scope: `.codex/config.toml` (default flip + escape-hatch comment),
`factory/scripts/check_vendor_integrity.py` (hash `.codex/hooks.json`),
`factory/tests/test_gates.py` (manifest/config assertions), a decision
record for the flip (orchestrator-authored, human-accepted), and a real
delegation end to end under workspace-write.

Non-goals: no per-task sandbox-escalation plumbing — the companion
accepts no sandbox override (only `--write`), so a delegate-side
escalation flag would be dead machinery until an upstream plugin release;
deferred with a revisit trigger. No hashing of `.codex/config.toml` —
deliberately: AC2 names hooks.json only, hooks are frozen gate surface,
while the sandbox default must remain a client-adjustable, diff-visible
knob because that edit IS the escape hatch. No uv-cache/network sandbox
work (workspace-write already fits the worker contract; implementer.md
forbids the git/control writes it would deny).

## Acceptance Criteria

- Vendored `.codex/config.toml` defaults `sandbox_mode =
  "workspace-write"`, with a comment documenting the escape hatch: a
  genuinely-broader task requires a deliberate config edit in the client
  repo, reviewed in its diff and ledgered per the decision record.
- `check_vendor_integrity.py` includes `.codex/hooks.json` in the hashed
  vendor surface; the manifest freeze test proves an edit to hooks.json
  fails integrity, and the re-vendor test proves adopt/upgrade repair and
  re-hash it.
- Config-default assertion added beside the existing
  init/upgrade hook-portability test.
- A decision record covers the default flip and the escape-hatch
  doctrine (authored this story; acceptance is the human's).
- A real delegation (this story's own implementation run) passes end to
  end with the companion's workspace-write mapping, recorded in the
  testing artifact.

## Technical Approach

1. `.codex/config.toml:15`: `danger-full-access` → `workspace-write`,
   plus a three-line comment naming the escape hatch and pointing at the
   decision record.
2. `check_vendor_integrity.py:23`: add `.codex/hooks.json` to the hashed
   path set. Manifest generation needs no change — `write_manifest()` in
   scaffold/adopt/upgrade derives from the same surface list.
3. Tests: extend `test_scaffold_freezes_gate_surface_and_check_verifies`
   (:12377) and `test_adopt_and_upgrade_refreeze_the_manifest` (:12615)
   to cover hooks.json drift and repair; add the workspace-write default
   assertion near `test_init_and_upgrade_ship_portable_hook_commands`
   (:2572).
4. Decision record (orchestrator-authored before the stage):
   sandboxed-workers-default — records that workspace-write is the
   vendored default, that delegation already runs workspace-write via the
   companion mapping, that full access is obtainable only by a deliberate
   client config edit (the ledgered escape hatch), and that per-task
   sandbox escalation is deferred pending a companion flag.
5. Deferral: per-task sandbox-exception plumbing through
   `launch_companion()` — revisit when the companion grows a sandbox
   override.
6. Evidence: the story's own `forge delegate` write run is the real
   workspace-write delegation; cite it in the automated testing artifact.

## Decisions

New record this story: sandboxed-workers-default (see approach step 4);
acceptance is the human's after review. Consistent with 0009 (frozen
gates — hooks.json joins the frozen surface), 0038 (the hooks being
frozen are the fail-closed ones), and 0037 (workers stay bounded).

## Surface Impact

Clients receive the safer default and the hooks.json freeze on their next
`forge upgrade`; a client that already edited hooks.json will see a
vendor-integrity failure at pr_ready naming the drift — that is the
feature. A client needing full access edits config.toml knowingly; the
diff and the decision record are the ledger.

## Task Decomposition

One bounded task, SBX-T1: config flip + integrity hash + tests land
together (the flip without the freeze leaves the hook surface soft; the
freeze without tests is unproven). The decision record is
orchestrator-authored outside the stage.

## Risks

- A client with legitimately customized hooks.json gets flagged at next
  upgrade: intended behavior (re-vendor or upstream the change), stated
  in the decision record.
- The flip does not change delegation behavior (already
  workspace-write): stated honestly in the decision record so nobody
  reads the story as having hardened a hole it did not.
- Existing manifest fixtures/tests may pin the exact hashed-path list:
  the two named tests are updated in the same stage.

## Verify Plan

- `uv run --with pytest python -m pytest factory/tests/test_gates.py -q
  -k "manifest or freeze or portable_hook"` focused; FULL suite before
  review (lesson from Q-0057: content pins live in differently-named
  tests).
- `python3 factory/scripts/check_dual_runtime.py` and
  `check_vendor_integrity.py` green in the harness repo.
- The story's own delegation run recorded as the workspace-write E2E.
