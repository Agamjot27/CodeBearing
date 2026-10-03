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
- CLI: `diffcontext/cli.py`; refund example; 29 regression tests; 2 synthetic
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

## Current work / handoff

Read-only MCP integration is in progress in
[WI-003](docs/work-items/WI-003-mcp-integration/FEATURE.md). First share orchestration
and introduce true read-only memory (complete, four service tests passed); next
wrap the official SDK and test stdio. D-010/F-016 describe shared orchestration.
Git-diff integration is committed as `bbed3ae`. Continuity docs are `c213c74`.
Only the original `fa2dd36`
baseline is known pushed; later commits remain local unless separately pushed.

## Next planned slice

After MCP integration, exercise the tools with a coding assistant and establish
controlled outcome evaluations before adding an investigation loop or dashboard. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the larger sequence.

## Broken / blockers / limitations

- No failing application check is currently recorded. 29 tests and 2 smoke cases
  passed in WI-002. The first revision test run failed during Windows Git-object
  cleanup; contained read-only cleanup retry resolved it. Details are in WI-002.
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
- Full API, frontend, MCP, worker, tracing, model loop, incremental indexing, and
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
