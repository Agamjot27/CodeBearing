# WI-031 — Rename the canonical Python package

Status: complete
Opened / updated: 2026-10-06

## Request and scope

User requested consistent CodeBearing naming and a defensible comparison with
Aider, Serena, code-graph MCP servers and existing assistant capabilities.
This record covers: rename the canonical python package.

## Starting state and execution path

Baseline b216c0e. Package/imports/launcher module still diffcontext; distribution
and public commands CodeBearing. F-045/F-046 describe setup and wheel checks.
CI checks an obsolete 0.8.0 wheel although released source is 0.9.0.
No competing-tool performance benchmark has been run.

## Implementation and decisions

Scoped before edits. Preserve historical work items and model-result fingerprints.
Current package/docs may change; existing user projects and installed tools will
not be changed. D-038 (namespace) / D-039 (comparison) apply as relevant.

## Attempts and outcomes

Read current package, tests, wheel checker and primary competitor documentation.
Renamed the package, all executable imports, tests and current guides; removed
legacy console aliases. Version 0.10.0 signals the namespace/configuration change.
Existing data paths and historical work items/result fingerprints are preserved.
Source suite passed all 188 tests in 74.560s, including MCP and JS/TS checks.

Initial sandboxed pip build failed temporary-directory permissions. Approved
build succeeded but contained stale build/lib/diffcontext artifacts. The strengthened
wheel checker rejected that wheel before installation. Verified the absolute
workspace build path, removed only derived build/ output with PowerShell, and
rebuilt. New wheel is 72,344 bytes; SHA256
e8fcc9a8955c749a648ee5b45953086dee23012aab81de0131c362b53de9f6c1.
Clean install/stdio/cache verification passed. This demonstrates why a source
rename alone was insufficient; no old package shim is intentionally shipped.

## Verification

188 tests passed in 74.560s. Clean wheel checker passed outside-checkout CLI,
hybrid task, all three generated client configurations, setup, six-tool stdio
search/discovery and persistent cache reuse with optional JS/TS dependencies.
Wheel member/entry-point review confirms no diffcontext namespace or legacy
commands shipped. python -m codebearing --help uses the public CodeBearing entry.
Current guide links (100 checked at initial pass) resolve. README excerpt and
514 estimated-token count are unchanged under the renamed compiler.
No global environment, original project or user MCP configuration was changed.

## Handoff / completion

Complete; docs/NAMING.md explains upgrade/reconfigure and close/rename/reopen
for the registered outer checkout. Only the internal source package was moved.
Storage remains .diffcontext for compatibility. Historical records/hashes retained.
D-038/F-047 synchronized; existing installed 0.9.0 remains unchanged.

## Git trace

Predecessor b216c0e. Use git log --oneline -- this record for introducing commits.
