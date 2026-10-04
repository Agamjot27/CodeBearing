# Current handover

Updated: 2026-10-05 (Asia/Calcutta). Read after AGENTS.md. Detailed history lives
in Git, DECISIONS.md, FLOW.md and docs/work-items; this is the current snapshot.

## Completed capabilities

CodeBearing is a local context engine/MCP server with six read-only tools; the
coding assistant edits/tests. Python and optional JS/TS syntax indexing, conservative
call/import graph, tracked diff/deleted-source analysis, hybrid retrieval, bounded
whole-source context, confirmed/hash-fresh SQLite lessons and investigation traces
are implemented. CLI setup supports Claude Code, Cursor and Codex. Public repository:
https://github.com/Agamjot27/CodeBearing.git. No PyPI publication, frontend or HTTP API.

0.8.0 wheel/install/setup/stdio/cache checks passed and the user's configured
BookMyShow MCP interpreter reports 0.8.0. Earlier chats may require reconnect.
Latest previously pushed commit b90f79f. CLI reports full; compact MCP bounds
ranking diagnostics while retaining source/IDs/gaps. Total transport is not capped.

## Current authorized work — four final phases

WI-024 retrieval fix implemented: connected complementary evidence now precedes
disconnected vocabulary. Captured Luna query includes total/confirm/transaction
at 2884/3000 estimated text tokens, still partial with 15 omitted nonseeds.
28 focused tests pass. D-032/F-040; docs/work-items/WI-024-connected-task-evidence/BUG.md.

WI-025 in progress: repeated smaller-model fixed-packet trials with actual Codex
CLI usage. Read docs/work-items/WI-025-observed-codex-trials/FEATURE.md first.
Parent owns diffcontext/codex_trials.py, evals/codex_bench.py, tests/test_codex_trials.py
and processes.py env parameter. Six focused tests pass. Pilot lexical/hybrid refund
both pass, no tools, usage observed. Two matched 16-call model matrices are running.
CLI default temperature/no enforced generation cap are explicit; output allowance
is postchecked. Model ID is requested, not provider-attested; USD unknown.

WI-026 memory demo implemented and 3 tests pass: authored analogy to actual WI-020
test gap, proposal excluded, explicit operator review, fresh-process retrieval and
stale exclusion. scripts/demo_memory.py; docs/demos/MEMORY_CONTINUITY.md;
docs/work-items/WI-026-memory-continuity-demo/FEATURE.md. Root flow/decision pending.
Root integration: D-033/F-042 document actual storage/retrieval execution.
Does not attest human approval or improved later model behavior.

WI-027 quickstart/demo/README polish implemented; docs/work-items/WI-027-v1-user-guide/FEATURE.md.
Final trial links, root docs, full suite, release wheel/install and push pending.
Native recording unavailable; walkthrough/storyboard is not a recorded video.

## Evidence and limits

Four authored coding fixtures; legacy calibration16/16 reference/unchanged,
hybrid28/28. Calibration is model-free. Real paired demos: WI-017 both5/5,
WI-019 both6/6; exploratory requested gpt-6-luna/low WI-020 assisted6/6 versus
control3/6 with process/harness friction. No independent causal or cost claim.
All68 original BookMyShow hashes remained unchanged. Public scoped reports live
in docs/demos; ignored .eval-runs holds local artifacts. Full suite167 passed
before latest fixture/presentation changes; final combined suite pending.

## Avoid / next concrete action

Finish WI-025 repeated matrix and aggregate measured usage honestly, integrate
root decisions/flows, commit meaningful units, run combined checks/build/install,
then push. Preserve original projects and existing user-level BookMyShow MCP entry.
Do not read credentials, edit shared dependency junctions, or commit generated
.eval-runs/.test-tmp/.diffcontext files. Temporary trial servers must be removed.
Tree-sitter0.25.2 is pinned:0.26 crashed real redis.ts. Do not upgrade without
real-project regression validation. Graphs miss dynamic/type/runtime wiring.
Text budget excludes JSON and Codex scaffolding; whole-file hashes over-invalidate
lessons. Full-detail reruns are new snapshots. Solver isolation is not a hostile
code sandbox. Relevant check: .\.venv\Scripts\python.exe -m unittest discover -s tests -v.
