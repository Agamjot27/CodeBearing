# Execution flows

This describes the code that exists, not the target architecture. Updated with the
initial documented Git baseline on 2026-10-03. Paths are relative to the repository.
Decision IDs refer to DECISIONS.md. Use `git log -p -- FLOW.md` to inspect changes.

## Current modification scope

WI-003 shares CLI/agent orchestration through `service.py:RepositoryService`,
introduces read-only `memory.py:Memory` access, and exposes five MCP tools.
F-001, F-003–F-005, F-013–F-015 route through the service; F-016 documents it and
F-017 documents transport/client execution. See
[its feature record](docs/work-items/WI-003-mcp-integration/FEATURE.md)
and [HANDOVER.md](HANDOVER.md) for current progress and next work.

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
| Git diff → affected symbols | F-013: base commit to tracked working tree, both code versions |
| Dependency graph expansion | F-004 (explicit symbols), F-014 (revision) |
| Context compilation | F-005 (explicit symbols), F-015 (revision) |
| Token-budget selection | F-006 |
| Engineering-memory retrieval | F-007 |
| Lesson proposal | F-008: manual input |
| Lesson confirmation | F-009 |
| Lesson invalidation / stale detection | F-010: computed on reads |
| MCP request | F-017: repository-bound read-only stdio tools |
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
`main()` parses arguments → constructs `service.py:RepositoryService(args.repo)`
→ dispatches search/changes/impact/compile to service methods (F-016), or calls
`index.py:build_index()` for index and developer memory commands → `json.dumps()`
→ stdout. Requests still rebuild indexes; no persistent graph cache exists.

**Data Transformation:** Arguments become a resolved repository `Path`, a fresh
`Index`, and command-specific inputs. Results become indented JSON.

**Database Interaction:** None in the shared path. Memory branches are below.

**External Interaction:** Local source filesystem and console; revision paths also
read Git (F-013). `ValueError`,
`OSError`, and `sqlite3.Error` are printed to stderr with exit code 2. Argument
errors are handled by argparse; successful commands return 0.

**Output:** Command JSON or a human-readable error. No web response or stream.

## F-002 — Repository indexing

**Trigger:** Any CLI command, or direct `build_index(root)` call.

**Execution Path:** `cli.py:main()` → `index.py:build_index()` → `os.walk()` →
`Path.read_bytes()` → `build_index_from_sources()` → `tokenize.detect_encoding()`
→ decode → `ast.parse()` → SHA-256 of captured bytes → create `Symbol` records →
resolve calls via `_body_walk()` and import/qualified-name maps → return `Index`.
For the `index` command, `main()` then calls `Index.describe()`.

**Data Transformation:** `.py` files become source strings and ASTs; top-level
functions and direct class methods become IDs of the form `path.py:Class.method`.
Module-level imports resolve aliases and relative module paths. Calls become
`edges[caller_id] = {callee_ids}`. SHA-256 file hashes, imports, source ranges,
excerpts, captured source bytes, and warnings are attached. Sources that fail
parsing remain in `Index.sources` for diff diagnostics but not `Index.hashes`.
Historical callers can invoke `build_index_from_sources()` without disk reads.
Shadowed names are conservatively skipped
for the local bindings recognized by the current analyzer.

**Database Interaction:** None. `Index.symbols`, `edges`, `warnings`, and `hashes`
live only in memory. `describe()` serializes call edges with `kind: calls`.

**External Interaction:** Reads local files without importing or executing them.
Prunes hidden/common dependency directories and directory symlinks; skips file
symlinks and files over 1 MB. Recorded parse/read failures become warnings.
There is no Git integration or atomic source snapshot.

**Output:** `Index` to library callers; its JSON description for the index command.
See D-001, D-002, and D-008.

## F-003 — Lexical seed search

**Trigger:** `search "refund_total"` after shared indexing.

**Execution Path:** `cli.py:main()` → `RepositoryService.search_symbols()` →
`build_index()` → `context.py:search(index, query)` → return
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
Revision impact uses F-014, including old/current expansion.

**Execution Path:** `cli.py:main()` → `RepositoryService.analyze_impact()` →
`build_index()` → `context.py:impact()` →
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
Revision compilation uses F-015; this section describes the explicit-symbol path.

**Execution Path:** `cli.py:main()` → `RepositoryService.compile_context()` →
`index.py:build_index()` → `context.py:impact()` → `RepositoryService._lessons()`
→ if memory DB exists, `memory.py:Memory.__init__(read_only=True)` →
`Memory.list(candidate_ids)` → `Memory.close()` →
`context.py:compile_context(index, seeds, budget, depth, lessons)` →
`impact()` again → packing (F-006) → service adds `excluded_lessons` → CLI JSON.

**Data Transformation:** Candidate IDs scope the memory read. The compiler creates
`text`, inclusion metadata, omitted IDs/reasons, included lesson IDs, missing seeds,
estimated token count, and warnings. The CLI adds status/staleness for rejected
lessons. Scope checks also exist in the compiler for direct library callers.
Currently graph expansion runs twice on the CLI path; no cache removes that work.

**Database Interaction:** If no memory file exists, none. Otherwise opens SQLite
with URI mode=ro and query_only enabled; `list()` reads existing rows without
schema creation or commit. Compilation does not add or confirm lessons.

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

**Trigger:** Developer `memory list`, compilation, or service lesson retrieval.

**Execution Path:** `cli.py:main()` → `memory.py:Memory.__init__(root)` →
`Memory.list(scopes=None or candidate_ids)` → F-010 freshness checks → return
records → `Memory.close()`. Compilation then applies F-006 eligibility checks.
Service reads use `Memory(read_only=True)`; developer list uses default writable
initialization, so listing from the developer CLI can still create empty storage.

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

Snapshot checks in `tests/test_snapshots.py:SnapshotTests` cover disk/snapshot parity
and source byte behavior. Revision checks in `tests/test_changes.py:ChangesTests`
create local Git fixtures under verified UUID paths, stage/commit baseline files,
call the new service/CLI, and clean up. `cleanup()` clears read-only flags only
within its verified fixture when Windows refuses Git-object deletion. No remote
push, network, or change to the main checkout occurs during these fixtures.

## F-013 — Git revision to changed symbols

**Trigger:** `changes --ref HEAD` (HEAD default) or `impact/compile --ref <commit>`.

**Execution Path:** `cli.py:main()` → `RepositoryService.localize_changes()`
(or revision impact/compile service method) → `changes.py:localize_changes()` → `_git()`
root check and ref resolution → `git ls-tree -rlz` → `git cat-file blob` →
`index.py:build_index_from_sources()` for historical code → `git ls-files --cached`
→ `build_index()` to capture disk bytes → `build_index_from_sources()` to restrict
current code to tracked files → Git name/status diff and untracked list →
`difflib.SequenceMatcher.get_opcodes()` per changed Python file → `_mapped()` on
old/new nonempty ranges → old-callers recovery → `Changes`.

**Data Transformation:** A ref becomes an immutable commit hash. NUL-delimited
paths/statuses avoid quoting ambiguity. Source lines become 1-based hunk starts
and line counts (zero counts mean no actual lines). Overlaps yield seed IDs.
Out-of-symbol lines seed all symbols in that version's file and add an unresolved
warning. Old touched IDs that survive, and their surviving direct old callers,
also become current seeds. Removed IDs remain historical. Parse/skipped source
and non-Python changes are unresolved. Non-content changes get a note.

**Database Interaction:** None; two in-memory indexes and a report.

**External Interaction:** Read-only Git subprocesses with argument arrays, disabled
fsmonitor hooks, no external diff/text conversion, and 30-second call timeouts.
No checkout, remote access, model calls, or execution of source. Current capture
is not atomic. Untracked files are reported but excluded; staged deletions with
leftover disk files do not resurrect them. Renames are explicit deletion/addition.

**Output:** `Changes(current, historical, report)`; `changes` CLI prints the report
with commit identity, file hunks, seeds, removed symbols, unresolved changes,
untracked exclusions, and warnings. Root mismatch/invalid ref/Git failure gives
an actionable CLI error. D-008, D-009.

## F-014 — Impact from a revision

**Trigger:** `impact --ref <commit> --depth <0–5>`.

**Execution Path:** `cli.py:main()` → `RepositoryService.analyze_impact()` → F-013 →
`changes.py:changes_impact()` → `context.py:impact()` independently for nonempty
current and historical seed lists.

**Data Transformation:** Old-caller recovery from localization supplies current
seeds even when the callee was removed. Each graph expands at the requested depth.
Empty seed sets produce empty results, not unknown-symbol errors.

**Database Interaction:** None.

**External Interaction:** Git/filesystem in F-013; expansion is in memory.

**Output:** Changes report plus separate current/historical candidates and reasons.
This is a conservative syntactic impact set, not proof of all semantic effects.

## F-015 — Compile revision context and current memory

**Trigger:** `compile --ref <commit> --max-tokens <budget> --depth <0–5>`.

**Execution Path:** `cli.py:main()` → `RepositoryService.compile_context()` → F-013
→ current seed expansion with `impact()` → `_lessons()` → if a lesson database
exists, `Memory(read_only=True)` → `Memory.list(current_candidate_ids)` / `close()` →
`changes.py:compile_changes()` → `context.py:compile_context()` first for current,
then historical seeds with remaining budget → service attaches `excluded_lessons`.

**Data Transformation:** A provenance header and per-version labels count against
the shared estimated text budget. Existing whole-excerpt packing runs separately
against each graph. Historical headers include the immutable base commit. Lessons
are supplied only to the current compiler. A remaining budget below 128 explicitly
omits that version's seeds. Nested package metadata excludes duplicate text.
`complete` requires no packing omissions and no unresolved localization changes;
it still does not prove semantic sufficiency. An unchanged comparison is valid
and returns no symbol evidence.

**Database Interaction:** Reads existing current lessons through F-007/F-010;
does not confirm or update lessons. No historical memory database is opened.

**External Interaction:** Read-only Git and files during localization; optional
local SQLite. No LLM or coding-agent execution.

**Output:** One context `text`, estimated usage/budget, changes report, per-version
inclusions/omissions/missing seeds, memory metadata, completeness, and warnings.
Total text accounting remains heuristic and metadata lies outside the budget.
D-003, D-004, D-009.

## F-016 — Shared repository request service

**Trigger:** CLI search/changes/impact/compile and MCP handlers use the same
service. `RepositoryService(root)` fixes a resolved, existing directory once.

**Execution Path:** `service.py:RepositoryService.search_symbols()` → `build_index()`
→ `context.search()`; `localize_changes()` → `changes.localize_changes()`;
`analyze_impact()` and `compile_context()` → `_validate()` → existing index/changes
and context functions (F-004/F-005/F-014/F-015). `get_lessons(symbols)` → `_validate()`
→ `build_index()` → `select_symbol()` → `_lessons()` → `Memory(read_only=True)` →
`list()` → `close()` → confirmed/fresh filtering.

**Data Transformation:** Exactly one symbols/ref selector; 1–20 nonempty symbols;
depth 0–5; query/ref up to 2000 characters; search limit 1–50; context budget
128–32000 estimated tokens. Core result structures are preserved. Lesson retrieval
returns eligible text plus metadata for rejected records, never proposed advice.

**Database Interaction:** Existing lesson SELECTs only in agent/context reads.
`mode=ro` prevents database creation and query_only rejects SQL mutations. Missing
memory returns empty results. Default developer Memory methods remain writable.

**External Interaction:** Local parsing/hashing and optional read-only Git/SQLite.
No SDK dependency, network, or LLM in this layer.

**Output:** Core-compatible dictionaries or actionable validation/database errors.
`tests/test_service.py:ServiceTests` checks parity, no creation, SQL/method write
rejection, filtering/freshness, unchanged DB bytes, and request bounds. D-010.

## F-017 — MCP startup, tool requests, and client demonstration

**Trigger:** An MCP host launches `python -m diffcontext --repo <root> serve`, or
`examples/mcp_client.py` runs its model-free demonstration.

**Execution Path:** `__main__.py` → `cli.py:main()` serve branch → lazy import
`mcp_server.py:create_server(root)` → `RepositoryService(root)` → official SDK
`MCPServer.run(transport="stdio")`. Client initialization/discovery is handled by
the SDK. A tool call invokes the corresponding nested function in `create_server()`:
`search_symbols()`, `localize_changes()`, `analyze_impact()`, `compile_context()`,
or `get_lessons()` → `_call()` → same-named `service.py:RepositoryService` method
→ F-016 and its relevant core flows → SDK response to the client. Synchronous
handlers use the SDK worker threads; there is no application job queue/worker.

`examples/mcp_client.py:demonstrate()` → `StdioServerParameters` → `Client` async
context (starts subprocess/initializes) → `list_tools()` → `call_tool("search_symbols")`
→ first lexical match ID → `call_tool("compile_context")` → print JSON → client
context closes the process. This demo's automatic first match is not a planner.

**Data Transformation:** Pydantic annotations produce SDK input schemas and enforce
bounds. Service validation enforces exactly one selector and resolves symbols.
Python dictionaries become structured tool content plus SDK text representation.
`_call()` converts expected ValueError/OSError/SQLite failures to `ToolError`;
the SDK returns a tool error without terminating the session. Unexpected failures
retain SDK diagnostics. Read-only hints describe tools but do not enforce OS isolation.

**Database Interaction:** Existing SQLite SELECTs only for compilation/lessons
through F-016. No memory creation, mutation tools, or developer confirmation.

**External Interaction:** Local stdin/stdout protocol; Git/filesystem/SQLite as
described in core flows. stdout is reserved for protocol, stderr for diagnostics.
No HTTP API, frontend, remote provider, model call, source/test execution, or network
interaction in the tools. The optional dependency is imported only for `serve`.

**Output:** Five discoverable tools, structured results and recoverable errors.
Compilation budgets only result `text`, not metadata/MCP overhead. Tests in
`tests/test_mcp.py:MCPTests` exercise contracts/memory; `StdioTests` uses a real
subprocess with historical/current Git evidence. Missing SDK skips these tests
unless `DIFFCONTEXT_REQUIRE_MCP=1`, used by the separate MCP CI job. D-011/WI-003.
