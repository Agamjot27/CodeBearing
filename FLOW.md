# Execution flows

This describes the code that exists, not the target architecture. Updated with the
initial documented Git baseline on 2026-10-03. Paths are relative to the repository.
Decision IDs refer to DECISIONS.md. Use `git log -p -- FLOW.md` to inspect changes.

## Current modification scope

WI-001 adds development documentation continuity only. No runtime file/function
or F-001–F-012 execution path changes in this cycle. See
[its feature record](docs/work-items/WI-001-documentation-continuity/FEATURE.md)
and [HANDOVER.md](HANDOVER.md) for current progress and next work.
Future cycles must identify the exact flows/functions they modify here.

## Session documentation path (development workflow)

Read `AGENTS.md` → `HANDOVER.md` → linked active
`docs/work-items/<id>-<slug>/FEATURE.md` or `BUG.md` → relevant `DECISIONS.md:D-XXX`
→ affected `FLOW.md:F-XXX` → source files/functions → inspect Git status.
During changes, update the work-item record and local intent comments, then the
affected decisions/flows and handover in the same cycle. This is an instruction
for developers/agents, not an automatically executed application function.

## Implementation coverage

| Requested workflow | Current status / flow |
| --- | --- |
| Repository registration | Not implemented; `--repo` is a directory argument, not a persistent registration |
| Repository indexing | F-002: full in-memory rebuild |
| Incremental re-indexing | Not implemented |
| Natural-language task → localization | F-003: lexical candidates only; no automatic seed selection or semantic planner |
| Git diff → affected symbols | Not implemented |
| Dependency graph expansion | F-004 |
| Context compilation | F-005 |
| Token-budget selection | F-006 |
| Engineering-memory retrieval | F-007 |
| Lesson proposal | F-008: manual input |
| Lesson confirmation | F-009 |
| Lesson invalidation / stale detection | F-010: computed on reads |
| MCP request | Not implemented |
| Investigation loop | Not implemented |
| Evaluation execution | F-011 and F-012 |
| Frontend Context Explorer | Not implemented |
| Run Inspector / trace loading | Not implemented |

There are no HTTP routes, frontend components, controller services, workers, model
calls, remote database, or persisted run traces. Do not use proposed names from the
roadmap as if they were callable code.

## F-001 — CLI entry and shared behavior

**Trigger:** `python -m diffcontext --repo <directory> <command>` or the installed
`diffcontext` entry point.

**Execution Path:** `diffcontext/__main__.py` → `diffcontext/cli.py:main()`.
The installed script maps directly to `cli:main` through `pyproject.toml`.
`main()` parses arguments → calls `index.py:build_index(args.repo)` → dispatches
to the requested function → `json.dumps()` → stdout. This rebuild occurs for
**every command**, including memory list/status operations.

**Data Transformation:** Arguments become a resolved repository `Path`, a fresh
`Index`, and command-specific inputs. Results become indented JSON.

**Database Interaction:** None in the shared path. Memory branches are below.

**External Interaction:** Local source filesystem and console. `ValueError`,
`OSError`, and `sqlite3.Error` are printed to stderr with exit code 2. Argument
errors are handled by argparse; successful commands return 0.

**Output:** Command JSON or a human-readable error. No web response or stream.

## F-002 — Repository indexing

**Trigger:** Any CLI command, or direct `build_index(root)` call.

**Execution Path:** `cli.py:main()` → `index.py:build_index()` → `os.walk()` →
`tokenize.open()` → `ast.parse()` → `digest()` → create `Symbol` records →
resolve calls via `_body_walk()` and import/qualified-name maps → return `Index`.
For the `index` command, `main()` then calls `Index.describe()`.

**Data Transformation:** `.py` files become source strings and ASTs; top-level
functions and direct class methods become IDs of the form `path.py:Class.method`.
Module-level imports resolve aliases and relative module paths. Calls become
`edges[caller_id] = {callee_ids}`. SHA-256 file hashes, imports, source ranges,
excerpts, and warnings are attached. Shadowed names are conservatively skipped
for the local bindings recognized by the current analyzer.

**Database Interaction:** None. `Index.symbols`, `edges`, `warnings`, and `hashes`
live only in memory. `describe()` serializes call edges with `kind: calls`.

**External Interaction:** Reads local files without importing or executing them.
Prunes hidden/common dependency directories and directory symlinks; skips file
symlinks and files over 1 MB. Recorded parse/read failures become warnings.
There is no Git integration or atomic source snapshot.

**Output:** `Index` to library callers; its JSON description for the index command.
See D-001 and D-002.

## F-003 — Lexical seed search

**Trigger:** `search "refund_total"` after shared indexing.

**Execution Path:** `cli.py:main()` → `context.py:search(index, query)` → return
matches → `main()` adds index warnings and prints JSON.

**Data Transformation:** Query, symbol names/paths, and source are lowercased and
tokenized using an identifier regex. Score = 3 × query/name-path term overlap +
query/source overlap. Nonzero matches sort by descending score, then ID. Default
limit is 10. This is not BM25 or embedding search and does not split snake_case.

**Database Interaction:** None; reads `Index.symbols`.

**External Interaction:** None beyond shared source indexing.

**Output:** Candidate IDs and scores. The caller must choose seed IDs; this flow
does not automatically call `impact()` or an LLM.

## F-004 — Dependency expansion

**Trigger:** `impact --symbol <id>` or a `compile_context()` call.

**Execution Path:** `cli.py:main()` → `context.py:impact()` →
`index.py:select_symbol()` → construct reverse caller map → breadth-first traversal
over callers and callees → sort candidates by distance, then ID.

**Data Transformation:** Exact IDs or unique short names become normalized seed
IDs. Unknown or ambiguous names fail explicitly. Each visited symbol has a minimum
discovery distance and a list of relationship reasons. Previously discovered
symbols are not requeued; reasons can still accumulate. Depth defaults to 2 and
is restricted to 0–5.

**Database Interaction:** None; reads the in-memory graph.

**External Interaction:** None after shared indexing.

**Output:** `{seeds, candidates: [{id, distance, reasons}], warnings}`. Tests are
found through call edges, not through a separate test-discovery service. D-002.

## F-005 — Context compilation with memory

**Trigger:** `compile --symbol <id> --max-tokens <budget>`.

**Execution Path:** `cli.py:main()` → `index.py:build_index()` →
`context.py:impact()` → if memory DB exists, `memory.py:Memory.__init__()` →
`Memory.list(candidate_ids)` → `Memory.close()` →
`context.py:compile_context(index, seeds, budget, depth, lessons)` →
`impact()` again → packing (F-006) → `main()` adds `excluded_lessons` → JSON.

**Data Transformation:** Candidate IDs scope the memory read. The compiler creates
`text`, inclusion metadata, omitted IDs/reasons, included lesson IDs, missing seeds,
estimated token count, and warnings. The CLI adds status/staleness for rejected
lessons. Scope checks also exist in the compiler for direct library callers.
Currently graph expansion runs twice on the CLI path; no cache removes that work.

**Database Interaction:** If no memory file exists, none. Otherwise opens SQLite;
`Memory.__init__()` performs `CREATE TABLE IF NOT EXISTS lessons` and a commit, then
`list()` reads lessons. Compilation does not add or confirm lessons.

**External Interaction:** Local source, optional SQLite file, stdout. No model call.
The evidence label is not an enforced prompt-injection defense.

**Output:** Context JSON. Only `text` is budgeted; metadata is outside that budget.
`complete` indicates no budget omissions, not semantic sufficiency. D-003, D-004.

## F-006 — Estimated token-budget selection

**Trigger:** `context.py:compile_context()` after graph expansion.

**Execution Path:** `compile_context()` validates budget ≥128 → adds evidence
header → constructs each candidate section → `estimate_tokens(text + section)` →
includes the entire section or records an omission → evaluates eligible lessons
in supplied order using the same check → calculates missing seeds and final size.

**Data Transformation:** Each section includes path/range, name, reasons, module
imports, and the full source excerpt. Token estimate = `ceil(UTF-8 bytes / 3)`.
Lessons follow code, must have candidate-matching scope, confirmed status, and
`stale == False`. The compiler trusts the supplied freshness flag; the CLI obtains
it from `Memory.list()`. Direct callers must also retrieve fresh records.

**Database Interaction:** None inside the compiler.

**External Interaction:** None; text transformation only.

**Output:** Whole excerpts within the heuristic budget, plus omissions. No exact
tokenizer, optimal subset solver, summarizer, or model-specific guarantee. D-003.

## F-007 — Engineering-memory retrieval

**Trigger:** `memory list`, compilation with an existing memory file, or direct use.

**Execution Path:** `cli.py:main()` → `memory.py:Memory.__init__(root)` →
`Memory.list(scopes=None or candidate_ids)` → F-010 freshness checks → return
records → `Memory.close()`. Compilation then applies F-006 eligibility checks.

**Data Transformation:** SQLite rows become dictionaries. Optional exact scope
filtering is performed in Python after `SELECT * FROM lessons ORDER BY id`.
`stale` is added in memory; `list()` includes proposed and stale rows for inspection.

**Database Interaction:** Creates `.diffcontext/memory.sqlite3` and the `lessons`
table if necessary. Reads all lesson rows. The table contains `id`, `scope`,
`lesson`, `evidence`, `evidence_hash`, `scope_hash`, `status`, and `created_at`.

**External Interaction:** SQLite and file hashing; no vector database or LLM.

**Output:** Ordered lesson dictionaries. CLI wraps them under `lessons`. D-004.

## F-008 — Manual lesson proposal

**Trigger:** `memory add --scope <exact-id> --lesson <text> --evidence <path.py>`.

**Execution Path:** `cli.py:main()` → `build_index()` → `Memory.__init__()` →
`Memory.add(index, scope, lesson, evidence)` → `index.py:safe_path()` →
`digest(evidence_path)` → SQLite INSERT → commit → `Memory.close()`.

**Data Transformation:** Validate indexed exact scope and nonempty text. Evidence
must be an indexed Python file in the repository. Read the scoped file hash from
`Index.hashes` and hash the evidence file. Store the explanation exactly as supplied.

**Database Interaction:** Inserts one `lessons` row. SQLite supplies ID, creation
time, and default status `proposed`.

**External Interaction:** Local path validation, file reads, SQLite write. No
automatic correction capture, inference of intent, or execution of evidence tests.

**Output:** `{id, status: proposed}`. D-004.

## F-009 — Lesson confirmation, dispute, or supersession

**Trigger:** `memory status <id> confirmed|disputed|superseded`.

**Execution Path:** `cli.py:main()` → `build_index()` → `Memory.__init__()` →
`Memory.set_status()` → for confirmation, `Memory.list()` and freshness check →
UPDATE by ID → commit → close.

**Data Transformation:** Reject unknown IDs/statuses. Confirmation rejects stale
records. Dispute/supersede update status without refreshing evidence. There is no
state-transition policy beyond these checks and no link to a replacement lesson.

**Database Interaction:** Updates `lessons.status`; does not replace hashes or
append a review event. The freshness scan on confirmation currently reads all rows.

**External Interaction:** SQLite; confirmation also hashes local files.

**Output:** `{id, status}` or an error. Confirmation is developer attestation,
not independently established correctness. D-004.

## F-010 — Stale-lesson detection

**Trigger:** `Memory.list()` during listing, retrieval, or confirmation.

**Execution Path:** `memory.py:Memory.list()` → extract scope filename from ID →
`index.py:safe_path()` for evidence and scoped file → `digest()` → compare stored
hashes. Missing, unreadable, or rejected paths also set `stale = True`.

**Data Transformation:** Filesystem evidence produces a boolean on returned rows.
Any edit in either checked file invalidates freshness. Changes to other dependencies
are not checked. `status` remains unchanged even when a confirmed row becomes stale.

**Database Interaction:** No invalidation writes or schema column for `stale`.

**External Interaction:** Current local files; no watcher, worker, or Git history.

**Output:** A runtime `stale` flag. The compiler omits flagged rows; confirmation
asks for a new reviewed lesson. D-004.

## F-011 — Synthetic retrieval evaluation

**Trigger:** `python evals/run.py` or GitHub Actions.

**Execution Path:** `evals/run.py:main()` → `index.py:build_index(examples/refunds)`
→ read `evals/cases.json` → for each case, `context.py:compile_context(budget=4000)`
and `context.py:search(limit=20)` → compare returned IDs with expected IDs → JSON.

**Data Transformation:** Handwritten seed/expected sets become graph and lexical
recall values, missing expected IDs, and estimated context size. Seed itself is
excluded from retrieved comparison sets. The baseline is not token-budget matched.

**Database Interaction:** None; this calls the compiler directly without lessons.

**External Interaction:** Reads local fixture files. Does not run their test
functions, call a coding agent, use an LLM judge, or contact ContextBench.

**Output:** Labeled two-case smoke results; exit 1 if any graph-expected ID is
missing, otherwise 0. D-005.

## F-012 — Regression checks and CI

**Trigger:** `python -m unittest discover -s tests -v`; on GitHub, push/PR events.

**Execution Path:** `.github/workflows/checks.yml` → set up Python 3.11 → unittest
discovery → `tests/test_core.py:CoreTests.setUp()` → individual `test_*()` methods
→ cleanup. CI then runs `evals/run.py` (F-011).

**Data Transformation:** Tests create isolated Python repositories and assert
edges, ambiguity errors, budget behavior, memory eligibility/freshness, and CLI
JSON/exit codes. CLI tests use `subprocess.run([sys.executable, '-m', ...])`.

**Database Interaction:** Memory tests create and update temporary `lessons`
tables; production lesson data is not used.

**External Interaction:** Test files live under `.test-tmp/<uuid>`; setUp verifies
the resolved cleanup target is within that directory before registering recursive
cleanup. `Memory.close()` cleanups run before directory removal. CI setup downloads
its action/runtime dependencies; the Python checks require no model/network calls.

**Output:** Test report and process exit status. These checks establish prototype
behavior, not general agent success or security guarantees. D-005.
