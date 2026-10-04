# Execution flows

This describes the code that exists, not the target architecture. Updated with the
initial documented Git baseline on 2026-10-03. Paths are relative to the repository.
Decision IDs refer to DECISIONS.md. Use `git log -p -- FLOW.md` to inspect changes.

## Current modification scope

WI-013 adds explicit OpenRouter evaluation and usage-preserving error accounting
(F-032), extending F-023/F-024/F-031. MCP/source retrieval does not call a model.

WI-011 replaces grading/adapter pipe capture with bounded file-backed execution
(F-030), modifying F-021/F-022. WI-012 adds explicit hybrid experiment controls
(F-031), extending F-022–F-024; existing four-control defaults are retained.

WI-009 adds code-aware lexical/graph/reviewed-memory retrieval and task lesson
reservation (F-029), extending service/investigation F-016/F-018, packing F-006,
summary F-019 and MCP F-017. The six tool names remain; search/investigate gain
a hybrid/legacy policy argument. See
[its feature record](docs/work-items/WI-009-hybrid-retrieval/FEATURE.md)
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
| Repository indexing | F-002/F-027; opt-in persistence F-028 |
| Incremental re-indexing | F-028: content-validated parse reuse; full graph relinking |
| Natural-language task → localization | F-029: hybrid ranking and bounded seed selection; F-003 legacy; no semantic planner |
| Git diff → affected symbols | F-013: base commit to tracked working tree, both code versions |
| Dependency graph expansion | F-004 (explicit symbols), F-014 (revision) |
| Context compilation | F-005 (explicit symbols), F-015 (revision) |
| Token-budget selection | F-006 |
| Engineering-memory retrieval | F-007 |
| Lesson proposal | F-008: manual input |
| Lesson confirmation | F-009 |
| Lesson invalidation / stale detection | F-010: computed on reads |
| MCP request | F-017: repository-bound read-only stdio tools |
| Investigation loop | F-018: deterministic controller via CLI/MCP |
| Evaluation execution | F-011 and F-012 |
| Frontend Context Explorer | Not implemented |
| Run Inspector / trace loading | F-019: CLI saved-JSON inspector; web UI/persistent registry not implemented |

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
→ stdout. `--cache` propagates through service/build paths to F-028; otherwise
requests parse afresh. Investigation and installed launch flows are below.

**Data Transformation:** Arguments become a resolved repository `Path`, a fresh
`Index`, and command-specific inputs. Results become indented JSON.

**Database Interaction:** No shared storage without `--cache`; F-028 stores derived
index state when enabled. Memory branches remain separate.

**External Interaction:** Local source filesystem and console; revision paths also
read Git (F-013). `ValueError`,
`OSError`, and `sqlite3.Error` are printed to stderr with exit code 2. Argument
errors are handled by argparse; successful commands return 0.

**Output:** Command JSON or a human-readable error. No web response or stream.

## F-002 — Repository indexing

**Trigger:** Any CLI command, or direct `build_index(root)` call.

**Execution Path:** `cli.py:main()` → `index.py:build_index()` → `capture_sources()`
→ `os.walk()`/`Path.read_bytes()` → `build_index_from_sources()` →
`_build_python_index()` → `_python_unit()` → `tokenize.detect_encoding()`/decode/
`ast.parse()` → Symbol/call facts → qualified-map linking → return `Index`.
Web adapters follow F-027; cached parsing/publication follows F-028.
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

**Database Interaction:** None in the uncached path. `Index.symbols`, `edges`,
`warnings`, and `hashes` are returned in memory. Opt-in persistence follows F-028. `describe()` serializes call edges with `kind: calls`.

**External Interaction:** Reads local files without importing or executing them.
Prunes hidden/common dependency directories and directory symlinks; skips file
symlinks and files over 1 MB. Recorded parse/read failures become warnings.
There is no Git integration or atomic source snapshot.

**Output:** `Index` to library callers; its JSON description for the index command.
See D-001, D-002, and D-008.

## F-003 — Legacy lexical seed search

Selected by `retrieval="legacy"`; default search/task investigation now uses F-029.

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
Graph expansion still runs twice on the CLI path; parse caching does not remove
that work. See F-028 for the separate indexing cache.

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

Default search now follows F-029, including read-only reviewed-memory ranking;
the lexical call below describes retrieval="legacy". Other service paths remain.

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
`get_lessons()`, or `investigate()` → `_call()` → same-named `service.py:RepositoryService` method
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

**Output:** Six discoverable tools, structured results and recoverable errors.
Compilation budgets only result `text`, not metadata/MCP overhead. Tests in
`tests/test_mcp.py:MCPTests` exercise contracts/memory; `StdioTests` uses a real
subprocess with historical/current Git evidence. Missing SDK skips these tests
unless `DIFFCONTEXT_REQUIRE_MCP=1`, used by the separate MCP CI job. D-011/WI-003.

## F-018 — Bounded context investigation

For hybrid task selectors, replace the lexical search and BFS packing portions
below with F-029. Explicit symbols/ref and retrieval="legacy" retain this path.

**Trigger:** `service.py:RepositoryService.investigate(task|symbols|ref, limits)`.
From `cli.py:main()` investigate branch or `mcp_server.py:create_server():investigate()`
via `_call()`. The CLI can apply `runs.py:summarize()` after the run.

**Execution Path:** `RepositoryService.investigate()` → `investigation.py:run()`
→ validate exactly one selector/limits → `build_index()` or
`changes.py:localize_changes()` once → `_identity()` for captured version(s) →
service `_lessons(all_current_symbol_ids)` → compare lesson evidence/scope hashes
with captured hashes → lexical `context.py:search()` OR `index.py:select_symbol()`
OR localized old/current seeds → for each increasing depth: `context.py:impact()`
for each nonempty version → relevant lessons → `context.py:compile_context()` or
`changes.py:compile_changes()` → `_frontier()` → observable verification → expand
or stop. Nested `event()`, `exhausted()` and `finish()` record the run and limits.

**Data Transformation:** Captured source-byte digests become snapshot IDs. Task
search records up to 50 matches and selects at most three tied top-scoring IDs;
larger ties/no matches return needs_input. Exact seeds are normalized once.
Graph sets become versioned unexplored frontiers; packages expose missing seeds,
omissions, unresolved changes, excluded untracked files and source warnings.
Budget omissions stop immediately; other source gaps remain visible while known
edges expand within limits. Empty revision seeds return no_changes only when no
unresolved/untracked gaps exist. A ready result means selected static graph coverage,
not semantic correctness. Steps count capture/search/compile operations; trace
events are not extra calls. Each depth is attempted at most once.

**Database Interaction:** Existing lessons SELECT once through read-only F-016.
No writes, proposal, confirmation, or new run tables. Lesson validity is checked
against captured current hashes in addition to live-file freshness.

**External Interaction:** Local filesystem and optional read-only Git/SQLite only.
No model, network, worker, code edits, or source/test execution. Monotonic deadline
checks occur between operations and after compile; they cannot interrupt work.

**Output:** Schema_version 1 inline JSON-ready report with run_id, selectors, limits, usage,
snapshot IDs, search matches, versioned seeds, latest context, verification and
ordered trace. Status is ready/partial/needs_input/no_changes; stop_reason identifies
graph coverage, budget/depth/step/time limits, localization gaps or missing input.
Invalid requests/core failures raise normal service errors. D-012/WI-004.

## F-019 — Summary and saved-run inspection

**Trigger:** `investigate --summary` or `inspect <full-run.json>`.

**Execution Path:** `cli.py:main()` investigate branch → F-018 →
`runs.py:summarize(report)` → JSON. For saved input, `cli.py:main()` inspect branch
before RepositoryService creation → `runs.py:load_summary(path)` → bounded binary
read → UTF-8-sig decode → `json.loads()` → `summarize()` → JSON.

**Data Transformation:** Check schema_version 1 and needed field shapes. Full
context source text becomes versioned citation/lesson metadata. Keep search matches,
selectors, limits, usage, snapshot IDs, verification, warnings and compact trace
decisions. Unsupported/malformed encoding/JSON/format or oversized input raises an
actionable error. Full results are saved only by explicit user redirection, not by
the application. Summary output is not a reloadable report.

**Database Interaction:** None in inspection. Summary after a new investigation
inherits the read-only lesson interactions of F-018.

**External Interaction:** Saved file read capped at 10 MB; no repository re-index,
Git/model/network/worker execution. The original repository need not exist.

**Output:** Compact JSON without source bodies. Inspection failure exits two through
CLI error handling; successful partial/needs_input run delivery still exits zero.
`tests/test_investigation.py` verifies CLI save/load, BOM, absent repository,
malformed/oversized input and summary behavior. D-013/WI-004.

## F-020 — Investigation development fixtures

**Trigger:** `python evals/investigate.py`, including the core CI job.

**Execution Path:** `evals/investigate.py:main()` → read
`evals/investigation_cases.json` → `build_index(examples/refunds)` for baseline →
`RepositoryService.investigate(**request)` per case (F-018) →
`context.py:compile_context(same_selected_seeds, same_max_budget, depth=0)` →
compare expected IDs/status/stop_reason, estimated text budget and operation limit.

**Data Transformation:** Six labeled development requests become inclusion recall,
termination results, estimated text usage, operation counts and explicit pass/fail.
Cases cover task and helper expansion, no match, and budget/depth/step limits.
No expected answers enter task localization; labels are used only for scoring.

**Database Interaction:** Existing memory would be read-only; the committed example
has no database, and evaluation does not create one.

**External Interaction:** Local JSON/source files only. No Git, model/provider,
network, worker, or repository test execution. This is retrieval/controller checking.

**Output:** JSON results and exit zero only when every case passes. Comparison holds
chosen seeds and maximum text budget equal, not actual output token usage. These
development fixtures are not independent coding outcomes or model-cost evidence.
D-013/WI-004. Earlier two-case smoke evaluation remains unchanged at F-011/F-012.

## F-021 — Coding-fixture calibration, source application and grading

**Trigger:** `coding.py:calibrate(load_suite(manifest), scratch)` or per-trial grade.
Driver: `evals/coding_bench.py` calibrate/self-check or experiments per-trial grade.

**Execution Path:** `coding.py:load_suite()` → read suite manifest and validate IDs,
asset containment/source allowlists → `calibrate()` → `trial_workspace()` creates
UUID child under scratch and copies only repo/*.py (recursively) → `grade()` →
Python subprocess `-I -B -c GRADER` → public unittest discovery → external trusted
`checks.py` loaded with runpy → combined test suite → CHECK_RESULT JSON/exit status →
`apply_edits(reference)` → repeat grade → contained workspace cleanup.

**Data Transformation:** Suite rows become immutable CodingTask records. Candidate
full-file text is validated for source allowlist, string content, containment and
200 KB total size before any write. Snapshot source hashes identify inputs/output.
Test records, exit status, elapsed time and diagnostic tails become grade outcomes:
passed/test_failed/timeout/grader_error. Missing/malformed result output does not pass.
Calibration requires the untouched fixture to actually run tests and fail, and
the reference to pass. Syntax errors are failed candidates, not model/provider errors.

**Database Interaction:** None in fixture calibration.

**External Interaction:** Explicit fixture filesystem copies/edits/cleanup and local
Python test subprocesses with timeout. No Git/model/network calls. Subprocess code
has ordinary caller permissions: this is not a security sandbox. The fixture root
contains no checks/reference files; grading material is loaded only after context
preparation/candidate application. Repositories/checks are trusted local assets.

**Output:** Calibration report labeled reference-fix checking, not model outcomes.
Four regression tests cover calibrated tasks, asset separation/atomic edit rejection,
syntax errors, timeout and fresh trials. D-014/WI-005.

## F-022 — Coding prompt preparation and memory controls

F-031 extends this flow with opt-in hybrid treatments and explicit policy diagnostics.

**Trigger:** `evals/coding_bench.py prepare --model --output`, or trial setup.

**Execution Path:** script `main()` → `coding.py:load_suite()` →
`experiments.py:export_requests()` → `_config()`/`initialize()` → `_trials()`
rotated condition order → `trial_workspace()` → `make_request()` → for memory:
`_seed_memory()` → `Memory.add()`/`set_status(confirmed)` → optional stale evidence
comment append → lexical condition `build_index()`/`context.search()` plus complete
matched-file packing OR `RepositoryService.investigate()` (F-018) → prompt budget
check → `source_hashes()`/`fingerprint()` → atomic `write_json(request)` → cleanup.

**Data Transformation:** Same task/instructions/query/settings become condition-
specific evidence. Reserve task/instruction overhead from the maximum estimated
full prompt budget. Pack only whole matched files for lexical baseline; graph/memory
use current investigator. Packet stores prompt, editable paths, requested model,
temperature/output limits, source hashes and stable request_hash. Diagnostics store
inclusions/omissions/warnings, lessons and preparation time. No runtime run UUID or
timing contaminates the stable packet fingerprint.

**Database Interaction:** Synthetic Memory INSERT/confirmation in disposable trial
copies only for memory controls, followed by existing read-only retrieval. Stale
control changes the evidence comment after confirmation. Original source/database
and developer memory are not changed; lessons are labeled authored fixture data.

**External Interaction:** Local copies, JSON, source and SQLite only. No provider,
Git or candidate execution in prepare. Check/reference bytes are hashed only for
experiment provenance outside packets; content is never included by preparation.

**Output:** Twelve default JSON packets under output/requests plus manifest; no
model results. IDs/labels are development hints, not a zero-shot localization test.
D-015/WI-005.

## F-023 — Candidate execution, checkpoints and quota-aware resumption

**Trigger:** `coding_bench.py run --model --output` with `--command-file`,
`--command-json` or `--replay`. File arguments are decoded as UTF-8-sig JSON arrays.

**Execution Path:** script `main()` → `CommandRunner()` or `ReplayRunner()` →
`experiments.py:run_experiment()` → `_config()`/`initialize()` → adapter identity
check → `_trials()` → fresh `trial_workspace()` → `make_request()` → validate
checkpoint request_hash/reuse scored row OR write packet → `coding.grade()` baseline
failure check → runner(request) → `validate_response()` → `coding.apply_edits()` →
`coding.grade()` candidate → acceptance-failure intersection → atomic trial checkpoint
→ `summarize_results()` → report.json → cleanup.

**Data Transformation:** Command runner sends packet JSON on stdin and parses one
stdout JSON response; no shell. Replay maps trial_id to collected responses. Validate
schema/model/hash/status/usage and declared output limit before applying code.
Allowlist/payload rejection is invalid_candidate; executable outcomes include passed,
test_failed and candidate timeout. Provider/quota/process/protocol/budget/grader errors
remain unscored. Quota stops new dispatch but retains already scored checkpoints.
Explicit resume retries unscored rows; changed settings/assets/adapter/packet refuse
reuse. Expected task outcomes never enter prompts. Source edits and diagnostics are
saved for reproducibility; provider logs are not copied blindly into errors.

**Database Interaction:** F-022 disposable lesson storage only. No experiment DB.
JSON checkpoints are per-trial files, replaced atomically after complete outcomes.
Transient attempt history is retained when an unscored trial is retried.

**External Interaction:** Explicit local output/scratch paths, runner subprocess or
recorded file read, and trusted grading subprocesses. External model/network calls
occur only if the user-selected adapter performs them. No live adapter is configured
by the harness. Imports/processes are isolated but OS permissions are not sandboxed.

**Output:** Trial rows with config/model/request identity, condition diagnostics,
baseline/candidate grades, timing, runner-reported usage, accepted response edits and
persisting acceptance-failure IDs. Grader timeout is distinct from runner timeout.
Nine experiment tests exercise IPC, replay, provenance, memory/budget/leakage, invalid
edits, provider/quota classification and scored checkpoint reuse. D-015/WI-005.

## F-024 — Coding report aggregation and model-free harness self-check

F-031 extends aggregation/self-check to the selected four/seven-condition set.

**Trigger:** End of run or `python evals/coding_bench.py self-check` (core CI).

**Execution Path:** `experiments.py:summarize_results()` → group by condition →
scored denominator → matched lexical/graph, graph/memory, graph/stale tasks → report.
For self-check: script `main()` → F-021 `calibrate()` → F-023 twice with explicit
`CalibrationRunner(reference=True/False)` → reference runner reads reference JSON
only inside this privileged calibration path → verify all reference passes, all
unchanged failures, confirmed retrieval and stale exclusion → compact self-check JSON.

**Data Transformation:** Scored outcomes produce per-condition success rates;
unscored errors stay separate. Matched comparisons count wins/losses only for jointly
scored tasks. Cost sums only when every checkpointed attempt reports it; otherwise null.
Timing/estimated prompt and provider usage remain per trial. Calibration outcomes
are labeled test-harness checking, not model accuracy or memory efficacy.

**Database Interaction:** Only disposable memory from F-022; no aggregate DB.

**External Interaction:** Local result files and calibration grading. Self-check
performs zero model/network calls. Ordinary experiment provider activity depends
on its explicit adapter; replay has none. No automatic retry/concurrency.

**Output:** report.json plus CLI JSON. Exit 0 means complete scored experiment,
including all-failed candidates; 1 means failed calibration/unscored incompletion;
2 means invalid configuration/file input. Default self-check calibrates three bugs
and checks 12 reference/12 unchanged trials. D-015/WI-005.
## F-025 — Installed MCP launch and client configuration

**Trigger:** Assistant executes generated config, or user runs
`diffcontext-lab-mcp --repo <root> [--config claude|cursor|codex]`.

**Execution Path:** `pyproject.toml` console entry → `diffcontext/connect.py:main()`
→ resolve/validate root → config mode `configuration()` → print JSON/TOML; or
lazy import `mcp_server.py:create_server(root)` → `RepositoryService(root)` →
SDK `run(transport="stdio")` → existing F-017 tool dispatch/F-016 service calls.
Generated configs invoke installed Python `-m diffcontext.connect`, using this
same path without relying on executable discovery in the GUI host's PATH.

**Data Transformation:** User repository becomes an absolute existing directory.
Config uses the owning interpreter, module and repository argument array;
Claude adds type=stdio. JSON string escaping also serves TOML basic path strings.
Missing root/dependencies fail with stderr and nonzero exit. Server stdout is MCP
protocol only; config mode prints config without importing the optional SDK.

**Database Interaction:** None in configuration/startup. Tool memory reads follow
F-016; no host configuration files are written. No new database/entity introduced.

**External Interaction:** Local interpreter/filesystem and host subprocess pipes.
No HTTP, worker, model/provider call, repository execution or automatic settings
mutation. The external coding assistant may send returned code to its model.

**Output:** Mergeable configuration or the six-tool local server. One fixed root
per launch; user must enable/approve the server in the host. D-016/WI-006.

## F-026 — Connection and clean distribution validation

**Trigger:** `diffcontext-lab-mcp --repo <root> --check`, or
`python scripts/check_wheel.py <wheel>` (also in the MCP CI job).

**Execution Path:** `connect.py:main()` → `asyncio.wait_for(check_connection())`
→ SDK `Client(StdioServerParameters)` → installed Python child F-025 →
`list_tools()` → compare six names → `call_tool(search_symbols)` → F-016 search
→ validate structured result → print connection JSON → close child.
Distribution: `scripts/check_wheel.py:verify()` → inspect ZIP → create disposable
venv → `run(pip --python ... install wheel[mcp])` → copy refund fixture into path
with spaces → run installed core index/help → generate/parse three client configs
→ installed launcher --check → assert no memory state created → constrained cleanup.

**Data Transformation:** MCP discovery/search becomes status, tool names and parser
warnings. It checks transport, not retrieval accuracy or host integration. Wheel
check validates ownership of interpreter/repo paths, excludes development artifacts,
and runs outside the importable checkout root. TOML parsing uses Python 3.11+;
3.10 remains a core runtime target. Check timeout is 45 seconds; subprocess
distribution operations each have a 240-second timeout.

**Database Interaction:** None created; search only reads/parses source. The wheel
fixture assertion detects accidental repository-local state creation.

**External Interaction:** Local ZIP, venv, source files and subprocess pipes.
Pip may download optional dependencies; no provider/model or publishing call.
No assistant settings edited, no HTTP server or worker introduced.

**Output:** Connection JSON or stderr/nonzero failure; wheel passed JSON after
installation/entry-point/config/protocol checks. D-016/WI-006.

## F-027 — Optional TypeScript/JavaScript snapshot indexing and downstream reuse

**Trigger:** CLI/MCP indexing, search, compilation or investigation for a repository
containing supported web source; Git localization also builds historical snapshots.

**Execution Path:** `cli.py:main()` or `mcp_server.py:create_server()` tool →
`service.py:RepositoryService` operation → `index.py:build_index()` → directory
scan using `is_source_path()` → `build_index_from_sources()` → validate captured
paths/size → `_build_python_index()` for Python → optional
`typescript.py:extend_index()` for web bytes → grammar `Parser.parse()` →
`_definitions()`/`_imports()`/`_put_export()` → Symbol construction → `_shadowed()`
and `_resolve_module()` resolve eligible calls → shared Index returned.
`changes.py` uses `is_source_path()` for current paths and historical Git blobs,
then the same snapshot adapter; deletion recovery follows F-013–F-015.
`context.py:search()`/`impact()`/`compile_context()` consume the shared graph;
`memory.py` hashes evidence and scope as before; F-016–F-018 expose results through
the same six tools/investigator. No language-specific second service is introduced.

**Data Transformation:** Captured raw bytes → valid syntax tree → callable IDs
`relative/path.ts:name`, language field, exact byte-sliced excerpts/line ranges,
imports and SHA-256 hashes → caller/callee sets. Invalid UTF-8/error trees retain
captured bytes but no parsed symbols/hash. Missing extras leave Python intact and
list unindexed web files. Ambiguous/import/type/dynamic gaps stay explicit; compiler
metadata also explains universal syntax-graph limitations. No cross-language
runtime edge is guessed. Selection and token estimates follow existing F-003-F-006.

**Database Interaction:** Uncached adapter calls use no persistent symbol/edge
tables. Optional caching follows F-028. Confirmed lessons use the existing SQLite schema and evidence hashes; read-only
service operations do not create the database. No worker or graph database.

**External Interaction:** Filesystem and, for revision tools, Git blob reads.
Optional local parser libraries; no Node/build, target-code execution, network or
LLM. Installing the extra may download packages.

**Output:** The same index/search/context/change/investigation JSON contracts with
web-language evidence and warnings. `evals/typescript.py:main()` indexes the authored
refund fixture and calls `compile_context()` at two budgets to check expected IDs,
whole excerpts and estimated tokens; no provider or coding-benefit measurement.
`scripts/check_wheel.py:verify(..., typescript=True)` extends F-026 by installing
both extras, copying the web fixture and checking installed compilation. D-017/WI-007.

## F-028 — Persistent parse reuse, graph refresh and cache-enabled requests

**Trigger:** CLI `--cache` or launcher configuration/startup with `--cache`.

**Execution Path:** `cli.py:main()` or `connect.py:main()` →
`mcp_server.py:create_server(cache=True)` → `RepositoryService(cache=True)` →
`service.py:_index()` → `index.py:build_index(cache=True)` → `capture_sources()` →
`index_store.py:build_cached_sources()` → `IndexStore.__init__()/load()` →
`parser_fingerprint()` plus byte/checksum validation →
`index.py:build_index_from_sources(units=...)` → `_build_python_index()` uses
`_python_unit()` only for absent units; web `typescript.py:extend_index()` uses
`_parse_unit()` only for absent units → complete current-symbol/import map →
resolve cached/new call facts → `IndexStore.publish()` for a changed generation →
Index with counters → existing search/impact/compile/lesson paths and MCP response.
Unchanged generations avoid publication writes. `investigation.py:run(cache=True)`
captures once and retains `indexing` in reports; `runs.py:summarize()` preserves it.

Revision path: `service.py:_changes()` → `changes.py:localize_changes(cache=True)`
→ Git historical blobs → uncached `build_index_from_sources()` →
`capture_sources()` → tracked-current filter → `build_cached_sources()` → existing
old/current hunk mapping and deletion recovery. Current filtering now precedes
parsing in uncached mode too; untracked code is not parsed twice or used as evidence.

**Data Transformation:** Fresh eligible bytes → SHA-256/parser fingerprints →
validated JSON per-file facts (symbols, aliases/exports, warnings, call references)
→ globally resolved graph. Syntax failures may reuse failure facts, retain bytes
and have no successful hashes. Edits/new files replace facts; removed paths vanish.
Schema/root mismatches reset derived tables; checksum/parser mismatch reparses;
malformed payload reparses all current facts. Cache I/O errors add warnings while
returning current evidence. Counters distinguish reused/parsed/uncached/removed
files; cache pipeline time excludes capture, which ordinary current builds measure
separately. Git/historical costs are outside current-cache counters.

**Database Interaction:** `.diffcontext/index.sqlite3` tables `metadata`, `files`,
`symbols`, `edges`; transactional generation publication. No lesson-table writes;
`memory.sqlite3` stays separate. No graph server or worker. Without `--cache`, no
cache database is opened and previous no-state retrieval behavior remains.

**External Interaction:** Local reads, optional local parsers, SQLite and Git for
revision tools. No network, LLM, target-code execution or host-settings changes.
`connect.py:configuration(cache=True)` prints `--cache` without opening storage.
`check_connection(cache=True)` propagates the choice into its MCP child.

**Output:** Existing evidence responses plus optional `indexing` metadata.
`evals/indexing.py:main()` → authored workload → `measured()` → full/cold/warm/edit
builds → `same_graph()` and parse-count gates → timing JSON. Clean wheel F-026 also
checks cache persistence between installed CLI indexing and MCP search. D-018/WI-008.

## F-029 — Hybrid task localization, graph ranking and scoped lesson packing

**Trigger:** CLI search/investigate or MCP search_symbols/investigate; default
`retrieval="hybrid"`. Selecting `legacy` runs the original overlap/packing path.

**Execution Path:** `cli.py:main()` or `mcp_server.py:create_server()` handler →
`service.py:RepositoryService.search_symbols()` → `_index()` (F-028 if enabled)
→ `_lessons(set(index.symbols))` → `retrieval.py:hybrid_search()` → `_lexical_rows()`
→ `_tokens()`/`_bm25()` weighted name/path/body scores → `_memory_signals()` →
`eligible_lessons()` checks captured hashes/status → normalized/capped blend →
ranked match response. No graph traversal is performed by the search tool itself.

Investigation: `RepositoryService.investigate()` → `investigation.py:run()` →
one source/index capture and lesson snapshot → `hybrid_search()` → best-score ties
up to three seeds (otherwise needs_input) → for each bounded depth,
`retrieval.py:rank_candidates()` → `context.py:impact()` pool → lexical/graph/memory
candidate scores, seed-first order → eligible scoped lessons/query-match priority
→ `compile_context(candidates=..., lesson_budget=max_tokens//5,
require_lesson_scope=True)` → verify frontier/omissions/gaps → expand or return.
Detailed candidates/signals appear in context.retrieval and search_matches;
`runs.py:summarize()` preserves policy metadata. Existing step/time limits apply.
Explicit symbol/Git selectors keep F-018's prior packing path. `experiments.py:
make_request()` explicitly uses legacy for existing graph/memory treatments.

**Data Transformation:** Task text → full/split identifier tokens and conservative
suffix variants → per-field BM25 → exact-name priority and capped scoped memory
signals → seeds → bounded static graph → ranked whole excerpts. Compiler validates
the ranked pool matches impact; detailed lexical explanations remain outside text.
Eligible lesson sections reserve at most 20% of budget, but optional advice never
hides a seed that fits the full budget. Lessons whose scoped code is omitted are
omitted too. Every final section still passes the estimated whole-text budget.
Scores are heuristics; no-match/large exact ties remain requests for input.

**Database Interaction:** Existing lessons SQLite is opened read-only, if present;
no lesson confirmation or search-state writes. Optional derived parse storage
follows F-028. Query ranks are not cached; no vector/embedding database or new table.

**External Interaction:** Local source/SQLite/optional parsers; Git only for the
unchanged revision selector path. No provider, model, target execution, HTTP or
worker. Search may reread evidence for freshness before captured-byte validation.

**Output:** Ranked IDs/reasons/signals and optional indexing counters; task run
context plus policy, scored candidates, omissions, lessons and trace. Six tool
names unchanged; search/investigate gain a retrieval enum. `evals/hybrid.py:main()`
→ authored fixtures → same captured Index/lessons per pair → legacy/hybrid search
and compilation → recall/precision/MRR/budget/eligibility/abstention/latency JSON.
This is a development retrieval comparison, not live coding outcomes. D-019/WI-009.

## F-030 — Bounded grading and command-adapter execution

**Trigger:** coding.py:grade() or experiments.py:CommandRunner.__call__().

**Execution Path:** caller builds argv/input → processes.py:run_bounded() →
TemporaryFile input/stdout/stderr → Popen(shell=False, POSIX new session) →
wait(timeout) → on timeout _stop_tree() → Windows taskkill owned PID / POSIX
killpg → bounded wait → TimeoutExpired to caller; otherwise _tail() → ProcessResult.
Cleanup failure raises OSError: grade returns grader_error; adapter provider_error.

**Data Transformation:** JSON request → UTF-8 file stdin. Output bytes → retained
tail, UTF-8 replacement decoding and universal newlines. Grader retains 64 KB
stdout / 4 KB stderr and parses CHECK_RESULT. Runner retains 250 KB stdout,
rejects truncation then parses JSON; stderr is never checkpointed. Timeout keeps
the existing timeout/runner_timeout classifications when cleanup succeeds.

**Database Interaction:** None. Existing experiment checkpoint files unchanged.

**External Interaction:** Trusted grader/adapter command, temporary local files,
owned-process OS termination. No new model/network/worker integration. Adapter
may contact its configured provider externally; helper does not select one.
Disk output has no quota and this is not a security sandbox.

**Output:** Completed ProcessResult or bounded execution/cleanup exception;
unchanged grade results and adapter response/error contracts. D-020, WI-011.

## F-031 — Paired hybrid coding controls and provenance

**Trigger:** coding_bench.py:main() with --condition-set hybrid, or experiment
functions with conditions=HYBRID_CONDITIONS. Default remains CONDITIONS (legacy four).

**Execution Path:** main() chooses tuple → experiments.py:_conditions() validates
unique supported names → export_requests()/run_experiment() → _config() task assets,
package source hashes, policy_version=2, selected conditions → initialize() checks
manifest equality → _trials() rotates selected order → fresh trial_workspace() →
make_request() → optional _seed_memory() → RepositoryService.investigate() with
hybrid for the three new names, legacy for old graph/memory names → request hash
→ unchanged F-023 runner/quota/checkpoint/grading → summarize_results() selected
condition summaries and eight possible scored-only pairs → report.json.

**Data Transformation:** Same task, settings and total estimated prompt budget
produce different cited evidence. Fresh/stale pairs share identical source hashes
across legacy/hybrid. Diagnostics disclose retrieval_policy, seeds, included_symbols,
lessons and preparation time. Source/config/condition changes reject resume before
dispatch. Unscored provider errors are excluded from paired task denominators.

**Database Interaction:** Only disposable memory.sqlite3 for four memory controls,
confirmed synthetic lesson and normal freshness reads. No report database.

**External Interaction:** Local assets, source hashing, JSON checkpoints, bounded
trusted grading/adapter subprocesses (F-030). Real network/model calls depend on an
explicit adapter; self-check uses privileged references and unchanged edits only.

**Output:** Four or seven packets per task; selected summaries, matched-task
passes/regressions and unchanged quota/error/cost contracts. Hybrid self-check
expects 21 reference passes and 21 unchanged failures across three authored tasks,
with six fresh and six stale checks. This is calibration, not held-out/model evidence.
D-021, WI-012. No frontend/API/worker changes.

## F-032 — Explicit live model request and accountable failure

**Trigger:** coding_bench.py:main() run --openrouter; check-provider only validates
local settings and makes zero network calls. Default self-check remains model-free.

**Execution Path:** main() → providers.py:OpenRouterRunner.__init__() reads key
from OPENROUTER_API_KEY, builds settings identity → run_experiment() pins runner
settings → make_request() → OpenRouterRunner.__call__() → fixed-endpoint POST via
urllib opener with _NoRedirect → bounded retained response → usage/model/choice/
finish/edits checks → envelope → response_usage() validates provenance and numbers
before validate_response() classifies status/budget → success apply_edits()/grade(),
or unscored RunnerError → checkpoint attempt incl usage/provider_metadata → report.
HTTP 429 and embedded quota errors produce rate_limited and stop later dispatch.

**Data Transformation:** Request prompt/model/temperature/max_output_tokens →
one non-streaming JSON-mode completion. Provider prompt/completion tokens and cost
map to input_tokens/output_tokens/cost_usd; missing stays null. API generation ID,
returned model/provider and finish reason become typed provenance. Partial/refused/
malformed output and model mismatch never become scored fixes. Credentials and
HTTP error bodies never enter packets/checkpoints. Per-attempt provenance survives
retry, including paid failures whose usage is valid.

**Database Interaction:** None added. Existing disposable lessons and JSON report/
checkpoint storage remain F-031. Source retrieval/MCP behavior unchanged.

**External Interaction:** Explicit live HTTPS POST to OpenRouter only on run;
optional provider-only routing, supported-parameter requirement, no redirects or
automatic retries. HTTP timeout limits socket operations, not strict total time.
Offline tests substitute the opener; no provider/account/model has been exercised.

**Output:** Checked edits envelope or classified unscored error with known usage;
local preflight returns locally_configured, settings and network_calls=0, without
proving API access. D-022, WI-013.


## F-033 — CodeBearing install and project connection

**Trigger:** Installed `codebearing setup --client cursor|claude|codex`, optionally
`--repo` and `--cache`. Without --repo, use the current working directory.

**Execution Path:** pyproject.toml entry point → diffcontext/onboarding.py:main()
→ prepare_config() → diffcontext/connect.py:configuration() → JSON/TOML validation
and merge → asyncio.wait_for(check_connection(), 45 seconds) → existing stdio
launcher/server discovery and search check (F-025/F-026) → save_config() → project
settings file. A later assistant launch follows connect.py:main() →
mcp_server.py:create_server() → existing six RepositoryService tools (F-017).
Advanced `codebearing` arguments delegate to diffcontext/cli.py:main().

**Data Transformation:** Project path and client select `.mcp.json` (Claude),
`.cursor/mcp.json` (Cursor), or `.codex/config.toml` (Codex). Generated configuration
pins the installed Python interpreter and repository root. Merge preserves other
servers/settings; conflicting CodeBearing entries and malformed data fail before
writing. Identical entries preserve original bytes. save_config() checks that bytes
have not changed during the protocol check and atomically replaces the file.

**Database Interaction:** No configuration database. The protocol search reads
repository symbols; optional --cache uses the existing parse cache (F-028).
Existing lesson tables and core retrieval flows remain unchanged.

**External Interaction:** Local filesystem and a child MCP stdio process, no LLM,
provider network, HTTP API, worker or frontend. Installation may download packages.
Assistant trust/approval is a separate host action, not performed by setup.

**Output:** Plain settings path, verified tool count and first-task prompt; status 2
on failure. Failed connection writes no assistant configuration. The six tools
return existing structured context/impact/lesson/investigation results, not edits.
D-023, WI-014. This slice changes public naming, onboarding and guides only.


## F-034 — Windows parser compatibility correction

**Trigger:** JS/TS project setup or any index-backed request (including F-033).
**Execution Path:** onboarding.main → connect.check_connection →
mcp_server.search_symbols → RepositoryService.search_symbols → index.build_index
→ typescript.extend_index → _parse_unit → _call_facts → _File.text.
The execution algorithm is unchanged; optional dependency now selects binding
0.25.2 rather than the version that crashes on the observed real project.
**Data Transformation:** Raw sources → syntax trees → portable symbols/call facts.
Existing cache dependency fingerprints reject facts from the replaced binding.
**Database Interaction:** None by default; optional existing SQLite index cache.
**External Interaction:** Local files/native parser and MCP process; no model call.
**Output:** Normal search results enable verified setup to save Codex project config.
No application source edits. D-024, WI-015; F-027 remains the language flow.


## F-035 — BookMyShow desktop registration workaround

**Trigger:** User reports missing CodeBearing in the desktop MCP list.
**Execution Path:** Existing connect.py:main(--check) → check_connection() →
server discovery/search (F-033/F-034), then external `codex mcp add codebearing`
→ user-level ~/.codex/config.toml → app reload → interpreter -m diffcontext.connect
→ mcp_server.create_server → RepositoryService methods. App reload is unverified.
**Data Transformation:** Reuse the tested absolute Python command and repo args;
server identity codebearing remains bound to BookMyShow. No core transformation change.
**Database Interaction:** None added; default check only reads captured source.
**External Interaction:** Local Codex config/CLI and MCP subprocess, no network,
model, frontend code or worker. Existing desktop UI is the verification target.
**Output:** CLI reports global entry added and enabled. Desktop visibility and an
actual assistant tool call remain pending. D-025, WI-016.
