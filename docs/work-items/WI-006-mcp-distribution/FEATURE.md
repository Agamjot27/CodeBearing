# WI-006 — Installable MCP server and assistant onboarding

Status: complete (local/source distribution; public PyPI publication pending)
Opened: 2026-10-04

## Request and scope

Ship the existing tools for coding assistant platforms with minimal setup. Add a
distinct launcher, generated client configurations, a model-free connection check,
clean wheel installation validation, and user/release documentation. No cloud
service, new retrieval engine, host-setting mutation, or dashboard. Public PyPI
publication needs a package-owner publishing identity; none is configured here.

## Starting state and execution path

Read AGENTS.md, HANDOVER.md, D-010/D-011/D-015 and F-016/F-017/F-024. Clean Git
status. Existing pyproject defines diffcontext-lab 0.1.0 and the diffcontext CLI.
MCP SDK 2.3.0 is installed in .venv, but that environment has no pip module;
the global Python installation provides pip. Six existing read-only tools work.

## Implementation and decisions

D-016; F-025/F-026. New connect.py launcher shares create_server and the unchanged
RepositoryService. It prints absolute interpreter/repository config for Claude
Code, Cursor and Codex, without touching host settings. Separate SDK client checks
tool discovery and a search request. Keep one repository per server launch.

## Attempts and outcomes

- Inspected package and MCP contracts. Selected an installed launcher and generated
  configuration to remove development-machine paths from user instructions.
- Initial sandbox verification could not open Windows subprocess pipes, and pip
  could not write its temporary tracker. Re-ran the same checks with approved
  shell access; no application workaround or permission change was introduced.
- Built 0.2.0 wheel and verified clean installation, installed CLI/config generation
  and actual MCP discovery/search outside the importable checkout root.
- Read-only subagent review found virtualenv executable symlink dereferencing and
  non-BMP JSON escapes incompatible with TOML. Preserved interpreter path, emitted
  TOML Unicode scalars, added regressions and Windows/Linux CI distribution checks.
  Rebuilt and rechecked the final artifact after those fixes; it passed.

## Verification

Full MCP-enabled suite passed 68 tests before final portability fixes. All seven
connection tests passed afterward, including symlink and non-BMP regressions.
Both initial and rebuilt final wheel checks passed. Installed
0.2.0 wheel in existing .venv and verified the installed launcher reports connected,
six tools and no warnings on examples/refunds. No real assistant session was tested.

## Handoff / completion

Packaging/onboarding implemented and validated. Public publication needs publisher
identity/name verification; actual assistant integration needs a chosen host and
project. No model calls, provider spend or user settings changes. The checked
wheel is local under dist/ and excluded from Git. MCP CI now checks Linux/Windows;
those remote jobs have not been observed running during local verification.

## Git trace

Use `git log --oneline -- docs/work-items/WI-006-mcp-distribution/FEATURE.md`.
