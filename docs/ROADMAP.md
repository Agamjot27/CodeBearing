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
  recovery. Lesson confirmation stays in the developer CLI. Real assistant MCP
  use is recorded in the [public trials](DEMO.md); transport checks alone do not
  prove outcomes. Project setup supports Claude Code, Cursor and Codex.
- Extend implemented Git-diff seeds with complete module/class evidence and
  configuration dependencies; current fallback seeds symbols and reports gaps.
- Implemented: optional TS/JS parsing and persistent incremental parse reuse
  with full current-graph relinking; see [INDEXING.md](INDEXING.md).
- Implemented: code-aware lexical/graph/confirmed-memory ranking and bounded
  lesson reservation; [authored matched-budget comparison](RETRIEVAL.md).
  Real authored trials and [repeated smaller-model packets](demos/SMALL_MODEL_PACKET_TRIALS.md)
  with observed usage are recorded. No advantage established. Next: independently
  selected held-out tasks and source-root configuration.
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

Implemented: explicit lesson proposal and developer confirmation, SQLite storage,
symbol scopes/source hashes, and retrieval that excludes unconfirmed or stale
advice. The six MCP tools read memory; they do not create or confirm lessons.
Implemented demonstration: [authored analogy to an actual recorded test gap](demos/MEMORY_CONTINUITY.md),
explicit operator review, fresh-process retrieval and stale exclusion. It does not
attest human identity or later model benefit. Next: authenticated provenance and
independently measured later-session behavior where shared use requires them.
Automatic correction capture, renamed-symbol reconciliation and contradiction
handling remain future work. Repository content and lessons are untrusted evidence,
not instructions overriding the coding assistant.

## 5. Controlled evaluations and experiments — development harness implemented

Implemented: four synthetic buggy repositories, separated acceptance/reference
assets, executable grading, paired lexical/graph/confirmed-memory/stale controls,
shared declared model/budgets, prompt fingerprints, JSON command/replay contracts,
atomic scored checkpoints, quota-stop/resume and matched-task reports. Model-free
CI calibrates reference passes and unchanged failures. Interactive assistant
outcomes are recorded separately in the [public trial reports](DEMO.md); they
do not establish broad quality/cost improvements. Authored lessons are not genuine
historical corrections. See
[CODING_EVALS.md](CODING_EVALS.md). Opt-in hybrid controls and a built-in OpenRouter
HTTP adapter are implemented; only fake transport tests have exercised that
adapter. Interactive trials use the assistant's account rather than this adapter.
Implemented: separate opt-in saved-sign-in Codex packet protocol with actual
input/cached/output usage, counterbalanced repetitions and frozen engine/graders.
[32-call results](demos/SMALL_MODEL_PACKET_TRIALS.md) show no quality/cost advantage;
eight post-result retry checks verify a narrow declaration repair separately.
Strong execution isolation and [independent temporal task splits](INDEPENDENT_EVALS.md)
remain future evaluation work.

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
The [quickstart](QUICKSTART.md) and [reproducible demo plan](DEMO.md) show the existing
assistant workflow. Smaller-model testing and provenance-labeled correction-memory
demonstrations are published with their limits. Current evaluation does not
establish general improvement; independent validation remains future research.
A dashboard is optional future presentation work, not required to use the MCP
server. No frontend, HTTP API or autonomous editor is implemented.
