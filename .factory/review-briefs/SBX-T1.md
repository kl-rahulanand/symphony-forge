# Plan-contract review brief — SBX-T1

For each contract, emit a verdict — implemented | partial | missing — with file:line evidence, recorded as contract_verdicts in the quality artifact. Then review the diff normally; the contract check does not replace the quality/performance/security lenses.

## Task SBX-T1

### Plan contracts

- **SBX-C1**
  - Source: plans/active/FORGE-WIN-SBX-workers-run-sandboxed-by-default.md#technical-approach
  - Statement: The vendored .codex/config.toml defaults sandbox_mode to workspace-write with a comment documenting the deliberate-edit escape hatch and pointing at decision 0041; forge upgrade restores the default.
- **SBX-C2**
  - Source: plans/active/FORGE-WIN-SBX-workers-run-sandboxed-by-default.md#technical-approach
  - Statement: check_vendor_integrity hashes .codex/hooks.json, every manifest writer agrees, and tests prove both drift detection and re-vendor repair.
- **SBX-C3**
  - Source: plans/active/FORGE-WIN-SBX-workers-run-sandboxed-by-default.md#scope--non-goals
  - Statement: config.toml is deliberately not hashed, and decision 0041 records the flip, the escape-hatch doctrine, and the honest statement that delegation already ran workspace-write.
- **SBX-C4**
  - Source: plans/active/FORGE-WIN-SBX-workers-run-sandboxed-by-default.md#verify-plan
  - Statement: A real delegation passes end to end under the companion's workspace-write mapping, recorded in the testing artifact.

### Reviewer focus

The surface-list agreement is the trap: if the hashed list is defined in more than one place, all writers and the checker must agree or every clean client fails integrity. The config comment must not promise enforcement the mechanism lacks (visibility, not prevention). The flip must not touch delegation argv or any other config key.
