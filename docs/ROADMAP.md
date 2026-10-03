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

## 2. Agent integration and change localization — next

- Read-only MCP tools: search symbols, inspect impact, compile context, retrieve
  lessons. Keep lesson confirmation in the developer-controlled interface.
- Git-diff seeds with old/new coordinates, explicit deleted-symbol handling, and
  fallback for changes to imports, constants, and configuration.
- Proper lexical ranking and source-root configuration; incremental indexing.
- Structured trace events with run IDs, candidates, selection reasons, budget,
  index version, timing, and errors. Make traces inspectable before adding a UI.
- Exact tokenizer adapter and separate reserved budget for applicable lessons.

Acceptance: a real coding agent can consume our tools in a small repository, with
reproducible context and visible omissions. Integration contracts are tested.

## 3. Bounded investigation loop

Locate → retrieve → check missing evidence → expand or finish. The verifier uses
observable evidence, not a claim to inspect private model reasoning. Budget tool
calls, elapsed time, and tokens; stop repeated searches; report unresolved gaps.
Start with one coordinator. Add independent agents only for work that benefits
from parallel execution and measure the added cost.

## 4. Correction memory and reliability

Capture an explicit correction, mistaken approach, explanation, patch/commit,
test evidence, scope, source version, and status. Propose records automatically
but require review before treating them as authoritative. Handle renamed symbols,
contradictions, changed dependencies, and supersession. Separate repository content
from trusted instructions and test injection attempts through comments and lessons.

## 5. Controlled evaluations and experiments

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
