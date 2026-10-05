# WI-033 — Repair the stale CI wheel filename

Status: complete
Opened / updated: 2026-10-06

## Request and scope

User requested consistent CodeBearing naming and a defensible comparison with
Aider, Serena, code-graph MCP servers and existing assistant capabilities.
This record covers: repair the stale ci wheel filename.

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
Replaced the obsolete 0.8.0 filename with 0.10.0, synchronized with
pyproject.toml and codebearing.__version__. Keep the CI filename in the release
checklist. No workflow permissions, triggers, dependency pins or hosts changed.
Local clean-wheel run passed; hosted CI is not claimed green.

## Verification

CI wheel filename matches pyproject source version 0.10.0 (checked with tomllib).
The exact local checker command passed clean install/CLI/hybrid/configuration/
setup/six-tool stdio/cache with JS/TS. Hosted GitHub Actions has not been run or
observed in this session. No new full-suite rerun needed for the YAML filename.

## Handoff / completion

Complete: .github/workflows/checks.yml points at the current wheel. Release
checklist documents synchronizing the filename. Existing F-046/F-047 paths apply;
source namespace commit 903a0b4 supplies the package used by this CI command.

## Git trace

Predecessor b216c0e. Use git log --oneline -- this record for introducing commits.
