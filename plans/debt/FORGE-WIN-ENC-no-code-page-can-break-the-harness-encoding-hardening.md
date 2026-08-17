---
issue: FORGE-WIN-ENC
title: No code page can break the harness (encoding hardening)
status: approved
saved: 2026-08-13T16:06:14+00:00
story: FORGE-WIN-ENC
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

# FORGE-WIN-ENC — No code page can break the harness

## Problem

PR #101 (merged ef738988) proved the bug class on a default Windows cp1252
console and fixed its output half: factory_lib + the four standalone
`check_*.py` scripts force UTF-8 (`errors="replace"`) on stdout/stderr at
import, and `factory_lib.run_cmd` decodes child output as UTF-8. Everything
else in the harness still uses the locale default, which on a fresh Windows
box is the ANSI code page. Read-only exploration (Codex rescue, 2026-08-13)
inventoried the remainder:

- ~30 subprocess call sites in `factory/scripts/**` decode child output with
  the locale default (`text=True`, no `encoding=`): `common.run_quiet` (15
  doctor call sites — winget/git/hook-health captures), the git queries in
  factory_lib/stages/phase/audit/adopt/lessons/project/quickfix/roadmap/
  sanitise/scaffold/gstack, `pre_tool_use.py`'s ledger `git add`, and the
  standalone checkers' own git calls.
- ~100 text-mode file I/O sites without explicit `encoding=`
  (`read_text`/`write_text`/text `open`): plan/spec/decision markdown,
  evidence JSON/JSONL (events, signals, recorders, pr_ready archive),
  scratchpad, vendored-doc scaffolding, upgrade manifests.
- SIX text temp-log handles capture child output with the locale encoding
  (validated by the sol-xhigh pass, 2026-08-13): delegate's worker
  stdout/stderr (`delegate.py:1055-1056`, read back `:1117-1130`) plus the
  required-test runner's pair (`stages.py:855-856`, read `:891-894`) and the
  verify-command runner's pair (`stages.py:945-946`, read `:980-983`).
- stdin is an unswept boundary: hook JSON enters via locale-configured
  `sys.stdin` (`factory_lib.py:978-982`) and all four recorder scripts repeat
  the pattern (`record_{decomposition,grill,review,test}_from_json.py`).
- Launcher runs export `PYTHONUTF8=1` (WIN-2), so the gap opens on DIRECT
  invocations: `python factory/scripts/<script>.py` (CI does this in four
  workflows), registered hooks on machines where the launcher env is bypassed,
  and any client tooling that imports the scripts.

On cp1252 the failure is usually silent — mojibake in evidence files and
comparisons — and occasionally fatal (five undefined cp1252 bytes raise
UnicodeDecodeError mid-flow, aborting before evidence lands).

## Scope / Non-goals

In scope: every text-mode boundary in `factory/scripts/**` names its encoding
explicitly; a structural check prevents regression; a forced-cp1252 CI proof.

Out of scope, deliberately:

- **Byte-exact and digest paths stay bytes** (inventory §5 + sol-xhigh
  additions — the DO-NOT list): `check_dual_runtime.py:99-108` copy
  detection, `check_vendor_integrity` SHA-256, `factory_lib.sha256_of`,
  `forge_cli/context.py` hashing (normalized-bytes — CRLF-rewritten before
  hashing, noted precisely), `forge_cli/gstack.py:125` byte equality,
  `stages.py:252-265,551-564` measurement/authority digests (NB symlink
  targets str.encode there — swept only if byte-behavior preserved),
  `upgrade.py`'s NUL-delimited surrogateescape paths, factory_lib's fd-based
  safe writers (`:525-623`), delegation's byte ledger + brief digest
  (`delegate.py:150-166,977-1001`), review-brief bytes
  (`review_brief.py:80-86`), board HTTP payload bytes (`board.py:559-577`),
  downloaded executable bytes (`doctor.py:983-990`), plan/task digests
  (`plans.py:70-71`, `stages.py:575-578`), signal/quickfix identity hashes
  (`signal.py:61-67`, `quickfix.py:99-105`), and check_agents_hygiene's
  UTF-8 byte-budget (`:18-22`). Correct today BECAUSE they avoid text
  decoding; the sweep must not touch them.
- No `errors="replace"` on evidence/digest-adjacent READS — replace belongs
  only where output is for human display (captures, logs, prints). A strict
  UTF-8 read that fails loudly on corrupt evidence is the correct behavior
  (0009 frozen-gate integrity).
- No change to PR #101's landed surface; no launcher changes (WIN-2 owns
  PYTHONUTF8); no non-`factory/scripts` sweep (client app code is not ours).
  The inline Python in `.github/workflows/{roadmap-gate,pr-link}.yml` also
  default-decodes — parked with a deferral (harness-owned but outside this
  story's scripts surface; revisit trigger: first mojibake in a gate log).
- ENC branches from MAIN (post-#101): the plan's baseline exists there, not
  on pre-merge story branches.

## Acceptance Criteria

(roadmap FORGE-WIN-ENC, recorded 2026-08-13; grill-settled interpretations
2026-08-13, human-ruled: AC1's "single helper" phrasing is satisfied by one
enforced CONVENTION — the ~30 direct sites share no interface, so a shared
wrapper would be forced abstraction; decision 0043 records this. AC3's
forcing mechanism corrected: PYTHONIOENCODING only covers stdio, so the CI
net forces the LOCALE instead.)

1. One shared decode CONVENTION for captured child output, classified by
   consumer (sol-xhigh refinement of the earlier blanket-replace ruling):
   DIAGNOSTIC captures (doctor's run_quiet, human-facing prints) decode UTF-8
   with `errors="replace"`; MACHINE-CONSUMED captures decode strictly —
   git path output keeps filesystem semantics (bytes or surrogateescape:
   stages path/digest authority, quickfix scope enforcement, pr_ready
   freshness paths), JSON protocol output (gh, merge-stage roadmap) decodes
   strict UTF-8 and fails loudly. No locale-default `text=True` capture
   remains in `factory/scripts/**`; check_encoding_hygiene reports zero
   violations.
2. Text I/O is explicit across ALL text boundaries: every
   `read_text`/`write_text`/text-mode `open`/`Path.open` append, all six
   text temp-log handles, and stdin (hook + the four recorders read strict
   UTF-8) name `encoding="utf-8"` — strict for evidence/plans/specs/
   manifests, `errors="replace"` only for human-display captures and worker
   logs; byte-exact digest paths stay bytes. check_encoding_hygiene
   validates the VALUE, not presence: `encoding` must literally be "utf-8"
   and `errors="replace"` only at allowlisted diagnostic sites; it covers
   subprocess kwargs, open/Path.open, tempfile text constructors, and
   sys.stdin reads. Existing nonconforming replacement reads
   (check_dual_runtime canon reads, upgrade's indexed-symlink read) are
   reconciled or added to the documented exception list.
3. CI proves the flows under a FORCED non-UTF-8 locale: an ubuntu step with
   `LC_ALL=C` + `PYTHONUTF8=0` (explicit LC_ALL suppresses PEP 538 coercion —
   validated) runs `forge next`, `doctor --fast`, and the standalone
   checkers; the windows-hook-gates selector runs with `PYTHONUTF8` unset.
   Both legs ASSERT the forcing took (sys.flags.utf8_mode == 0 and a
   non-UTF-8 `locale.getpreferredencoding(False)`) so a future coercion-rule
   change cannot false-green, and the Windows delegation E2E's success path
   has the fake worker emit a non-cp1252 glyph that must round-trip into the
   captured handoff. All exit clean.
4. Vendored clients receive the hardening (existing init/adopt/upgrade
   propagation tests cover the touched scripts).

## Technical Approach

- **Per-site explicit args, not a mega-helper.** The exploration confirmed
  the direct subprocess sites do not share an interface (separate streams,
  cwd, timeouts, byte modes), so the sweep adds `encoding="utf-8",
  errors="replace"` per capture site; `run_quiet` gains it once for its 15
  doctor call sites. Byte-mode sites (`pr_ready.py:348`, `doctor.py:283`,
  `upgrade.py:159/314/324/355`) are exempt by mode.
- **File I/O split by class**: human-display and log writes get
  `encoding="utf-8", errors="replace"` only where a write can carry
  arbitrary worker output (delegate temp logs); everything else —
  plan/spec/decision markdown, evidence JSON/JSONL, manifests — gets strict
  `encoding="utf-8"` (fail loudly on corruption, per 0009/0025).
- **Worker-output contract** (sol-xhigh correction: a child does NOT
  inherit a parent handle's Python-level encoding — that only governs the
  parent's reads): the six text temp-log handles become
  `encoding="utf-8", errors="replace"` for the PARENT's read-back, and the
  CHILD side is contracted to UTF-8 by setting `PYTHONUTF8=1` in the spawned
  process env (delegate's companion env, stages' runner envs) — non-Python
  children are unaffected and their output degrades via replace.
- **Regression net**: new `factory/scripts/check_encoding_hygiene.py` —
  AST-based (not regex), VALUE-validating: flags (a) `subprocess` text
  captures whose `encoding` is absent or not the literal "utf-8", (b)
  `read_text`/`write_text`/text `open()`/`Path.open` (incl. append modes)
  without `encoding="utf-8"`, (c) `tempfile.TemporaryFile`/
  `NamedTemporaryFile` text modes without it, (d) `sys.stdin` reads outside
  the blessed strict-UTF-8 helper, and (e) `errors="replace"` anywhere
  outside the allowlisted diagnostic sites. Explicit allowlist carries the
  byte-exact DO-NOT list and the documented exceptions. Wired into the
  scaffold-check workflow beside the other checkers (self-testing in
  test_gates.py). AST beats regex: bytes-mode `open(p,"rb")` and `dir_fd`
  idioms must not false-positive.
- **CI proof (grill-corrected mechanism)**: `PYTHONIOENCODING` covers stdio
  only — it cannot exercise the file-I/O and subprocess locale defaults this
  story fixes. The honest forcing function is the LOCALE: an ubuntu
  scaffold-check step exports `LC_ALL=C PYTHONUTF8=0` (ASCII locale — any
  non-ASCII default-decode fails loudly) and runs `forge.py next`,
  `doctor --fast`, and the four standalone checkers; the windows-hook-gates
  selector runs with `PYTHONUTF8` explicitly unset so the runner's real ANSI
  code page applies to the delegation E2E.
- **Fold-in**: the windows-zero-setup spec's decomposition section gains
  story 5 (this story) — canon bookkeeping travels with ENC-2's docs task
  instead of a separate vacuous window.

## Decisions

- NEW: `0043-explicit-io-encoding-convention` (record before decomposition):
  every text-mode boundary in harness scripts names its encoding; UTF-8
  everywhere; `errors="replace"` only for human-display captures/logs; strict
  UTF-8 for evidence and canon; byte paths stay bytes; enforcement lives in
  check_encoding_hygiene. The roadmap AC's "single helper" phrasing is
  satisfied by this enforced convention (human-ruled at the plan grill,
  2026-08-13): the direct call sites share no interface, so a shared wrapper
  would be forced abstraction. Rejected: mega-helper wrapping all subprocess
  shapes; global reconfigure-only (PR #101's belt covers stdout/stderr, not
  file/subprocess boundaries); re-exec under PYTHONUTF8=1 at import (fixes
  everything in one line but double-starts every process and surprises
  embedders/pytest); locale-respecting I/O (the harness's artifacts are repo
  files shared across machines — the repo is UTF-8, not the console).
- No other new decisions; 0040/0042 attested unchanged.

## Surface Impact

| Surface | Class | Note |
|---|---|---|
| Runtime behavior | Changed | all text boundaries decode/encode UTF-8 explicitly; failures on undecodable child output become '?' replacements in displays, loud errors in evidence reads |
| API | N-A | — |
| Data/schema | Unchanged | evidence bytes were already UTF-8 on healthy machines; corrupt-locale writes can no longer occur |
| CLI/ops | Changed | new check_encoding_hygiene structural gate |
| Deps | Unchanged | stdlib only |
| Docs | Changed | docs/windows.md encoding note; spec decomposition gains story 5 |
| Tests | Changed | hygiene-check self-tests; cp1252 CI steps |

## Task Decomposition

(JIT contracts per 0032; sequential.)

1. **ENC-1 sweep + hygiene gate** — `run_quiet` encoding; per-site subprocess
   sweep (inventory §1 minus byte-mode exemptions); file I/O sweep (inventory
   §2, strict UTF-8; replace only for delegate temp logs §3); NEW
   check_encoding_hygiene.py (AST, allowlist for §5) + self-tests; decision
   0043. Scope: `factory/scripts/**`, `factory/tests/test_gates.py`,
   `docs/decisions/0043-*.md`.
2. **ENC-2 CI proof + docs** — locale-forced steps in factory-scaffold.yml
   (ubuntu: LC_ALL=C + PYTHONUTF8=0; windows: PYTHONUTF8 unset); docs/windows.md encoding section; spec
   decomposition story-5 line; propagation confirmation.
   Scope: `.github/workflows/factory-scaffold.yml`, `docs/windows.md`,
   `docs/specs/windows-zero-setup.md`, `factory/tests/test_gates.py`.

## Risks

- **Rewrite-regression class (recorded lesson)**: ~130 mechanical edits in
  one stage invite silent drops. Mitigations: the hygiene check itself defines
  done (zero violations = the sweep is complete); full suite green; review
  focuses on the §5 DO-NOT list (any `errors="replace"` on a digest-adjacent
  read is a blocking finding).
- **Python 3.11/3.13 divergence (recorded lesson)**: any test faking
  encodings must not construct bare `Path()` under a patched os.name; prefer
  real-encoding tests (`PYTHONIOENCODING` subprocess probes).
- **Hygiene-check false positives** on dynamic call patterns: AST + explicit
  allowlist; the check is advisory-red with named fix text, not a silent gag.
- **False-green CI legs**: both legs assert the forcing took effect at
  runtime (utf8_mode off + non-UTF-8 preferred encoding); the Windows E2E's
  success path carries a non-cp1252 glyph through the worker handoff.
- **Locale-forcing step flaking on runner defaults**: `LC_ALL=C` is present
  on every ubuntu runner (no locale generation needed); the Windows job needs
  only `PYTHONUTF8` unset (the ANSI code page is the default). No `chcp`
  (console-host dependent), no `PYTHONIOENCODING` (stdio-only, and PR #101's
  reconfigure overrides it anyway).
- **Decision-number collision** (0043): another session minted 0041 in
  parallel last week; renumber-on-collision at merge is the established
  repair (0041→0042 precedent).

## Verify Plan

- `verify.py` with pinned `.envrc` commands; full POSIX suite green.
- check_encoding_hygiene reports zero violations on the swept tree; its
  self-tests prove it catches a seeded violation and passes the allowlist.
- factory-scaffold LC_ALL=C step green on ubuntu; windows-hook-gates (incl.
  the delegation E2E) green with PYTHONUTF8 unset — the real proof.
- No pr_ready before windows CI is green (WIN-2/WIN-3 lesson).
