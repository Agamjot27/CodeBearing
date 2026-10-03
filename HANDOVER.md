# Current handover

Updated: 2026-10-03 (Asia/Calcutta). Read this at each session start, after AGENTS.md.
This is a current-state snapshot; detailed history belongs in Git and work items.

## Objective

Build an independent change-aware context engine and evidence-backed engineering
memory for coding agents. Prove usefulness through controlled evaluations. The
current product is a local Python CLI, not the full planned web application.

## Done

- Python AST symbols and statically resolved call edges: `diffcontext/index.py`.
- Lexical seed search, bounded caller/callee expansion, and whole-excerpt packing:
  `diffcontext/context.py`. Token counts are estimates, not exact tokenizer counts.
- SQLite lesson proposal/review, exact-scope retrieval, evidence/source hash
  freshness checks: `diffcontext/memory.py`.
- CLI: `diffcontext/cli.py`; refund example; 37 regression/protocol tests; 2 synthetic
  retrieval smoke cases; GitHub Actions check configuration.
- Baseline committed and pushed: `fa2dd36` on `main`, remote
  `https://github.com/Agamjot27/DiffContext.git`.
- Engineering decisions D-001–D-006 and execution flows F-001–F-012 documented.
- Continuity workflow: handover, work-item templates, session-start instructions,
  and non-obvious comment requirements. D-007 records this addition.
- Captured-source index adapter: `f09d471`, documented by D-008.
- Git revision localization: `changes.py` maps tracked modifications, additions,
  and deletions in old/current graphs; restores surviving old callers; labels old
  context; flags out-of-function and unsupported changes. D-009, F-013–F-015.
- Shared `RepositoryService`, SQLite read-only retrieval, and five optional MCP
  stdio tools; client demo and connection instructions in `docs/MCP.md`.
  D-010/D-011 and F-016/F-017 document the paths and boundaries.

## Current work / handoff

WI-004 is active: [bounded investigation](docs/work-items/WI-004-investigation/FEATURE.md).
`investigation.py:run()` and `RepositoryService.investigate()` implement capture,
lexical/explicit/revision localization, incremental depth, observable verification,
limits and inline trace. Nine focused controller tests pass. CLI/MCP exposure and
fixture evaluations are next; final regression checks still pending this cycle.
MCP SDK 2.3.0 is installed in `.venv`; host settings are not configured.
All commits through `98c7517` are verified pushed on main. Current changes are local.

## Next planned slice

User requested completion before using a real codebase. Finish local investigation
and controlled fixtures now; then real assistant outcome evaluations. Model planning,
autonomous edits, and a dashboard remain planned. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the larger sequence.

## Broken / blockers / limitations

- No failing application check is currently recorded. 37 tests and 2 smoke cases
  passed in WI-003. The Windows sandbox blocked MCP subprocess pipe creation;
  the same test passed with approved pipe access. Details are in WI-003.
- Static analysis misses dynamic dispatch, inheritance, re-exports, nested
  functions, configuration, and some binding behavior. Missing edges do not prove
  independence. Method excerpts do not reconstruct class context.
- Every command rebuilds the index. The compile CLI expands the graph twice.
- Git analysis requires the repository root, excludes untracked files, represents
  renames as deletion/addition, and reads historical blobs separately. Working-tree
  capture is not atomic. Out-of-function/non-Python changes remain unresolved even
  with conservative symbol fallback. See `changes.unresolved` before trusting output.
- Memory uses whole-file hashes, over-invalidates unrelated edits, and does not
  check all dependencies. Code-first packing can leave no budget for lessons.
- HTTP API, frontend, worker, tracing, model loop, incremental indexing, and
  independent end-to-end benchmarks are not implemented.
- Restricted shell execution requires approved escalation for Git writes/network
  operations. Prior approved pushes succeeded. Some `.test-tmp/tmp*` directories
  from failed TemporaryDirectory attempts may be inaccessible; do not confuse them
  with source. Current tests use workspace UUID directories with normal creation.

## Useful commands

Run from the repository root:

```powershell
git status --short
python -m unittest discover -s tests -v
python evals/run.py
python -m diffcontext --repo examples/refunds compile --symbol billing.py:refund_total --max-tokens 2000
python -m diffcontext --repo . changes --ref HEAD
python -m diffcontext --repo . compile --ref HEAD --max-tokens 4000
.\.venv\Scripts\python.exe examples/mcp_client.py --repo examples/refunds
```

## Avoid

- Do not invent pre-Git history, retrospective rationale, or benchmark gains.
- Do not call the lexical baseline BM25 or the byte heuristic an exact token bound.
- Do not treat developer confirmation as proof that an evidence test ran, or the
  untrusted-data label as a proven injection defense.
- Do not duplicate core logic in future API/MCP wrappers or add infrastructure
  without a concrete problem, alternatives, and a measurable validation plan.
- Do not commit `.diffcontext`, `.test-tmp`, credentials, or generated artifacts.
- Follow AGENTS.md: meaningful commits with synchronized decisions, flows,
  work-item records, handover updates, and comments for non-obvious logic.
