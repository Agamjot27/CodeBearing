# WI-016 — CodeBearing absent from desktop MCP list

Status: configured; desktop verification pending
Opened: 2026-10-04

## Discovery

User screenshot shows BookMyShow selected on the new-chat screen, but the MCP list
contains only bundled servers. CLI `mcp get codebearing` reads an enabled project
entry; saved project path matches, interpreter exists, project trust is trusted.
User-level settings do not contain CodeBearing. CLI configuration discovery does
not establish that the desktop app loaded or connected it. Exact UI cause unknown.

## Execution path and approach

Project .codex/config.toml → Codex project configuration → MCP launch. Add the same
verified command as a user-level server using `codex mcp add`, preserving unrelated
settings. This is an individual host workaround, not a change to setup's default
project scope. The global entry remains bound to BookMyShow; it is not a repository
switcher. Desktop restart/real tool call remains user-side verification.

## Verification

Before changing settings, inspect only the specific server and trust fields; no
credentials logged. Test the pinned interpreter/server. Record final configuration
registration and pending desktop verification below.

## Outcome

The exact saved interpreter command passes the real-project six-tool MCP search
check. `codex mcp add codebearing -- <verified-python> -m diffcontext.connect
--repo <BookMyShow>` successfully registers a global server. `mcp get` confirms
it is enabled. No other servers or application source were changed. User must
fully quit/reopen the app and verify a tool call. Do not claim the screenshot's
absence was conclusively caused by scope or that desktop loading is now verified.
D-025/F-035. No product code change or new automated tests in this host repair.
