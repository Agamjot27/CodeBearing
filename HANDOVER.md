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
- CLI: `diffcontext/cli.py`; refund example; 9 regression tests; 2 synthetic
  retrieval smoke cases; GitHub Actions check configuration.
- Baseline committed and pushed: `fa2dd36` on `main`, remote
  `https://github.com/Agamjot27/DiffContext.git`.
- Engineering decisions D-001–D-006 and execution flows F-001–F-012 documented.
- Continuity workflow: handover, work-item templates, session-start instructions,
  and non-obvious comment requirements. D-007 records this addition.

## Current work / handoff

Git-diff localization is in progress in
[WI-002](docs/work-items/WI-002-git-diff-localization/FEATURE.md). First expose the
indexer for in-memory historical sources (complete, 13 tests passed); next map tracked changes and connect
impact/context commands. Existing runtime paths F-002, F-004, F-005 are affected.
Continuity docs were committed locally as `c213c74`; push status is not assumed.

## Next planned slice

After Git-diff localization, expose read-only MCP tools: search, impact, context compilation,
and lesson retrieval. Before implementing, create its FEATURE.md, document the
actual SDK/interface choice in DECISIONS.md, and add implemented paths to FLOW.md.
MCP is not implemented. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the larger sequence.

## Broken / blockers / limitations

- No failing application check is currently recorded. The 9 tests and 2 smoke
  cases last passed in the baseline-documentation cycle; this documentation-only
  cycle did not rerun them or claim new runtime verification.
- Static analysis misses dynamic dispatch, inheritance, re-exports, nested
  functions, configuration, and some binding behavior. Missing edges do not prove
  independence. Method excerpts do not reconstruct class context.
- Every command rebuilds the index. The compile CLI expands the graph twice.
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
