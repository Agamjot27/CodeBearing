# WI-015 — Windows setup and TypeScript indexing crash

Status: resolved (original trampoline error not reproduced)
Opened: 2026-10-04

## Discovery and reproduction

User reports uv trampoline canonicalization failure in BookMyShow. Launcher help
works when retried; original trampoline error has not been reproduced. Setup then
fails with a grouped MCP connection error. Direct indexing exits with a Windows
access violation in typescript.py:text(), called by _call_facts(). Per-file parsing
isolates backend/src/config/redis.ts. No application code or secrets are copied.

## Affected execution path

onboarding.main → connect.check_connection → MCP search → build_index →
typescript._parse_unit → _call_facts → _File.text. No settings written on failure.

## Investigation and attempts

Installed launcher and interpreter exist. Direct faulthandler establishes native
parser failure, rather than a missing package. Investigating syntax tree lifetime
and binding behavior; root cause not yet established. Related upstream Markdown
report is a different grammar and does not establish the cause of this crash.

## Verification / handoff

Retry real project setup after fixing indexing; retain regression reproducer.
No host usage or model outcome yet. See Git history for this record.

## Confirmed workaround

Keeping the Tree alive did not help and was reverted. Testing tree-sitter 0.25.2
under the same Python 3.13 indexes the whole project successfully (316 symbols).
Pin the prior binding and release 0.6.1 (D-024/F-034); exact upstream defect is
unproven. First downgrade attempt encountered a loaded DLL; retry after diagnostic
process exit succeeded. Original uv trampoline error remains unreproduced.

## Resolution verification

13 TypeScript/JavaScript, four cache CLI/MCP and 13 index-store tests pass (30).
Built and installed codebearing 0.6.1 wheel with parser 0.25.2. The installed
`codebearing setup --client codex` completes in BookMyShow, verifies six MCP tools
and writes its project .codex/config.toml. No application source was modified.
Codex must still reload/approve the project server; no actual model task was run.
The full 155-test suite was not repeated for this dependency-only patch.
Reinstallation refreshed the uv launchers; no canonicalization error recurred.
