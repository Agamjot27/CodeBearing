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

WI-016 configured, desktop verification pending: user screenshot lacks CodeBearing
on the BookMyShow new-chat MCP list, although CLI reads the trusted project entry.
Exact configured interpreter passes six-tool check. Added the same server to the
user-level Codex config using codex mcp add; get confirms enabled. This global
entry remains bound to BookMyShow, even in other projects. General setup remains
project-only. User must fully quit/reopen the app and confirm a real tool call.
Root cause of UI omission unproven; D-025/F-035, WI-016 BUG.md. No app source edit.

WI-015 resolved: patch 0.6.1 pins tree-sitter 0.25.2 after binding 0.26.0
crashes natively on BookMyShow's redis.ts. Same interpreter/project succeeds
with the prior binding (316 symbols). 30 language/cache regression tests pass.
Installed patch and completed BookMyShow `setup --client codex`; verified six tools
and safely wrote its project .codex/config.toml. No application code changed.
Original uv trampoline error was not reproduced; reinstallation refreshed launchers.
D-024/F-034. Next: restart Codex in BookMyShow and perform the actual tool-assisted
bug-fix trial. No model result yet. See WI-015 BUG.md for attempted fixes/evidence.

WI-014 completed locally: CodeBearing is the selected public name, version 0.6.0.
Distribution/commands are codebearing/codebearing-mcp; internal diffcontext imports,
legacy aliases and stored data remain compatible. Project-scoped setup safely merges
Claude/Cursor/Codex settings after a real MCP connection check. D-023/F-033.
155 full-suite tests pass, plus seven connection tests after the Cursor stdio fix;
clean-wheel install, project setup, six-tool discovery/search and cache reuse pass.
README now leads with install/connect; docs/FIRST_TASK.md describes a manual trial.
No actual assistant bug-fix session or PyPI publication has been performed.
Next: choose an assistant, connect a project and observe a real task using its tools.
Provider/held-out benchmark work is paused in favor of usability; make no quality
improvement claims from synthetic calibration or protocol tests.

WI-013 completed and pushed as 21d30db: explicit OpenRouter adapter and local
preflight; D-022/F-032. No model/key selected and no real provider call made.
Independent benchmark import/isolation remain unimplemented.

WI-012 completed and pushed as 4a71cde: [Hybrid coding controls](docs/work-items/WI-012-hybrid-coding-controls/FEATURE.md).
Opt-in seven-condition comparison implemented, four new tests pass. Final full
regression passed 142 tests; hybrid self-check passed 21 reference/21 unchanged
trials and six fresh/six stale checks. D-021/F-031; manifests now pin
all package source hashes and reject old version-1 outputs. No new provider calls.

WI-011 completed (d364adb): [Bounded harness subprocesses](docs/work-items/WI-011-bounded-subprocesses/BUG.md).
processes.py now uses file-backed I/O and bounded owned-tree/group cleanup for
grading and command adapters (D-020/F-030). Three process, four grading and nine
experiment tests pass with Windows process permissions. No real model trial has run.

WI-009 completed and pushed as 3738e3a:
[Hybrid retrieval](docs/work-items/WI-009-hybrid-retrieval/FEATURE.md).
Version 0.5.0: default search/task investigation combines code-aware lexical
ranking, bounded graph candidates and fresh developer-confirmed memory. Explicit
symbol/ref packing remains unchanged; --retrieval legacy preserves the baseline.
Hybrid tasks reserve up to 20% for whole scoped lessons, with seed priority.
D-019/F-029 and docs/RETRIEVAL.md document weights, paths and limits.
Saved seven authored matched-budget cases: MRR 0.20/0.90 over five nonempty tasks;
both policies fail the broad refund task, and hybrid fresh-memory precision is 1/3.
These are development results, not held-out or live coding outcomes.
Final full suite passed all 135 tests with MCP and TS extras. Six investigation,
two original smoke and TS budget fixtures pass; seven hybrid cases pass their
contract gates. Clean 0.5.0 wheel passed outside-checkout hybrid task retrieval,
generated client configs, six-tool MCP transport and cross-process cache reuse.
Editable installation metadata refreshed to 0.5.0. WI-010 startup-sensitive test
fix committed as a514b20; runtime timeout behavior was not changed.
WI-008 pushed as 7de87ec; optional --cache reuses parse facts and relinks current
graphs (D-018/F-028). WI-007 pushed as 53dd799; WI-006 as 8bfe195.
MCP SDK/parsers are installed in .venv. No assistant-host settings configured,
public PyPI release or live model outcomes. Check final Git synchronization after push.

## Next planned slice

Run one actual assistant task using CodeBearing and record which tools it calls,
what context it receives and whether the project tests pass after its edit.
The user selected CodeBearing; package ownership and PyPI publisher are still
unconfigured. Git-source installation and an installed wheel are available.
A real host integration and model outcome remain unverified. Return to independent
held-out tasks and observed prior corrections after the usability trial; keep
synthetic calibration distinct from evidence of coding improvement.

## Broken / blockers / limitations

- WI-013 full suite passed 149 tests. Earlier WI-009 attempts had a transient Git
  timeout, restricted MCP pipe errors, and a startup-sensitive assertion fixed in
  WI-010. Restricted MCP pipes require approved access.
  An earlier suite stalled at grading timeout; WI-011 replaces inherited pipe
  capture and tests descendant termination. Hosted CI/POSIX cleanup unverified.
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
  check all dependencies. Explicit/ref code-first packing may leave no lesson budget.
- Investigation task selection uses lexical/memory heuristics. ready means selected static graph
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
python evals/hybrid.py
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
