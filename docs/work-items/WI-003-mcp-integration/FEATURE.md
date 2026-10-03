# WI-003 — Read-only MCP integration

Status: complete
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
5. Added the optional SDK extra, `serve`, five annotated tools, and protocol tests.
   In-memory checks passed, but expected domain errors produced unexpected-error
   tracebacks. Converted ValueError/OSError/SQLite failures into SDK ToolError;
   errors now retain actionable messages and subsequent valid calls succeed.
6. The first real stdio test failed at Windows asyncio pipe creation with WinError
   5 inside the sandbox. Reran unchanged transport with approved pipe access:
   all four protocol tests passed, including deleted-symbol context and recovery.
7. Installed the editable project extra in `.venv`. Added connection instructions,
   a separate CI job requiring MCP, and `examples/mcp_client.py`. Its real subprocess
   demonstration discovered tools, selected refund_total, and compiled cited code.
   Launching the installed module outside the project directory also succeeded.
8. Final full suite: 37/37 passed with SDK (24.010s); dependency-free environment:
   33 passed, four MCP skips (20.031s). Both existing synthetic smoke cases passed.

## Verification

Passed: 4 service checks for core parity, read-only SQL/method rejection, absent DB
non-creation, confirmed/fresh filtering, unchanged DB bytes, and bounds.
Passed: SDK tool discovery/calls, bounds/actionable errors/recovery, stdio transport,
revision context, fresh/confirmed filtering, unchanged database bytes, client demo,
and outside-project module launch. Local Python version is 3.13.9 on Windows;
configured Linux/Python 3.11 CI has not been observed remotely. No real coding-agent
outcome claim or independent benchmark yet.

## Handoff / completion

Service/read-only memory and MCP adapter complete. D-010/D-011, F-016/F-017 and
related existing CLI flows are synchronized; HANDOVER/README/ROADMAP updated.
Next: a real assistant session and controlled outcome evaluation. Keep memory
review developer-controlled, inspect omitted/unresolved evidence, and do not claim
the transport demonstration proves coding-task success or injection resistance.

## Git trace

Shared service/read-only prerequisite: `f52f667`.
Transport: `git log --oneline -- diffcontext/mcp_server.py`.
Full record: `git log --oneline -- docs/work-items/WI-003-mcp-integration/FEATURE.md`.
