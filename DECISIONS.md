# Engineering decisions

Record decisions when they are made; preserve their IDs. If an approach changes,
mark its entry **Superseded by D-XXX** and add a replacement entry. Update this
file and FLOW.md in the same commit as the implementation when applicable.

## Provenance and history

This log was introduced on 2026-10-03 after the first prototype had been written,
at the user's request. D-001 through D-005 capture choices already explained in
the development conversation or explicitly documented in the existing code and
README. They are baseline records, not contemporaneous historical ADRs. The
alternatives below are comparisons recorded now, not claims that experiments or
formal comparisons happened earlier. No performance benefit is assumed.

Unrecorded details are identified as such. Git begins with the existing prototype
and these documents as one baseline; it does not reconstruct fictitious earlier
commits. Use `git log --oneline -- DECISIONS.md` and `git log -p -- <path>` to find
introducing and modifying commits. A commit cannot contain its own final hash.

## D-001 — Start with a local Python core and CLI

**Status:** Accepted; baseline record.

**Decision**

Use Python 3.10+, standard-library AST parsing, and a command-line entry point for
the first working slice. Analyze Python repositories without executing their code.

**Context**

The workspace was empty. The immediate objective was to make indexing, impact
analysis, and context compilation runnable before adding an agent or dashboard.

**Alternatives Considered**

Comparison recorded now: a TypeScript service with a parser dependency; a
multi-language parser such as Tree-sitter; beginning with a hosted full-stack app.

**Why This Approach**

The original progress update explicitly selected Python to analyze Python code
locally without API keys. The standard library made the initial slice runnable
without installing runtime dependencies or operating external services.

**Trade-offs**

Only Python is supported. The analyzer does not resolve arbitrary runtime behavior,
inheritance, re-exports, nested functions, or configuration. There is no web API,
frontend, or MCP server yet. Python parses the syntax supported by its runtime.

**Future Reconsideration**

Add language adapters when target repositories require them. Add API/MCP boundaries
when connecting a real coding agent, reusing rather than duplicating the core.

**Implementation:** `diffcontext/index.py`, `diffcontext/cli.py`, `pyproject.toml`.
**Flows:** F-001, F-002.

## D-002 — Keep the initial graph in memory and rebuild on each command

**Status:** Accepted; baseline behavior, rationale adopted explicitly now.

**Decision**

Continue with an in-memory `Index` and bounded caller/callee traversal for this
prototype. Do not introduce a persistent graph service in this documentation cycle.

**Context**

`cli.main()` currently rebuilds the index for every command. There was no prior
recorded database comparison or indexing latency measurement. This entry does not
claim otherwise.

**Alternatives Considered**

SQLite or PostgreSQL symbol/edge tables; a dedicated graph database; a disk cache
with file-level invalidation.

**Why This Approach**

The present scope is a local demonstrator. Keeping the existing design now avoids
adding cache invalidation and deployment work before measuring indexing latency.
It also keeps the execution path simple enough to inspect and test.

**Trade-offs**

Every CLI request pays the indexing cost, even lesson status updates. Indexes are
not atomic repository snapshots; files may change between reads. Imports are used
to resolve calls, but imports and inheritance are not separate persisted edge types.

**Future Reconsideration**

Measure cold and repeated indexing on representative repositories. Add snapshot
identity, caching, and incremental updates when repeated work or consistency matters.
Evaluate graph storage against measured traversal workloads, not terminology.

**Implementation:** `Index`, `build_index()`, `context.impact()`.
**Flows:** F-002, F-004.

## D-003 — Pack whole excerpts with explicit estimated-budget omissions

**Status:** Accepted; baseline record.

**Decision**

Pack complete function/method excerpts with imports, citations, and inclusion
reasons. Use the dependency-free `ceil(UTF-8 bytes / 3)` estimate for now, and expose
omissions and missing seeds. Do not describe this as an exact model token bound.

**Context**

The initial slice needed a deterministic size-limited context package. Import
aliases lose meaning when separated from their imports (recorded in the code).

**Alternatives Considered**

Model-specific tokenizers; raw character truncation; LLM-generated summaries;
splitting oversized functions into partial excerpts.

**Why This Approach**

Whole excerpts preserve the selected code without silent truncation. Explicit
omissions let callers detect inadequate context. The original implementation was
deliberately dependency-free. The particular divisor of three has no recorded
empirical calibration; it is a provisional heuristic, not a measured optimum.

**Trade-offs**

Oversized seeds can be omitted. Repeated imports consume budget. Distance-first
ordering is not a learned relevance ranking. Code is packed before lessons, which
can leave no space for memory. `complete` means no budget omissions among generated
candidates, not proof that all task-relevant evidence was discovered.

**Future Reconsideration**

Integrate an exact tokenizer for a selected model; test reserved lesson budgets,
deduplication, and alternate ranking on held-out tasks with matched budgets.

**Implementation:** `context.estimate_tokens()`, `context.compile_context()`.
**Flows:** F-005, F-006.

## D-004 — Store explicitly reviewed lessons in repository-local SQLite

**Status:** Accepted; baseline record.

**Decision**

Store lessons in `.diffcontext/memory.sqlite3`. Require explicit confirmation for
inclusion. Check evidence and scoped-source file hashes and exclude stale lessons.
Keep developer explanations distinct from inferred explanations.

**Context**

The project needs to preserve corrections without injecting unconfirmed or obsolete
advice. The original discussion made evidence, scope, confirmation, and freshness
part of the memory design; the prototype implemented those checks locally.

**Alternatives Considered**

Unstructured notes; embedding-only retrieval; automatic confirmation; PostgreSQL;
symbol-level or semantic validity checks instead of whole-file hashes.

**Why This Approach**

SQLite supports the current local, single-user workflow without a database server.
Exact scope and file hashes make retrieval eligibility inspectable. Developer
confirmation records an attestation; the system does not invent intent from a diff
or claim that an evidence test was executed.

**Trade-offs**

Unrelated edits invalidate a whole file's lessons. Changes elsewhere may go
undetected. There is no immutable review history, explicit supersession link,
multi-user authorization, or schema migration framework. Confirmation is a CLI
operation, not a security boundary against someone with local filesystem access.

**Future Reconsideration**

Add structured correction/test artifacts, review history, and scope migrations as
memory capture matures. Consider PostgreSQL when shared API workers or multiple
users require it. Test stale-memory interference before relaxing freshness checks.

**Implementation:** `memory.Memory`, `context.compile_context()`.
**Flows:** F-007 through F-010.

## D-005 — Treat the current evaluation as a smoke fixture

**Status:** Accepted; baseline record.

**Decision**

Use deterministic regression tests and two synthetic retrieval cases to check the
foundation. Label their limits explicitly; do not claim agent task-success gains.

**Context**

The initial implementation needed repeatable checks without model costs. The
evaluation's own docstring and output already state that it is not an independent
benchmark or a comparison at matched budgets.

**Alternatives Considered**

A full ContextBench run immediately; LLM-as-judge scoring; live agent executions
before retrieval and memory behavior were stable.

**Why This Approach**

Local checks isolate implementation failures and cost no model calls. A small
fixture can prove the expected code path runs, but cannot prove general retrieval
quality. This distinction was explicitly communicated when the first slice shipped.

**Trade-offs**

The examples are hand-built and not held out. Lexical search is term overlap, not
BM25. No model, correctness test runner for generated patches, API cost tracking,
latency benchmark, or adversarial prompt-injection evaluation is implemented.

**Future Reconsideration**

Once agent integration works, use temporally separated tasks, fixed models and
budgets, executable outcome checks, and documented baselines. Choose gates from
credible baseline measurements rather than an arbitrary headline pass percentage.

**Implementation:** `tests/test_core.py`, `evals/run.py`, `evals/cases.json`.
**Flows:** F-011, F-012.

## D-006 — Adopt commit-level implementation traceability

**Status:** Accepted on 2026-10-03; new decision from the user's workflow instructions.

**Decision**

Make meaningful commits regularly. Maintain DECISIONS.md and FLOW.md alongside
implementation, and preserve these requirements in root AGENTS.md.

**Context**

The user requires an engineering history that explains why choices were made, how
execution works, and which commits changed it. No local Git repository existed.
The supplied GitHub repository had no advertised refs when checked.

**Alternatives Considered**

One final delivery commit; end-of-project documentation; splitting the existing
prototype into fabricated historical feature steps.

**Why This Approach**

An honest initial baseline followed by small, coherent implementation commits
preserves the real history. File/function-level flow records can be verified against
code. Stable decision IDs make changed approaches traceable without erasing them.

**Trade-offs**

Documentation takes time in every significant development cycle. The original
prototype's pre-Git edit sequence cannot be recovered from commit history.

**Future Reconsideration**

Keep the policy unless the user changes it. Split large documents into linked files
only if needed, while retaining these root entry points and stable decision IDs.
