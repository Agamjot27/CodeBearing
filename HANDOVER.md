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

WI-025 complete: repeated smaller-model fixed-packet trials with actual Codex
CLI usage. Read docs/work-items/WI-025-observed-codex-trials/FEATURE.md first.
Parent owns diffcontext/codex_trials.py, evals/codex_bench.py, tests/test_codex_trials.py
and processes.py env parameter. Six focused tests pass. Two pilot calls excluded;
32/32 matrix calls scored, no tools/operational/budget exclusions. gpt6luna
lexical7/8/hybrid5/8;gpt5.6luna lexical8/8/hybrid7/8. No advantage established.
Public docs/demos/SMALL_MODEL_PACKET_TRIALS.md/JSON; D-034/F-043.
CLI default temperature/no enforced generation cap are explicit; output allowance
is postchecked. Model ID is requested, not provider-attested; USD unknown.

WI-026 memory demo implemented and 3 tests pass: authored analogy to actual WI-020
test gap, proposal excluded, explicit operator review, fresh-process retrieval and
stale exclusion. scripts/demo_memory.py; docs/demos/MEMORY_CONTINUITY.md;
docs/work-items/WI-026-memory-continuity-demo/FEATURE.md. D-033/F-042 document actual
storage/retrieval execution.
Does not attest human approval or improved later model behavior.

WI-027 quickstart/demo/README polish implemented; docs/work-items/WI-027-v1-user-guide/FEATURE.md.
Final trial links, release wheel/install and push pending. Full suite183 passed
in135.779s before the additional WI-028 exception-declaration repair.
Native recording unavailable; walkthrough/storyboard is not a recorded video.

WI-028 complete: actual matrix exposed omitted local Python exception declaration
when symbol excerpts are used for full-file replacement. Read
docs/work-items/WI-028-python-exception-evidence/BUG.md; context.py now bundles
referenced conservative local exception declarations atomically. Five focused,
nine core and14 investigation checks pass. D-036/F-044. Separate retry-only
post-fix8/8 passes (same-task development checks); full suite188 passes in81.338s.
Original matrix remains unchanged. Public postfix artifact links from trial report.

## Evidence and limits

Four authored coding fixtures; legacy calibration16/16 reference/unchanged,
hybrid28/28. Calibration is model-free. Real paired demos: WI-017 both5/5,
WI-019 both6/6; exploratory requested gpt-6-luna/low WI-020 assisted6/6 versus
control3/6 with process/harness friction. No independent causal or cost claim.
All68 original BookMyShow hashes remained unchanged. Public scoped reports live
in docs/demos; ignored .eval-runs holds local artifacts. Full suite183 passed;
repeat appropriate verification after WI-028 changes.

## Avoid / next concrete action

Finish final guide links/release version, commit meaningful units, build/check/install,
then push. Preserve original projects and existing user-level BookMyShow MCP entry.
Do not read credentials, edit shared dependency junctions, or commit generated
.eval-runs/.test-tmp/.diffcontext files. Temporary trial servers must be removed.
Tree-sitter0.25.2 is pinned:0.26 crashed real redis.ts. Do not upgrade without
real-project regression validation. Graphs miss dynamic/type/runtime wiring.
Text budget excludes JSON and Codex scaffolding; whole-file hashes over-invalidate
lessons. Full-detail reruns are new snapshots. Solver isolation is not a hostile
code sandbox. Relevant check: .\.venv\Scripts\python.exe -m unittest discover -s tests -v.
