# WI-029 — Package, validate and install CodeBearing 0.9.0

Status: validated/installed; push pending
Opened / updated: 2026-10-05

## Request and scope

Finish the authorized four-phase work with a usable Git-distributed MCP release.
Synchronize package versions, validate an actual clean wheel away from the source
checkout, update the existing user's installed tool and push meaningful commits.
No public PyPI publication or invented recorded video/model superiority claim.

## Starting state and execution path

Installed release0.8.0. New retrieval, exception evidence, measured trial tooling,
memory demo and quickstart are implemented. Full188 tests pass after compiler fix.
Existing packaging flow: pip wheel → scripts/check_wheel.py isolated environment
→ installed CLI/setup → six-tool stdio MCP smoke → cache reuse. Existing configured
CodeBearing interpreter launches diffcontext.connect bound to BookMyShow.

## Implementation and decisions

Implemented: bumped pyproject.toml and diffcontext/__init__.py together to0.9.0, updated
current release docs, build/check/install wheel without changing project config.
Retain six read-only MCP tools and optional pinned language adapters. Release is
Git-installable; independent quality validation remains research, not a release
metric. Existing D-023/D-035 packaging/onboarding scope applies.

## Attempts and outcomes — update during work

Scoped before version edits. Built dist/codebearing-0.9.0-py3-none-any.whl,
68,821 bytes, SHA256268bb1d01e487290acfa1f1b99e9b7cefcc10b3f10322d2ea5763c8972faea2c.
Clean wheel checker passed; global install verified; push pending.38 public local links
resolve; six investigation fixtures and TypeScript budget fixtures ran successfully.
Stopped only the exact prior read-only CodeBearing connector tree rooted atPID1612
for Windows interpreter locks; its two descendants were included. No Codex app or
unrelated processes stopped. uv tool install --force installed0.9.0 with existing
mcp/TypeScript pinned extras. User assistant configuration was not rewritten.

## Verification

Full188 tests pass in81.338s after compiler repair; focused parser/packing checks,
separately labeled retry8/8, six investigation cases and both TS budgets pass.
Clean checker passed installed CLI/hybrid task, project setup/client configuration,
six-tool stdio discovery/search and persistent cache reuse outside checkout.
Actual configured interpreter `-I` imports installed site-packages version0.9.0;
user codebearing --help succeeds; installed connect --check on public TS fixture
returns connected and all six tools with existing static-call warnings disclosed.
Wheel SHA256 independently rechecked. No model calls or original project edits
during packaging. Existing chats require reconnect/new chat after the scoped stop.

## Handoff / completion

Root HANDOVER/FLOW synchronized (F-046). Do not read
credentials, overwrite user MCP entries or stop unrelated application processes.
If Windows locks the interpreter, stop only the exact old read-only CodeBearing
connector process, then verify the configured interpreter's installed version.

## Git trace

Predecessors e6b7fbb retrieval,9b00438 memory demo,7ffc2f1 measured trials,
65aa91b exception evidence. Use git log --oneline -- this record for release history.
