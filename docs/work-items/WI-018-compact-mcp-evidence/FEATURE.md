# WI-018 — Bounded agent-facing context and warning presentation

Status: implementation verified; harder trial running
Opened: 2026-10-04

## Scope / observed problem

WI-017 assisted trial reports truncated context and index_warnings partial coverage.
The user authorizes implementation and harder fresh-session trials with subagents.
Measure actual MCP payload duplication/warning volume before choosing a format.
Preserve complete CLI/service evidence and disclose omissions rather than hiding
limits. Keep BookMyShow unchanged. Parent owns docs, verification and commits;
subagents own presentation implementation/tests and isolated harder-trial design.

## Execution / plan

Measure RepositoryService investigation → mcp_server tool response; introduce
bounded agent-facing presentation if warranted; verify warning counts, relevant
gaps, source inclusion and full-report compatibility over real stdio. Rebuild the
installed tool and rerun a harder isolated paired task in user-authorized chats.
Record exact design and evidence once known; no unobserved performance claim.

## Attempts / handoff

Investigation active. Existing mcp_server.py reports modified in Git without a
content diff; preserve unrelated changes. No original project source edits.

## Measurements / selected approach

Frozen original BookMyShow report saved locally: JSON 292449 bytes, canonical
context.text 5269 bytes, 521 warnings, five trace events, partial/index_warnings.
Separate backend-copy report measured by subagent: 214303 bytes, 193 warnings,
14 trace events, 4200 canonical source bytes. SDK dictionary conversion duplicates
JSON into text and structured content. Keep both channels for host compatibility.
D-027 chooses MCP-only warning sampling/counts and equal-field trace references;
full detail opt-in, no core retrieval/status change or arbitrary critical-gap loss.
Subagents implementing and testing this scope. Harder trial preparation active.

## Implementation and verification

presentation.py:present_report defaults to compact, warning limit eight with exact
counts and capability caveats, equal trace fields become explicit references.
Context and verification serialize before long search metadata. All six MCP tools
accept compact/full; CLI/service reports and critical gaps/status are unchanged.
Frozen structured JSON: 292449 → 40259 bytes (86.23% smaller); SDK both-channel
response: 649084 → 101729 bytes (84.33% smaller). This measures representation size,
not token/cost or coding-quality improvement. Source equality verified.

Full suite: 160 tests passed in 63.124s. A final serialization-order regression was
then added; all six presentation tests pass. Clean 0.7.0 wheel check passes install,
outside-checkout CLI, configs/setup, six-tool stdio search and cache reuse. Installed
0.7.0 and confirmed real trial-copy transport. No original BookMyShow changes.

Installed upgrade initially failed on Windows locked Scripts directory. Identified
only Python processes running uv/tools/codebearing with -m diffcontext.connect,
stopped those read-only MCP processes and retried successfully. Parent-child exit
race produced a missing-PID error on first stop; remaining scoped processes were
stopped and install completed. No Codex app or unrelated process stopped. Existing
host sessions need reconnect/restart to load the upgraded MCP server.

Current work: harder paired booking trial WI-019 running in fresh sessions.
D-027/F-037 documents presentation; full-detail calls recapture current evidence.
