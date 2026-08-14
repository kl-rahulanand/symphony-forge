---
issue: FORGE-WIN-3
title: Delegation runs on native Windows
status: approved
saved: 2026-08-13T06:13:09+00:00
story: FORGE-WIN-3
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

# FORGE-WIN-3 — Delegation runs on native Windows

## Problem

WIN-1 and WIN-2 made the hooks, launcher, and doctor work on native Windows,
but `forge delegate` — the sole sanctioned write path (0037) — still cannot
launch or supervise a Codex worker there. `delegate.py`'s process model is
POSIX-only: it spawns with `subprocess.Popen(start_new_session=True,
preexec_fn=…)` (delegate.py:1052-1058) — `preexec_fn` *raises* on Windows and
`start_new_session` is a no-op — discovers processes by shelling out to `ps`
(`_process_table` :210, `_process_start_identity` :185, `_process_is_zombie`
:202, `_tagged_processes` :244, none of which exist on Windows), and
terminates worker trees with `os.killpg` (:173/:364/:392). So on Windows a
delegation cannot launch, and even if it launched, a runaway or descendant
tree could not be reaped and the delegation lock would never release. This is
the last piece that makes the harness actually *usable* end-to-end on Windows.

Already done (do not re-touch): the delegation file lock is cross-platform
(WIN-1.2 `_lock_file`/`_unlock_file` :471-503, msvcrt on nt, lazy fcntl on
POSIX); the ledger append is lock-free O_APPEND (:142). `os.kill(pid, 0)`
liveness (`_pid_alive` :161) and `signal.signal(SIGINT/SIGTERM)` arming
(:1037) already work on Windows; SIGHUP/SIGQUIT are already getattr-filtered.

Two decisions were human-settled at this planning gate (2026-08-13):
psutil as the cross-platform process abstraction; AC2 reframed to the
achievable half (workspace-write) with the unelevated piece deferred.

## Scope / Non-goals

In scope — the story's ACs (AC2 reframed): a delegation launches, is
supervised, and its worker tree is reaped on native Windows, proven on
windows-latest CI; the recorded invocation reflects the workspace-write
sandbox.

Out of scope, deliberately:

- **The unelevated sandbox flag / codex config** — the installed companion
  (1.0.6) `task` verb has NO `-c`/`--sandbox` passthrough; `--write` already
  selects `workspace-write` internally and no "unelevated" concept exists in
  the companion. Driving `~/.codex/config.toml` is forbidden by 0040 (no
  user-global config writes) and reopens the deferred elevation-trust class.
  The unelevated piece stays with D-0021.
- **No forking the companion** — external plugin; if a seam is truly needed
  it is an upstream ask, not our change.
- **Doctor's read-only-probe-under-admin residual (D-0022)** and the
  **hostile-env batch residuals (D-0023)** — not this story; WIN-3 is the
  process model, not the elevation-security pass.
- **D-0019** (hook-health executor fidelity) — separate concern; noted but
  not bundled unless the process work naturally touches it.

## Acceptance Criteria

From `plans/roadmap.json` FORGE-WIN-3, AC2 reframed per the gate decision:

1. `delegate.py` replaces `ps`/`killpg`/`preexec_fn`/`start_new_session` with
   cross-platform equivalents (psutil); a delegation completes on
   windows-latest CI (launch → running → reap → terminal row → lock release).
2. The recorded delegate invocation on Windows reflects the workspace-write
   sandbox (asserted from the existing `--write`); the unelevated/config-level
   tightening is deferred (D-0021), stated in the plan and docs.

## Technical Approach

Seams verified by read-only exploration 2026-08-13 (delegate.py is 1196 lines;
line refs current).

- **psutil as the single process abstraction** (new runtime dep): replace the
  `ps`-shelling and `killpg` in BOTH platforms with psutil, collapsing the
  nine POSIX-only functions to one portable path:
  - `_process_table` / `_descendants` / `_tagged_processes` → `psutil.Process(pid).children(recursive=True)` and `psutil.process_iter(['pid','ppid','create_time','environ','cmdline'])`. This DELETES the `ps -o lstart=` calendar-fragility (recorded lesson `normalize-ps-derived-identity`) — psutil `create_time()` is a float, no whitespace parsing.
  - `_process_start_identity` / `_process_is_zombie` → psutil `create_time()` / `status()` (`psutil.STATUS_ZOMBIE`).
  - `_process_group_alive` / `_signal_verified_process_group` / `_capture_spawn_identity` termination → psutil `Process.terminate()`/`kill()` over `children(recursive=True)` + the leader, identity-checked by `create_time()` (PID-reuse guard preserved).
  - The `FORGE_PROCESS_TOKEN` env-marker sweep (detached-child catch) → `process_iter(['environ'])` filtered by the token (psutil reads env cross-platform where permitted; on Windows environ may be restricted for other-user procs — same-user workers are readable).
- **Launch (`launch_companion` :1052-1058)**: drop `preexec_fn`; branch the
  Popen — Windows: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`
  (the group-leader analog, so the recorded `pgid` becomes the process-group
  root psutil walks); POSIX: keep `start_new_session=True`. The
  `blocked_termination_signals()` / `unblock_termination_signals_in_child`
  atomicity is already a no-op on Windows (pthread_sigmask absent) — leave the
  guard, it degrades cleanly.
- **`_reconcile_stale_launches` (:584)**: its `_process_start_identity` +
  `_terminate_tagged_processes` + `_process_group_alive` calls all route
  through the psutil layer once the helpers are ported — no separate Windows
  branch needed there.
- **Doctor**: add a psutil presence check to `forge doctor` (required),
  and install it in `doctor --fix` (pip/uv). psutil ships to every client
  via the vendored machinery — the install path must be honest (named red row
  when absent), reusing the WIN-2 doctor-row + `--fix` patterns.
- **Dependency vendoring**: psutil must be declared where the harness pins its
  Python deps (verify.py/`.envrc` toolchain, `factory/` requirements if any);
  the `uv run --with pytest` test path gains `--with psutil`.
- **AC2**: assert the recorded `.factory/delegations.jsonl` argv carries
  `--write` (→ workspace-write) on Windows; document in docs/windows.md that
  unelevated sandbox is deferred (D-0021).

## Decisions

- NEW: `0042-psutil-cross-platform-process-model` (record before
  decomposition): psutil is the harness's cross-platform process abstraction;
  the `ps`-shelling and `killpg` are replaced on both platforms (not merely
  Windows-branched), retiring the ps-lstart fragility. Accepts the first
  runtime Python dependency in the harness; doctor gates its presence and
  `--fix` installs it. Rejected: per-function os.name branching (two paths in
  ~9 functions, subtle Windows tree logic, keeps the ps fragility on POSIX);
  Windows-only job objects via ctypes (more code, no POSIX simplification).
- AC2 reframe (workspace-write achievable, unelevated → D-0021) is a
  gate-settled scope narrowing, recorded in 0042's context, not a new record.
- No other new decisions.

## Surface Impact

| Surface | Class | Note |
|---|---|---|
| Runtime behavior | Changed | delegate process launch/discovery/termination now psutil-based cross-platform |
| API | N-A | — |
| Data/schema | Unchanged by design | delegations.jsonl fields unchanged (pid/pgid/create-time identity keeps shape) |
| CLI/ops | Changed | doctor gains a psutil row + --fix install |
| Deps | Changed | psutil added — first runtime Python dep; vendored to clients (0042) |
| Docs | Changed | docs/windows.md: delegation supported on Windows; unelevated deferred |
| Tests | Changed | new nt delegation E2E joins windows CI selector; ps-monkeypatch unit tests migrate to psutil fakes |

## Task Decomposition

(JIT contracts per 0032; CI-blind — windows-hook-gates is the Windows
verifier. Sequential; disjoint scopes where possible.)

1. **WIN-3.1 psutil process model** — port the nine functions to psutil,
   drop preexec_fn + branch Popen creationflags, decision 0042, migrate the
   ps-monkeypatch unit tests to psutil fakes, dependency declaration.
   Scope: `factory/scripts/forge_cli/delegate.py`, dep manifest,
   `factory/tests/test_gates.py`, `docs/decisions/0042-*.md`.
2. **WIN-3.2 doctor psutil row + Windows delegation E2E + CI + docs** —
   doctor required psutil row + `--fix` install; a new nt-appropriate
   delegation E2E (launch → running → psutil/taskkill teardown → terminal
   failed + lock release) added to the windows-hook-gates selector;
   docs/windows.md delegation section (unelevated deferred).
   Scope: `factory/scripts/forge_cli/doctor.py`,
   `.github/workflows/factory-scaffold.yml`, `factory/tests/test_gates.py`,
   `docs/windows.md`.

## Risks

- **CI-blind cost (accepted)**: WIN-3 is pure native-Windows process
  behavior; windows-hook-gates is the sole verifier and each round is a full
  CI cycle. Mitigate by making the psutil port reason-complete and keeping
  POSIX behavior byte-identical (the POSIX suite catches regressions locally;
  only the genuinely-Windows launch/teardown needs CI). LESSON APPLIED: do
  NOT pr_ready before windows CI is green (WIN-2's premature close).
- **psutil environ access on Windows**: reading another process's `environ`
  can raise `AccessDenied`; the token sweep must catch that and fall back to
  cmdline/children-walk — same-user workers are the only ones we reap.
- **Vendored dependency reaching clients**: psutil must install cleanly on
  client machines; doctor's honest red row + `--fix` is the safety net, and
  the WIN-2 propagation tests (init/adopt/upgrade) should confirm the dep
  manifest ships.
- **Rewrite-regression class (recorded lesson)**: porting ~9 functions in one
  stage risks silently dropping behavior; verify against committed HEAD after
  any multi-round rewrite, and the story-level review is the backstop before
  pr_ready.
- **normalize-ps-derived-identity lesson**: the port DELETES the fragile
  ps-lstart comparison rather than reimplementing it — confirm no residual
  string-normalized identity comparison survives.

## Verify Plan

- `verify.py` with pinned `.envrc` commands (test path gains `--with psutil`).
- Full POSIX gate suite green locally (psutil port must be byte-identical on
  POSIX; the existing termination/reap tests migrate to psutil fakes and stay
  green).
- windows-hook-gates green on the PR with the new nt delegation E2E in its
  selector — the real proof that launch/supervise/reap works on native
  Windows. CI is the verifier (CI-blind, user-chosen).
- Manual sanity (macOS): a real `forge delegate` still launches, supervises,
  and reaps a worker via the psutil path (POSIX).
