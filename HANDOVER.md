# Current handover

Updated: 2026-10-04 (Asia/Calcutta). Read this at each session start, after AGENTS.md.
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
- CLI: `diffcontext/cli.py`; refund example; 63 regression/protocol tests; 2 existing
  retrieval smoke cases and 6 investigation development fixtures; CI configuration.
- Baseline committed and pushed: `fa2dd36` on `main`, remote
  `https://github.com/Agamjot27/DiffContext.git`.
- Engineering decisions D-001–D-006 and execution flows F-001–F-012 documented.
- Continuity workflow: handover, work-item templates, session-start instructions,
  and non-obvious comment requirements. D-007 records this addition.
- Captured-source index adapter: `f09d471`, documented by D-008.
- Git revision localization: `changes.py` maps tracked modifications, additions,
  and deletions in old/current graphs; restores surviving old callers; labels old
  context; flags out-of-function and unsupported changes. D-009, F-013–F-015.
- Shared `RepositoryService`, SQLite read-only retrieval, and six optional MCP
  stdio tools; client demo and connection instructions in `docs/MCP.md`.
  D-010/D-011 and F-016/F-017 document the paths and boundaries.
- Bounded local investigator through CLI/MCP: task/symbol/ref localization, one
  captured code snapshot, checked lessons, observable verification, limits and trace.
- Versioned full JSON reports, `--summary`, explicit saved-file `inspect`, and
  budget-matched seed-only development comparison. D-012/D-013, F-018–F-020.
- Controlled coding harness: three buggy repositories, separated acceptance checks,
  reference calibration, paired context/memory controls, command/replay contracts,
  quota stop/resume, attempt history and provenance-checked JSON artifacts.
  `coding.py`, `experiments.py`, `evals/coding_bench.py`; D-014/D-015, F-021–F-024.

## Current work / handoff

WI-005 is complete: [controlled coding evaluation](docs/work-items/WI-005-coding-evaluation/FEATURE.md).
Full MCP-enabled suite passed 63 tests; final adapter/history changes also pass all
nine affected experiment tests. Model-free self-check: three calibrated bugs,
12 reference passes, 12 unchanged failures, three confirmed/stale memory controls.
Fixture/grader milestone: `321d140`; find paired-harness commit using
`git log --oneline -- diffcontext/experiments.py`. No live model was called.
MCP SDK 2.3.0 is installed in `.venv`; host settings are not configured.
Prior work through `11ec359` was verified pushed on main. Check later synchronization
with `git rev-list --left-right --count main...origin/main` after each push.

## Next planned slice

Configure a selected model adapter or collect responses to exported packets, then
run paired live trials. No model provider/account is configured. Add genuine prior
correction history and temporal held-out tasks before making memory-benefit claims.
Use observed failures to improve module/class evidence and retrieval.
Model planning, autonomous edits, and a dashboard remain planned. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the larger sequence.

## Broken / blockers / limitations

- No failing application check is currently recorded. 63 tests, 8 retrieval fixtures
  and the coding-harness self-check pass. MCP pipe tests need approved sandbox access.
- Coding trials are synthetic single-response edits; lessons are authored pre-task
  data, not real historical corrections. Declared model/settings/usage depend on the
  external adapter. Missing costs stay unknown across retried attempts. Grading
  subprocesses are not a security sandbox; use trusted local fixtures/candidates.
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
- Investigation task selection is lexical. ready means selected static graph
  coverage, not semantic task correctness. Deadline is cooperative; ongoing work
  can overrun before returning. Trace/JSON overhead is outside the text budget.
- HTTP API, frontend, worker, persistent tracing, model loop, incremental indexing, and
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
python evals/investigate.py
python evals/coding_bench.py self-check
python -m diffcontext --repo examples/refunds compile --symbol billing.py:refund_total --max-tokens 2000
python -m diffcontext --repo . changes --ref HEAD
python -m diffcontext --repo . compile --ref HEAD --max-tokens 4000
.\.venv\Scripts\python.exe examples/mcp_client.py --repo examples/refunds
python -m diffcontext --repo examples/refunds investigate --task refund_total --summary
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
