# Build roadmap

## Product objective

Help coding agents solve repository changes with the necessary evidence and avoid
repeating verified mistakes. Compare success, cost, and latency at the same model
and task budget. A smaller context is useful only if task quality holds or improves.

## 1. Local context and memory foundation — implemented

Python AST index → explicit seed → bounded caller/callee expansion → whole-excerpt
packing → JSON context package. SQLite lessons require confirmation and record
evidence/source hashes for conservative freshness checks. CLI, a refund example,
regression tests, and a synthetic evaluation fixture make the slice runnable.
Git revision localization now maps tracked old/current line changes into both
graphs, retains deleted evidence, and compiles labeled packages under one budget.
Imports/constants/unsupported-language changes remain explicit unresolved gaps.

## 2. Agent integration and change localization — partially implemented

- Implemented: six read-only MCP tools for search, change localization, impact,
  compilation, lessons and investigation. SDK/stdin-stdout tests exercise contracts and error
  recovery. Lesson confirmation stays in the developer CLI. Next: demonstrate
  usage in a real coding-assistant session; transport checks do not prove outcomes.
- Extend implemented Git-diff seeds with complete module/class evidence and
  configuration dependencies; current fallback seeds symbols and reports gaps.
- Implemented: optional TS/JS parsing and persistent incremental parse reuse
  with full current-graph relinking; see [INDEXING.md](INDEXING.md).
- Implemented: code-aware lexical/graph/confirmed-memory ranking and bounded
  lesson reservation; [authored matched-budget comparison](RETRIEVAL.md).
  Next: held-out tasks, real coding trials and source-root configuration.
- Implemented for investigation: inline run IDs, captured-byte snapshot identities,
  candidates, verification, limits, timing and stop reasons; explicit saved-JSON
  CLI inspection. Persistent history and traces for unexpected errors remain planned.
- Implemented for hybrid tasks: reserved budget for applicable lessons. Next:
  exact tokenizer adapter; explicit symbol/ref packing retains the prior policy.

Acceptance: a real coding agent can consume our tools in a small repository, with
reproducible context and visible omissions. Integration contracts are tested.

## 3. Bounded investigation loop — local controller implemented

Locate → retrieve → check static frontier/omissions/source gaps → expand or finish
now runs through `investigate` in CLI/MCP. One controller uses one code capture,
checked memory, unique depths, operation limits, estimated final-text budget and a
cooperative elapsed-time limit. No model planner/editor is included. Six development
fixtures check behavior and budget-matched seed-only retrieval. Next measure held-out
localization and real coding outcomes before adding model-based planning. Add
independent agents only when parallel execution shows measurable benefit.

## 4. Correction memory and reliability

Capture an explicit correction, mistaken approach, explanation, patch/commit,
test evidence, scope, source version, and status. Propose records automatically
but require review before treating them as authoritative. Handle renamed symbols,
contradictions, changed dependencies, and supersession. Separate repository content
from trusted instructions and test injection attempts through comments and lessons.

## 5. Controlled evaluations and experiments — development harness implemented

Implemented: three synthetic buggy repositories, separated acceptance/reference
assets, executable grading, paired lexical/graph/confirmed-memory/stale controls,
shared declared model/budgets, prompt fingerprints, JSON command/replay contracts,
atomic scored checkpoints, quota-stop/resume and matched-task reports. Model-free
CI calibrates reference passes and unchanged failures. No live model outcomes have
been collected; authored lessons are not genuine historical corrections. See
[CODING_EVALS.md](CODING_EVALS.md). Opt-in hybrid controls and a built-in OpenRouter
HTTP adapter are implemented; only fake transport tests have exercised it. Live
model/account verification, repeat samples, strong execution isolation and
[independent temporal task splits](INDEPENDENT_EVALS.md) remain next.

Use temporally separated development and held-out tasks. Index only the repository
state available before each task; do not expose gold patches or future corrections.
Compare ordinary search/read, graph expansion, budget selection, and memory using
the same model and budget. Track task-test success, relevant-context recall,
repeated mistakes, stale-memory interference, latency, tokens, and monetary cost.

Cache safe reusable work, checkpoint runs, cap concurrency, and distinguish quota
errors from scored failures. Use executable checks as the primary signal; document
any LLM judge rubric and validate it against human labels. Choose CI thresholds
after measuring a credible baseline, not an arbitrary headline percentage.

## 6. Evaluated improvement and demonstration

Recorded retrieval failures propose ranking or retrieval-policy changes. Compare
candidate policies against independent regression and held-out sets before retaining
them. The optimization loop cannot change its own scoring rules or access boundaries.
Build a dashboard showing the task, graph, selected evidence, lessons, trace, and
before/after results once the backend is working and measured.
