# Read-only exploration brief — planning FORGE-WIN-SBX (no writes)

Story: delegated workers should run workspace-write sandboxed in every
client instead of danger-full-access, verified against a real delegation.
Acceptance criteria: (1) vendored .codex/config.toml defaults to
workspace-write; a real delegation passes end to end under it; the escape
hatch for genuinely-broader tasks is documented and ledgered;
(2) check_vendor_integrity hashes .codex/hooks.json; a decision record
covers the default flip.

Questions — report file:line evidence for each:

1. Where is the worker sandbox mode currently decided? Find every place
   danger-full-access (or an equivalent full-access mode) is set or
   implied: the vendored .codex/config.toml, the companion launch argv in
   factory/scripts/forge_cli/delegate.py, the codex-companion.mjs runtime
   (installed plugin), and any per-run overrides.

2. What exactly does the vendoring pipeline copy and hash today? List the
   files scaffold.py/adopt/upgrade vendor for .codex/, and what
   constitution/VENDOR_MANIFEST.json + check_vendor_integrity.py
   currently cover — specifically whether .codex/config.toml and
   .codex/hooks.json are hashed, and where the manifest is generated.

3. If config.toml flips to workspace-write, what breaks? Trace what a
   delegated write run touches outside the workspace: git control dir
   operations (refs, protected decomposition twin under
   git_control_dir), .factory writes, tmp dirs, uv/uvx caches, network.
   Which of these does the codex sandbox 'workspace-write' profile allow
   or deny, per the Codex CLI docs or the plugin's handling?

4. What would a ledgered escape hatch look like consistent with existing
   machinery — is there precedent (lite/degraded windows, delegation
   argv flags) for a per-task broader-sandbox declaration, and where
   would delegate.py carry it?

5. Which existing tests pin .codex vendoring, config content, or
   check_vendor_integrity behavior that this story must extend?
