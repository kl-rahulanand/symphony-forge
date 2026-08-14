---
status: proposed
confirmed_by: ""
date: 2026-08-13
stories: [FORGE-WIN-ENC]
---

# Explicit I/O Encoding Convention

## Context

PR #101 proved the encoding bug class on a default Windows cp1252 console and
fixed the stdout/stderr half. Read-only exploration plus a sol-xhigh
validation pass inventoried the rest: ~30 locale-decoding subprocess capture
sites, ~100 default-encoding text file I/O sites, six locale-encoded text
temp-log handles, and locale-decoded stdin in the hook reader and the four
recorders. The harness's artifacts are repo files shared across machines —
the repo is UTF-8, not the console. Launchers export PYTHONUTF8=1 (WIN-2),
but direct `python factory/scripts/<script>.py` invocations (CI does this in
four workflows) and imports into already-running hosts bypass it, and no
global lever covers the parent's decode of non-Python child output.

## Decision

Every text-mode I/O boundary in `factory/scripts/**` names its encoding
explicitly: UTF-8 everywhere. Error policy is classified by consumer —
`errors="replace"` ONLY for human-display captures and worker-log read-back;
strict UTF-8 (fail loudly) for evidence, plans, specs, manifests, JSON
protocol output, and stdin; git path output keeps filesystem semantics
(bytes or UTF-8 with `surrogateescape`); byte-exact digest paths stay bytes.
Stdin is read through a strict UTF-8 `TextIOWrapper` over `sys.stdin.buffer`.
Spawned Python children are contracted to UTF-8 output via `PYTHONUTF8=1` in
their env; the parent temp-handle encoding does not configure the child. The
convention is enforced by `check_encoding_hygiene.py` (AST-based,
value-validating, allowlisted DO-NOT list) — the roadmap AC's "single helper"
phrasing is satisfied by this enforced convention: the call sites share no
interface, so a shared wrapper would be forced abstraction (human-ruled at
the plan grill, 2026-08-13).

## Consequences

- New structural gate in the scaffold-check workflow; zero violations defines
  sweep completion and blocks regression.
- Undecodable child output degrades to `?` in diagnostics instead of
  aborting; corrupt evidence refuses loudly instead of decoding silently
  (0009/0025 preserved).
- Replacement decoding is limited to the checker's documented file-and-line
  allowlist: console reconfiguration, diagnostic captures, and the six
  worker-log handles. Indexed symlink targets and git path authority use
  lossless `surrogateescape`, not replacement.
- Rejected: a mega-helper wrapping all subprocess shapes; global
  reconfigure-only (stdio-only); re-exec under PYTHONUTF8=1 (double-starts
  every process, breaks imported hosts); locale-respecting I/O.
- Workflow-inline Python hardening parked as D-0026 with a revisit trigger.
