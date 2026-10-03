# WI-003 — Read-only MCP integration

Status: in progress
Opened / updated: 2026-10-03 (Asia/Calcutta)

## Request and scope

Expose searches, explicit/revision impact, context compilation, change localization,
and confirmed fresh lessons to an MCP client. Bind each server to one configured
repository. Share orchestration with the CLI; do not expose lesson mutations.
Acceptance: SDK client initializes a real stdio subprocess, discovers tools,
receives structured results, exercises failure recovery, and verifies no memory
writes. Provide runnable connection instructions and CI coverage.

## Starting state and execution path

Baseline CLI `cli.py:main()` orchestrates core calls and creates/opens Memory even
for reads. Existing Memory initialization may create schema and commit; that is not
appropriate for tools advertised read-only. Existing context and changes modules
already implement retrieval/packing and should remain the implementation authority.
Latest completed code: `bbed3ae` (WI-002); workspace initially clean.

## Implementation and decisions

First introduce shared repository-bound service methods and true SQLite read-only
access. Then wrap those methods with the official SDK's stdio transport. SDK chosen
after checking official docs and PyPI: version 2.3.0, installed only in `.venv`.
MCP remains an optional extra so the local core needs no SDK dependencies.

## Attempts and outcomes

1. Inspected instructions, handover, CLI, memory, core, CI, and current SDK docs.
2. `.venv` creation produced an interpreter but ensurepip failed in the restricted
   environment. Used existing pip's `--python .venv` installation interface rather
   than modifying global packages. SDK 2.3.0 installation completed successfully.
3. Added RepositoryService and mode=ro/query_only Memory reads; refactored CLI
   orchestration. The first run exposed a test expectation mismatch (missing
   read-only DB raises sqlite3.OperationalError, not ValueError) and inherited
   fixture tests duplicated discovery. Corrected the expected exception and reused
   fixture setup without inheriting/importing test classes into discovery.
4. All four focused service checks pass. The earlier full run's existing checks
   passed; the final full suite will be rerun with transport coverage.

## Verification

Passed: 4 service checks for core parity, read-only SQL/method rejection, absent DB
non-creation, confirmed/fresh filtering, unchanged DB bytes, and bounds.
Pending: SDK tool discovery/calls, bounds/errors, stdio transport,
revision context and absence of writes. No real coding-agent outcome claim yet.

## Handoff / completion

Service/read-only memory complete; next the MCP adapter/client test.
Update F-005/F-007/F-015 and add the actual new request flows as they are completed.

## Git trace

`git log --oneline -- docs/work-items/WI-003-mcp-integration/FEATURE.md`.
