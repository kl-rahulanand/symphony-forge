---
name: signal-resolution-is-auto
description: Permission-shaped worker signals are resolved autonomously by the orchestrator; only genuine scope changes go to the human
metadata:
  type: project
---

Delegated workers run with approvals off (`approvalPolicy: never`) and can
only fail or raise a signal. Operator ruling (Ravi, 2026-08-13, during
FORGE-WIN-SBX): keep resolution AUTO — when a worker raises a
blocked/confusion/contradiction signal that is permission- or
sandbox-shaped, the orchestrating session resolves it itself through the
ledgered paths (signal resolve + degraded/lite window when an
orchestrator edit is needed), without pausing for human approval.
Precedent: S-0001-5481 (sandbox refused the worker's `.codex` write) was
resolved via degraded window Q-0058 autonomously.

**Why:** headless delegation cannot prompt, and the ledger (signals +
windows + diffs) already records every exception reviewably — human
latency adds nothing but stall.

**How to apply:** resolve and resume without asking; the human boundary
stays where it always was — plan approval, decision acceptance, and
scope-change signals that alter what a story delivers.
