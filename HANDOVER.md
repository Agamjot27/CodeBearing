# Current handover

Updated: 2026-10-04 (Asia/Calcutta). Read this at each session start, after AGENTS.md.
This is a current-state snapshot; detailed history belongs in Git and work items.

## Objective

Build an independent change-aware context engine and evidence-backed engineering
memory for coding agents. Prove usefulness through controlled evaluations. The
current product is a local Python CLI and MCP server for coding assistants.

## Done

- Python AST symbols and statically resolved call edges: `diffcontext/index.py`.
- Optional TypeScript/JavaScript/TSX/JSX/MTS/MJS syntax-tree indexing, conservative
  ESM edges, shared Git deletion recovery and memory freshness; D-017/F-027.
  Install `[mcp,typescript]`; exact limitations: `docs/LANGUAGES.md`.
- Lexical seed search, bounded caller/callee expansion, and whole-excerpt packing:
  `diffcontext/context.py`. Token counts are estimates, not exact tokenizer counts.
- SQLite lesson proposal/review, exact-scope retrieval, evidence/source hash
  freshness checks: `diffcontext/memory.py`.
- CLI: `diffcontext/cli.py`; refund example; regression/protocol tests; 2 existing
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
- Installable 0.2.0 MCP launcher, generated Claude/Cursor/Codex configuration,
  model-free protocol check and clean-wheel validation; D-016, F-025/F-026.
  Setup/release guides: `docs/MCP.md`, `docs/RELEASING.md`. No PyPI release yet.

## Current work / handoff

WI-008 implemented: [Persistent incremental indexing](docs/work-items/WI-008-incremental-indexing/FEATURE.md).
Optional --cache stores JSON parse facts and current symbols/edges in local SQLite;
unchanged files skip parsing, all call facts relink against current exports.
Version 0.4.0; generated assistant configuration propagates cache choice.
Final full suite passed 108 tests; two subsequently added CLI/Git tests passed
separately (110 covered total). Core-only cache tests pass with TS skipped.
Saved authored 120-file/960-function local measurement: full 105.255ms, warm
30.950ms, empty-cache 276.860ms, full/cached edit 99.242/69.762ms. Exact parity
passed; no production/competitor/coding-benefit claim. Cache storage errors fall
back to current evidence. Clean wheel 0.4.0 with both extras passed installed compilation, configs,
MCP discovery/search and cross-process persistent-cache reuse.
WI-007 pushed as 53dd799; WI-006 pushed as 8bfe195. MCP SDK/parsers are installed
in .venv; source installation is editable; version metadata is refreshed for 0.4.0. No assistant-host settings configured,
public PyPI release or live model outcomes. Check final Git synchronization after push.

## Next planned slice

Implement and evaluate hybrid retrieval: improve lexical ranking, combine task
search with graph expansion and reviewed memory, compare against current retrieval
under identical budgets. Use the existing coding harness for paired live trials
once a model/provider is selected and configured. Dedicated graph storage needs
measured workload justification; derived symbols/edges now persist in local SQLite.
Public publication needs a selected distinct name/publisher identity, neither
configured. CodeBearing was suggested, not selected or availability-checked.
A real host integration and provider/model account remain unverified. Add genuine
prior correction history and held-out tasks before claiming memory benefit.
Model planning, autonomous edits, and a dashboard remain planned. See
[docs/ROADMAP.md](docs/ROADMAP.md) for the larger sequence.

## Broken / blockers / limitations

- No failing application check is currently recorded. Full suite passed 108 tests
  plus two separate CLI/Git cache tests. MCP pipes need approved sandbox access.
  CI was updated for Linux/Windows; hosted CI results are not yet verified here.
- Coding trials are synthetic single-response edits; lessons are authored pre-task
  data, not real historical corrections. Declared model/settings/usage depend on the
  external adapter. Missing costs stay unknown across retried attempts. Grading
  subprocesses are not a security sandbox; use trusted local fixtures/candidates.
- Static analysis misses dynamic dispatch, inheritance, re-exports, nested
  functions, configuration, and some binding behavior. Missing edges do not prove
  independence. Method excerpts do not reconstruct class context.
- Every request reads source bytes; --cache reuses parsing, not graph linking.
  Cold cache initialization can be slower. Historical Git parsing remains uncached.
  The compile CLI expands the graph twice.
- Git analysis requires the repository root, excludes untracked files, represents
  renames as deletion/addition, and reads historical blobs separately. Working-tree
  capture is not atomic. Out-of-function/unsupported-language changes remain unresolved even
  with conservative symbol fallback. See `changes.unresolved` before trusting output.
- Memory uses whole-file hashes, over-invalidates unrelated edits, and does not
  check all dependencies. Code-first packing can leave no budget for lessons.
- Investigation task selection is lexical. ready means selected static graph
  coverage, not semantic task correctness. Deadline is cooperative; ongoing work
  can overrun before returning. Trace/JSON overhead is outside the text budget.
- HTTP API, frontend, worker, persistent tracing, model loop, and
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
