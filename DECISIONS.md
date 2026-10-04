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

**Scope update:** Superseded by D-018 for cache-enabled parsing/persistence;
the original uncached mode remains available. The baseline rationale below is preserved.

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

**Scope update:** Superseded by D-019 for task-selected candidate order and lesson
reservation. Whole-excerpt/estimated-budget rules and explicit/ref packing remain.

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

## D-007 — Separate living session state from per-item engineering history

**Status:** Accepted on 2026-10-03; user-requested continuity workflow.

**Decision**

Require root HANDOVER.md at every session start. Keep one FEATURE.md or BUG.md
under a stable `docs/work-items/<id>-<slug>/` directory per meaningful work item.
Use templates, preserve actual attempts/results, and require intent comments for
new or changed non-obvious logic.

**Context**

A new AI session needs the current state without rereading a transcript. The user
also requires complete start-to-finish feature/bug traces and code intent, which
the existing decision log and execution-flow document do not fully capture.

**Alternatives Considered**

A transcript dump; putting all session status in AGENTS.md; one ever-growing root
BUG.md/FEATURE.md; relying on commit messages alone.

**Why This Approach**

A short replaceable snapshot makes resuming practical. Dedicated work-item records
retain detailed attempts and verification without making that snapshot unwieldy
or mixing unrelated bugs. AGENTS.md supplies a discoverable reading order and
maintenance requirements. Local comments explain contracts and surprising logic
where they matter, while decisions and flows retain cross-file detail.

**Trade-offs**

Several documents need coordinated updates. Stale summaries can mislead sessions,
so claims must be tied to observed checks and implementation. Documentation does
not automatically enforce compliance. No new runtime component is introduced.

**Future Reconsideration**

If duplication becomes costly, add lightweight checks or an index of work items.
Keep the current-state snapshot concise and preserve stable historical records.

**Implementation:** `AGENTS.md`, `HANDOVER.md`, `docs/templates/`,
`docs/work-items/WI-001-documentation-continuity/FEATURE.md`.

## D-008 — Reuse the analyzer for captured source bytes

**Status:** Accepted on 2026-10-03.

**Decision**

Extract `build_index_from_sources(root, sources, warnings)` and have disk indexing
delegate to it. Retain captured bytes, including parse failures, for localization.

**Context**

Deleted symbols require historical code and call relationships. The indexer could
previously only read the working tree. Reading source and hash separately also
allowed mismatched evidence if a file changed between those reads.

**Alternatives Considered**

Check out the base revision into a temporary directory; duplicate the parser in a
diff module; analyze deleted function names without historical call relationships.

**Why This Approach**

The same parser preserves analyzer behavior across revisions, without changing the
user's checkout, creating executable historical files, or adding dependencies.
Hashes derive from the bytes actually parsed. Disk/snapshot parity and encoding
tests validate the shared entry point. Keeping invalid source allows later diff
mapping to report unresolved changes instead of dropping them.

**Trade-offs**

Source bytes occupy memory alongside excerpts and AST parsing data. Capturing each
file consistently is not an atomic snapshot of the whole working tree. Historical
indexing still shares the analyzer's static-resolution limitations.

**Future Reconsideration**

Measure memory and indexing cost on large repositories; use snapshot caching or
lazy source retrieval when necessary, retaining provenance and parser parity.

**Implementation:** `index.py:build_index()`, `build_index_from_sources()`.
**Flows:** F-002. **Work item:** WI-002.

## D-009 — Compare tracked working-tree files with immutable Git blobs

**Status:** Accepted on 2026-10-03.

**Decision**

Resolve the base ref once to a commit; read historical Python blobs through Git;
use captured tracked current sources and SequenceMatcher line ranges to localize
changes in both indexes. Seed surviving old callers in the current graph. Keep
current/historical context separately labeled under one shared estimated budget.

**Context**

Users need automatic seeds from their changes. Deleted functions vanish from the
current graph, and zero-width deletion coordinates can point at unrelated code.
Imports/constants/class-level edits cannot be represented as a function-body edit.

**Alternatives Considered**

Parse unified Git patches; use GitPython; check out historical code; localize only
current lines; infer semantic renames; ignore out-of-function changes.

**Why This Approach**

Git provides immutable blobs and NUL-delimited path/status output, avoiding quoted
patch path parsing and another runtime dependency. One analyzer handles both
versions. Comparing actual source lines gives old/new ranges without deletion
anchor guesses. Tests demonstrate deleted-caller recovery, staged/unstaged
semantics, paths with spaces, and accurate disclosures. Whole-file symbol fallback
plus unresolved warnings prevents implying imports/constants were fully covered.
The compiler reuses existing packing and current memory eligibility, never applying
current lessons to historical code.

**Trade-offs**

Only tracked changes against the working tree are analyzed; stage new files first.
Renames appear as delete/add. Only the Git root is accepted. Historical indexing
reads every eligible Python blob with separate Git calls and may be costly on large
repositories. SequenceMatcher is syntactic, not a semantic diff. Working-tree reads
are not atomic, so concurrent edits can affect a run. Out-of-function evidence is
flagged but complete module/class excerpts are not yet compiled. Current context
gets budget priority and can crowd out old context; all omissions are reported.

**Future Reconsideration**

Measure startup/memory cost before batch blob reading or snapshot caching. Add
stable working-tree capture, source roots, module/class evidence, or semantic rename
matching when actual use requires them. Evaluate alternate old/current budget
allocation against coding outcomes, not just context size.

**Implementation:** `changes.py:localize_changes()`, `changes_impact()`,
`compile_changes()`; `cli.py:main()`. **Flows:** F-013–F-015. **Work item:** WI-002.

## D-010 — Share repository orchestration and open agent memory read-only

**Status:** Accepted on 2026-10-03.

**Decision**

Use `RepositoryService` for CLI/agent search, localization, impact, compilation,
and confirmed lesson retrieval. Bind it to a directory at construction. Open
existing memory using SQLite URI `mode=ro` and `PRAGMA query_only=ON` for reads.
Developer lesson mutation remains on the existing CLI path.

**Context**

An MCP wrapper around copied CLI logic would create two implementations. Existing
Memory initialization creates directories/schema and commits even on a read, so
it cannot honestly back read-only tools. Agent-facing requests also need explicit
input bounds and cannot choose arbitrary repository roots.

**Alternatives Considered**

Call the CLI as subprocesses; duplicate orchestration in tool handlers; use a
write-capable database connection while relying on convention; expose all lessons.

**Why This Approach**

The service calls existing core functions, keeping algorithms authoritative while
sharing validation/memory selection. SQLite enforces read-only access and absence
of creation. Tests compare core output, reject raw SQL writes, verify unchanged
database bytes, and exclude stale/unconfirmed advice. Missing memory returns empty
results without creating storage. Confirmed lesson text is returned only for the
requested current symbols; rejected entries expose metadata rather than advice.

**Trade-offs**

Fresh indexing still costs each request and expansion repeats before packing.
Request bounds (20 symbols, 50 search matches, 32k estimated context budget) limit
outputs but are not a whole-repository resource sandbox. SQLite reads still depend
on compatible schema and filesystem permissions. CLI compile now shares the 32k
upper bound; direct core compilation retains its original interface.

**Future Reconsideration**

Add snapshot caching, cancellation, and schema migrations when actual workloads
require them. Introduce shared database infrastructure only when concurrency or
multi-user needs warrant it.

**Implementation:** `service.py:RepositoryService`, `memory.py:Memory.__init__()`.
**Flows:** F-005, F-015, F-016. **Work item:** WI-003.

## D-011 — Optional official MCP SDK with local stdio transport

**Status:** Accepted on 2026-10-03.

**Decision**

Expose five read-only service methods using official Python MCP SDK 2.3.0, pinned
in the optional `mcp` extra. Start a single repository-bound stdio server with
`serve`. Keep the core dependency-free and developer memory writes outside MCP.

**Context**

Coding assistants need discoverable tool contracts and structured context without
copying CLI output by hand. Local operation requires no hosted API, authentication
service, or model provider. Protocol behavior must be verified across a real process.

**Alternatives Considered**

Hand-write JSON-RPC/MCP; wrap CLI subprocess output only; use the SDK v1 maintenance
line; introduce HTTP transport; make the SDK mandatory; expose writable memory tools.

**Why This Approach**

Official SDK handles initialization, schema generation, validation, serialization,
and lifecycle. Its current v2 docs and package availability were checked before
selecting 2.3.0. stdio fits local host-launched tools without a new deployment surface.
Optional installation preserves the simpler CLI. Shared service avoids competing
retrieval implementations. Read-only SQLite provides enforcement beyond annotations;
developer review remains explicit. Tests measure schema/discovery, parity, filtering,
error recovery, and separate-process revision compilation. Expected domain failures
become SDK ToolError responses so clients receive the reason and can retry.

**Trade-offs**

The extra adds several transitive packages and only the direct SDK is pinned.
The adapter imports the SDK's ToolError module, so SDK upgrades require contract
tests. stdio suits local processes, not multi-user remote access. Each call rebuilds
indexes; no cancellation policy or atomic snapshot is implemented. Protocol/JSON
overhead is outside the compiler budget. Annotations and untrusted-data instructions
are not an OS sandbox or an evaluated prompt-injection defense. Transport tests do
not establish real coding-agent task success.

**Future Reconsideration**

Upgrade with protocol regression checks. Lock transitive versions if deployment
reproducibility becomes necessary. Add authenticated HTTP only for a demonstrated
remote-host requirement. Measure latency before caching; collect actual assistant
outcomes before expanding the tool surface or adding an investigation loop.

**Implementation:** `mcp_server.py:create_server()`, `_call()`, `cli.py:main()` serve
branch, `examples/mcp_client.py:demonstrate()`. **Flow:** F-017. **Work item:** WI-003.
Sources: [SDK tools](https://py.sdk.modelcontextprotocol.io/servers/tools/),
[running servers](https://py.sdk.modelcontextprotocol.io/run/),
[clients](https://py.sdk.modelcontextprotocol.io/client/).

## D-012 — Deterministic investigation with captured evidence and observable checks

**Status:** Accepted on 2026-10-03.

**Decision**

Add a local evidence-gathering controller using existing search, graph expansion,
packing, and read-only memory. Capture code once per run, start at depth zero, and
increase depth only while a static caller/callee frontier remains. Return an inline
trace and explicit termination reason. No model provider or agent framework yet.

**Context**

The user wants the investigation workflow completed before trying a real codebase.
One-shot compilation requires the caller to choose seeds/depth. Repeated service
calls rebuild indexes and can mix source versions. We need reproducible traversal,
visible gaps, and termination without external quotas or unverifiable self-reflection.

**Alternatives Considered**

An LLM planner/verifier; an agent framework; repeated MCP calls with fresh indexes;
always expanding to depth five; a persisted run database; claiming timeout cancels
in-flight filesystem/Git operations.

**Why This Approach**

Static frontier, seed inclusion, omissions, parsing warnings and unresolved diff
changes are observable. The controller can check them without paying for model
calls or introducing a provider-dependent baseline. One capture avoids mid-loop
source changes; hashes identify actual bytes, including unparseable files. Memory
is read once and rechecked against captured evidence/scope hashes to avoid mixing
versions. Whole excerpts and current/historical packing reuse the existing core.
Steps/depth/budget bounds prevent indefinite expansion. Cooperative monotonic-time
checks honestly stop between operations. Tests measure unique depths, one capture,
both graphs, budget/deadline handling, ambiguous localization and memory consistency.

**Trade-offs**

This is a deterministic context investigator, not an LLM planner or autonomous
editor. Task localization uses the existing lexical score; up to three tied best
seeds are selected, while larger ties request explicit input. Even graph closure
does not prove task relevance or semantic completeness. Static graph components
can grow until a limit stops them. Source capture and lesson reads are not atomic.
Elapsed-time limits cannot cancel an in-flight operation; Git retains its existing
per-call timeout. The budget applies to the final context text, not trace metadata
or cumulative round work. Traces are inline, not a persistent run registry.

**Future Reconsideration**

Measure controlled coding outcomes before adding LLM localization/verifying or a
provider abstraction. Add cancellable workers if strict wall-clock bounds become
required. Reconsider top-score seed selection with labeled localization cases.
Persist traces only when browsing/history requirements justify storage.

**Implementation:** `investigation.py:run()`, `_frontier()`, `_identity()`,
`service.py:RepositoryService.investigate()`. **Flow:** F-018. **Work item:** WI-004.

## D-013 — Versioned inline runs with explicit saved-file inspection

**Status:** Accepted on 2026-10-03.

**Decision**

Return investigation schema_version 1 through CLI/MCP. Provide `--summary` and
`inspect <full-run.json>` as metadata/citation views. Users explicitly save full
UTF-8 JSON; the read-only server does not persist runs. Cap inspector reads at 10 MB.

**Context**

Users need to understand why a run expanded/stopped and inspect a past result
without recreating its repository. A database or frontend is not needed to review
the current local workflow. MCP tool claims must remain read-only.

**Alternatives Considered**

Automatic SQLite run persistence; a dashboard and HTTP API immediately; unversioned
JSON dumps; source-heavy console output only; re-running the original investigation
when inspecting a saved result.

**Why This Approach**

Inline results carry exact evidence and decisions without implicit writes. A schema
version makes unsupported formats explicit. Summary views omit source bodies while
retaining candidate matches, citations, warnings, gaps and trace decisions. Inspector
does no re-indexing and accepts UTF-8 BOM produced by Windows PowerShell. Bounded
reads and clear malformed-file errors are tested alongside the CLI round trip.
Six development fixtures compare expansion to seed-only retrieval at the same
chosen seeds/maximum text budget, avoiding misleading claims from unequal budgets.

**Trade-offs**

Users manage saved files; reports can contain source text. No automatic history,
authentication or frontend exists. Summary output is a view, not a reloadable full
report. The reader validates needed fields, not every historical schema property.
Ten megabytes may reject unusually large metadata-heavy runs. Fixtures are development
examples, not held-out evidence of coding success or model cost improvement.

**Future Reconsideration**

Add migration/full schema validation when public format evolution requires it.
Introduce optional persistence/trace browsing after history requirements and
retention/access boundaries are concrete. Expand evaluations with independent tasks
and executable coding outcomes before making broader performance claims.

**Implementation:** `runs.py:summarize()`, `load_summary()`, `cli.py:main()`,
`mcp_server.py:create_server():investigate()`, `evals/investigate.py:main()`.
**Flows:** F-017–F-020. **Work item:** WI-004.

## D-014 — Separate coding-task inputs from trusted executable grading

**Status:** Accepted on 2026-10-04.

**Decision**

Store three synthetic buggy repository fixtures under `evals/coding_tasks/*/repo`.
Keep acceptance checks and reference fixes outside each retrieval root. Use fresh
UUID workspace copies, allowlisted whole-file edits and timed Python subprocess
grading. Calibrate untouched failures and reference successes before model trials.

**Context**

Retrieval recall alone cannot establish correct fixes. A harness needs executable
task outcomes without exposing future fixes or acceptance tests to context selection.
Candidates must not edit tests through the harness or contaminate the next trial.

**Alternatives Considered**

Score with an LLM judge; place all evaluation assets inside indexed repositories;
run candidate imports in the harness process; grade changes in the working checkout;
introduce Docker/VM infrastructure before a runnable local grading baseline.

**Why This Approach**

Executable public/acceptance tests directly check refund rounding, pagination and
retry exhaustion. Separate assets make accidental retrieval leakage testable.
Fresh copies prevent sequential contamination. Batch validation rejects edits
outside declared source paths before any write. Python -I/-B subprocesses isolate
imports and enforce a per-grader timeout with no new dependencies. Reference fixes
only calibrate grading, never count as model successes. Tests verify failure/pass
transitions, excluded assets, rejected edits, syntax failures, timeout and fresh copies.

**Trade-offs**

Fixtures and lessons are synthetic development material, not independent benchmarks.
Whole-file responses differ from full interactive coding agents. Process isolation
is not OS security isolation: executed candidate code retains the caller's filesystem
and network permissions. This harness is for trusted local experiments; hostile
candidates need an actual sandbox. Output capture is not an adversarial resource
limiter. Allowlisted edit application does not restrict what executed code can do.

**Future Reconsideration**

Add containers/VMs before hostile or untrusted task execution. Expand independent
tasks and held-out splits after baseline calibration. Introduce patch-format support
only if whole-file responses materially distort measured coding outcomes.

**Implementation:** `coding.py:load_suite()`, `trial_workspace()`, `apply_edits()`,
`grade()`, `calibrate()`. **Flow:** F-021. **Work item:** WI-005.

## D-015 — Provider-independent paired experiments with resumable trial artifacts

**Scope update:** D-021 extends the four original controls with opt-in hybrid
conditions and replaces manifest policy version 1 with version 2. Original control
meanings remain; old manifests require a new output directory.
Usage-before-status handling is superseded by D-022 so unusable paid responses
retain validated accounting instead of silently becoming unknown cost.

**Status:** Accepted on 2026-10-04.

**Decision**

Prepare versioned prompt packets for lexical/graph/confirmed-memory/stale-memory
conditions. Support explicit JSON-stdin/stdout command adapters and recorded-response
replay. Keep reference runners calibration-only. Save configuration/provenance,
request fingerprints, per-trial atomic checkpoints and matched-pair reports locally.

**Context**

The project needs to measure executable fixes, latency, context and correction
memory without tying evaluation to one provider or exhausting free quotas during
development. Interrupted experiments must preserve completed work and avoid treating
provider failures as incorrect coding solutions. No provider/model is configured now.

**Alternatives Considered**

Embed one provider SDK now; use only manual copy/paste and spreadsheets; run every
case from scratch on resume; automatically retry quota errors; conflate transport
errors with failed fixes; report missing token/cost data as zero; auto-score with
an LLM judge instead of executable checks.

**Why This Approach**

The command contract can connect a selected model later without new core dependencies.
Replay validates collected response/model/packet identity and grades offline. Shared
task instructions, requested model/temperature/output limit and full-prompt estimated
input budget keep declared settings comparable. Memory is explicitly synthetic
pre-task fixture data; stale control changes an evidence comment after confirmation.
Atomic checkpoints and manifest/adapter/packet checks permit useful resume while
rejecting changed experiments. Quota stops dispatch; unscored failures retry only
on an explicit rerun. Reports compare matched scored tasks and retain missing usage
as null across retained transient attempt history. Command-file input avoids nested
JSON/native shell quoting. Tests measure leakage, budget, memory filtering, replay, resumption, error
classification, provenance, invalid edits and command IPC/timeouts.

**Trade-offs**

Adapters must actually honor settings and report usage; identity is declared, not
provider-attested. Estimated budgets are not exact token caps and actual usage differs.
Whole-file single-response trials differ from interactive coding agents. Three
synthetic tasks and authored lessons do not prove real memory benefits or held-out
performance. Fixed rotated ordering is not randomization. Crashes between billing
and checkpoint saving can repeat a call. Replay files may gain missing responses
at the same path; scored checkpoints stay reused. Output contains fixture source.
Ordinary subprocess execution has no security sandbox. No live model run was performed.

**Future Reconsideration**

Add a specific provider adapter after selecting a model and configuring access.
Add exact tokenizer/cost adapters, repeated trials, stronger execution isolation and
independent temporal task splits before publishing efficacy metrics. Introduce
concurrency only after latency/cost measurements and reliable quota handling.

**Implementation:** `experiments.py:make_request()`, `CommandRunner`, `ReplayRunner`,
`validate_response()`, `export_requests()`, `run_experiment()`, `summarize_results()`;
`evals/coding_bench.py:main()`, `CalibrationRunner`. **Flows:** F-022–F-024. **Work item:** WI-005.

## D-016 — Ship a local MCP launcher with configuration and wheel checks

Public naming and manual-only onboarding superseded by D-023. The read-only
`--config` command and core launcher design remain supported.

**Decision**

Keep the fixed-repository stdio service. Add `diffcontext-lab-mcp` to launch it,
print client configuration, and check discovery plus search in a child process.
Add a distinct core CLI alias and validate an installed wheel in a fresh
environment. Prepare release instructions without claiming PyPI publication.

**Context**

The user wants the fastest way to use DiffContext in existing coding assistants.
Development-path instructions are cumbersome; a dashboard or remote service is
not needed to call the existing tools. No publisher identity is configured.
Another project already owns the diffcontext distribution name.

**Alternatives Considered**

Desktop installer/dashboard; hosted HTTP MCP with accounts/repository uploads;
manual interpreter paths only; automatic client-settings writes; per-call arbitrary
repository paths; a new installation framework.

**Why This Approach**

Setuptools entry points solve executable discovery with no new runtime library.
Generated configuration pins sys.executable and absolute repository paths, avoiding
GUI PATH/activation assumptions. Printing preserves existing settings and enables
review. The SDK client validates actual protocol responses without model cost.
Preserve the interpreter's lexical absolute path: dereferencing a POSIX virtualenv
symlink loses its environment. Codex TOML emits Unicode scalars rather than JSON
surrogate escapes. Review caught both issues; regressions cover them.
Fixed roots preserve the current boundary; multiple projects use separate entries.
A clean wheel check proves users can run outside the source checkout and catches
missing modules/entry points. Measurable benefit: simpler setup with installed
discovery, parsing of generated configuration and a successful search request.

**Trade-offs**

Users still need Python, installation and configuration. Distinct distribution and
command names do not prevent module collision with the other diffcontext package;
use a dedicated environment. Transitive optional dependencies are not locked.
Checks do not prove real assistant integration or coding accuracy. Publishing
requires owner access and package-name verification outside this work.

**Future Reconsideration**

Add guided host configuration/installers if user onboarding remains a barrier.
Add multi-repository support with explicit access boundaries. Consider remote MCP
when private-code access is defined. Publish after release review and owner setup.

**Implementation:** `connect.py:configuration()`, `check_connection()`, `main()`;
`scripts/check_wheel.py:verify()`. **Flows:** F-025/F-026. **Work item:** WI-006.

## D-017 — Extend the shared snapshot graph with optional web-language parsers

**Decision**

Add a syntax-only Tree-sitter TypeScript/JavaScript adapter behind the optional
`typescript` extra. Preserve Python's standard-library parser and shared Index,
context, Git, memory and MCP contracts. Pin bindings 0.26.0, TypeScript grammar
0.23.2 and JavaScript grammar 0.25.0 to the combination verified here. This extends
the language scope of D-008/D-009 without replacing their captured-source design.

**Context**

The user needs useful infrastructure for coding assistants beyond Python and
measurable engineering evidence. Existing downstream services already consume
language-neutral symbols, edges and source hashes. The immediate gap is parsing,
not a need for another database or an agent framework.

**Alternatives Considered**

Regex extraction; a Node/TypeScript compiler or language server; replacing Python
AST with Tree-sitter; mandatory parser dependencies for all users; indexing whole
files without callable relationships; adding a graph database at this stage.

**Why This Approach**

Syntax trees provide reliable callable ranges and binding structure that regex
does not. The Python binding parses captured bytes directly without executing
target code or requiring Node, a project build or language-server lifecycle.
Keeping the adapter optional retains the dependency-free Python CLI. Reusing Index
avoids separate retrieval paths and immediately makes Git deletion recovery and
lesson freshness available to web projects. Conservative ambiguous/shadowed/
reassigned binding refusal prioritizes avoiding invented dependencies. Tests check
exact edges, UTF-8 excerpts, missing dependencies, malformed files, Git recovery,
memory and MCP; the authored retrieval fixture checks whole excerpts and budget.
No measured latency improvement or model success improvement is claimed.

**Trade-offs**

This is a syntax graph, not type checking: JSX references, runtime dispatch,
CommonJS, re-exports and aliases remain unresolved. Conservative scope guards lose
some valid edges. Optional native wheels increase installation/platform risk;
transitive dependencies are not locked. Source indexing still rebuilds each time;
the graph stays in memory, with SQLite used only for lessons. Actual gaps produce
index warnings; universal limitations stay in compiler metadata so they do not
automatically force every investigation to partial.

**Future Reconsideration**

Measure real repository misses before adding compiler resolution or more adapters.
Add persistent incremental indexing next, then compare lexical/graph/hybrid
retrieval under matched budgets. Adopt graph storage only when measured traversal
or persistence needs justify it. Revisit dependency pins after compatibility checks.

**Implementation:** `index.py:is_source_path()`, `build_index_from_sources()`,
`_build_python_index()`; `typescript.py:extend_index()`, `_definitions()`,
`_imports()`, `_resolve_module()`, `_shadowed()`; `changes.py` shared eligibility.
**Flows:** F-027, extending F-001/F-013/F-016/F-018/F-026. **Work item:** WI-007.

## D-018 — Persist JSON parse facts and relink the current graph in local SQLite

**Decision**

Add opt-in `--cache` indexing in `.diffcontext/index.sqlite3`. Persist per-file
JSON syntax facts keyed by SHA-256 bytes and parser/runtime/adapter fingerprints,
plus current symbols/edges. Reuse unchanged extraction, then relink all current
facts; publish changed generations atomically. Keep engineering memory separate.
Extend D-017's transient graph with derived persistence, retaining uncached mode.

**Context**

Repeated MCP requests currently reread and parse the repository. The user needs
practical repeated use and an honest performance comparison. Current call edges
depend on other files' exports, so simply retaining an unchanged caller's resolved
edges would miss changed or deleted targets.

**Alternatives Considered**

Cache only the complete graph; trust mtimes; serialize AST/tree objects with pickle;
keep only a process-local cache; a file watcher; targeted graph invalidation;
Neo4j or another database service; caching by default on every read-only request.

**Why This Approach**

JSON facts survive process restarts and avoid executable object deserialization.
They retain symbols, imports/exports and unresolved call references, letting the
current global symbol map resolve edges correctly without reparsing unchanged
files. Fresh byte hashes detect same-size/same-mtime edits and keep evidence
freshness honest. SQLite is standard-library infrastructure with transactional
publication and no deployment server. Separate derived tables can be discarded
without erasing human-confirmed lessons. Explicit opt-in preserves source-only
retrieval's existing no-state behavior; generated configurations retain the choice.
Measurable benefit is fewer parser calls and lower repeated-request latency,
checked against exact full-build output parity on edits/additions/deletions and
failure paths. Per-language fingerprints are computed once per store operation
to avoid repeatedly loading package metadata for every file.

**Trade-offs**

All source files are still read and hashed; all edges relinked. A changed generation
rewrites derived tables, so this is incremental parsing, not incremental graph
traversal or selective SQL updates. Empty-cache initialization adds overhead.
Historical Git snapshots remain uncached; working-tree capture is not atomic.
Parser facts/source excerpts consume disk. Checksums detect accidental corruption,
not adversarial local tampering. Corrupt/locked/unwritable cache storage falls back
to fresh results with warnings; a corrupt database is not silently destroyed.
No hosted graph DB or production-scale advantage has been established.

**Future Reconsideration**

Measure real repositories before adopting watchers, selective graph updates,
content-addressed historical caches or dedicated graph storage. Strengthen cache
fact validation and publication coordination for stronger multi-process demands.
Consider automatic caching only after the local-state contract is acceptable to
users. Use retrieval and live coding evaluations to establish product benefit.

**Implementation:** `index.py:capture_sources()`, `_python_unit()`,
`typescript.py:_parse_unit()`, `index_store.py:IndexStore.load()/publish()`,
`build_cached_sources()`; `service.py:_index()/_changes()` and launcher `--cache`.
**Flows:** F-028, extending F-002/F-013/F-016/F-018/F-019/F-025-F-027. **Work item:** WI-008.

## D-019 — Blend lexical, graph and reviewed-memory signals without embeddings

**Decision**

Default task search/investigation to dependency-free weighted per-field BM25,
code-identifier splitting, bounded graph candidate ranking and capped fresh-memory
signals. Keep `legacy` selectable and existing coding-harness treatments pinned
to it. Reserve up to 20% of task context for eligible advice, preserving seed code
and requiring included scoped code. Explicit/ref compilation remains unchanged.

**Context**

Original term overlap misses plain-English words inside camelCase/snake_case;
graph BFS orders candidates by distance/ID rather than task evidence. Confirmed
corrections can identify opaque code but code-first packing can exhaust their
space. The user wants improved retrieval and measurable benefit, not more services.

**Alternatives Considered**

Keep overlap/BFS only; identifier splitting alone; hosted/local embeddings and a
vector database; model-driven seed selection; graph-popularity boosts; always
include memory first; replace existing evaluation treatments implicitly.

**Why This Approach**

BM25 adds document frequency, length normalization and term-frequency saturation
without a dependency, model cost or new database. Per-field name/path/body weights
make intent inspectable; exact names preserve ambiguity rather than hiding it.
Memory can point at a reviewed scope only after captured hash/status validation;
its score is bounded, and repeated lessons use the strongest signal. Relinking
and bounded graph expansion already exist, so candidate ordering reuses them.
Seeds lead and graph candidates cannot escape the selected bounded pool. A small
reserve gives reviewed advice a chance while whole excerpts/budget checks retain
observable trade-offs. Ranking diagnostics stay outside the model evidence text
to avoid consuming source budget on verbose token-match explanations.
Actual benefit is checked with identifier, freshness, scope, packing, API and
matched-budget authored cases. No weight tuning or live coding improvement was
performed. Legacy selection preserves comparison and avoids relabeling old trials.

**Trade-offs**

This combines lexical/graph/memory signals; it does not supply semantic embeddings
or language understanding. Suffix heuristics and source comments can mislead
ranking. Broad queries can choose distractors, and graph neighbors can reduce
precision. We score the in-memory corpus again for each round; memory evidence
reading adds latency. The reserve can omit code to retain advice. Initial weights
and fraction are heuristics, not calibrated optima. Authored development cases
are not representative held-out coding tasks. Exact tokenizer accounting and
stronger injection defenses remain absent.

**Future Reconsideration**

Run held-out paired coding trials with explicit hybrid conditions, same model and
budgets. Measure task success, misses, advice utility, latency and cost. Add
embeddings only for demonstrated vocabulary/semantic misses; evaluate incremental
search statistics and candidate caps for large corpora. Revisit weights/reserve
on development data while keeping a separate held-out suite.

**Implementation:** `retrieval.py:lexical_search()`, `eligible_lessons()`,
`hybrid_search()`, `rank_candidates()`; `investigation.py:run()`, compiler options
in `context.py:compile_context()`, CLI/MCP policy selection. **Flow:** F-029. **Work item:** WI-009.

## D-020 — Bound harness waits using file-backed I/O and owned-tree cleanup

**Decision**

Share processes.py:run_bounded() between grading and command adapters. Replace
captured pipes with temporary files, bound wait and cleanup calls, and terminate
the launched PID tree on Windows / isolated process group on POSIX on timeout.

**Context**

WI-009 exposed a Windows grading stall: a descendant retained a captured pipe
after the venv wrapper exited. subprocess.run timeout recovery can wait for EOF
without a second deadline. A bounded harness must return without that pipe wait.

**Alternatives Considered**

Longer timeouts; kill only the wrapper; switch to a different interpreter; platform
job objects; container isolation; file I/O without descendant cleanup.

**Why This Approach**

Files remove the EOF dependency and allow byte-bounded retained output. Shared
code covers both existing callers without dependencies or changing adapter JSON.
Kill the owned tree before the Windows wrapper exits; a POSIX session supplies
a process group. Ordinary stdout/errors and real descendant termination are
verified locally; cleanup failures remain infrastructure errors. Interpreter
switching could lose the installed dependencies and would not fix other adapters.

**Trade-offs**

Temporary disk output is not quota-limited. Cleanup can add bounded seconds after
the execution deadline. taskkill needs Windows process permissions; processes
escaping their original tree/group are outside this guarantee. This is trusted
fixture reliability, not hostile-candidate containment. Successful commands that
deliberately detach background workers are not managed by this helper.

**Future Reconsideration**

Use OS job objects/resource limits or containers for untrusted execution, disk
quota requirements or detached-worker lifecycle control. Validate hosted Windows
and Linux checks; local Windows checks alone do not prove POSIX behavior.

**Implementation:** processes.py:run_bounded()/_stop_tree()/_tail(),
coding.py:grade(), experiments.py:CommandRunner.__call__(). **Flow:** F-030. **Work item:** WI-011.

## D-021 — Opt into paired hybrid conditions and pin execution source

**Decision**

Keep the default four legacy conditions; --condition-set hybrid adds hybrid,
hybrid_memory and hybrid_stale_memory, giving seven conditions. Record selected
conditions and all package Python source hashes in policy-version-2 manifests.

**Context**

Hybrid retrieval is implemented, but earlier coding controls intentionally retain
legacy behavior. Comparing results requires named treatments with the same source,
task/model/instruction/output budgets and matching memory freshness controls.
Resuming after implementation changes must not mix historical and new outcomes.

**Alternatives Considered**

Silently change the old graph/memory defaults; run seven conditions unconditionally;
create a second harness; resume using only task/packet hashes; claim the existing
authored tasks are held-out because the retrieval implementation changed.

**Why This Approach**

Reuse the quota/replay/checkpoint/grading paths with an explicit selected tuple.
Opt-in controls added call volume while keeping names interpretable. Compare
graph/hybrid, memory/hybrid_memory and stale counterparts, plus advice controls
within hybrid. Input budgets cap the complete prompt uniformly; actual tokens may
differ. Record policy, seeds and included symbols in diagnostics. Whole-package
hashes invalidate resume when retrieval, index, memory or grader code changes,
even when an individual fixture's packet happens to match. Model-free references
and unchanged edits calibrate every condition without API costs.

**Trade-offs**

The seven-condition set costs 75% more provider calls per task than the four-control
set before retries. Source hashes conservatively reject resume after unrelated
package changes too. Old manifests cannot resume under policy version 2. Rotating
condition order is deterministic, not a randomized repeated-sample experiment.
Three authored tasks and synthetic lessons do not establish generalization,
real correction-memory benefit or coding-agent improvement.

**Future Reconsideration**

Add independently collected held-out tasks, observed prior corrections, provider
adapters and repeated paired samples before quality/cost claims. Replace whole
package hashes with explicit dependency fingerprints only if conservative resume
rejection becomes an operational problem. Interactive agent/tool evaluation is
a separate future scope from one-response edits.

**Implementation:** experiments.py:_conditions()/make_request()/_config()/_trials(),
export_requests()/run_experiment()/summarize_results(), coding_bench.py:main().
**Flow:** F-031. **Work item:** WI-012.

## D-022 — Explicit OpenRouter adapter with usage preserved before status checks

**Decision**

Add an opt-in fixed-endpoint standard-library HTTP adapter, environment-only key,
strict requested/returned model equality, JSON edits, parameter-support routing
and optional provider pinning. Preserve validated usage/provenance on unusable
responses before classifying them as unscored errors. No automatic retries.

**Context**

The next evaluation slice needs a real provider boundary without requiring users
to write their own adapter. OpenRouter was among providers discussed; no model
choice is available yet. Previous validation discarded usage before reporting an
invalid response, which could hide the bill for a paid failure.

**Alternatives Considered**

Provider SDKs; implement several native APIs immediately; generic arbitrary URL
support; automatic fallback/retry; accept model aliases silently; leave command
adapters as the only live path; estimate cost from remembered price tables.

**Why This Approach**

One explicit HTTP boundary is easy to test with fake transports and requires no
runtime dependency. Official API, routing and usage documents establish field
contracts. Keep the prompt/settings unchanged across conditions; require supported
parameters, request no model fallback list and allow explicit provider-only routing.
Strict model equality prevents accidental comparisons under a different label.
Use provider-reported tokens/cost, never invented pricing; absent usage remains
unknown. Quota stop/resume already exists. Settings and per-attempt model/provider/
generation metadata are reviewable without exposing the key or HTTP error bodies.
Local preflight verifies configuration without network calls or claiming account
availability. User selection is still required before live evaluation.

**Trade-offs**

Only OpenRouter is implemented here. JSON mode/support restrictions exclude some
models; canonical aliases and :free variants may return a different model string
and are rejected until explicitly addressed. Provider routing may vary unless
pinned, and pinning a base slug can still cover multiple regional endpoints.
Usage is provider-reported, not independently audited. HTTP timeouts are socket
operation limits, not a strict total wall-clock deadline; no retry repairs a
malformed response. Public benchmark execution remains outside this adapter.

**Future Reconsideration**

Add native APIs when a selected provider requires them. Add explicit canonical
model mapping only with a documented equivalence contract, not fuzzy matching.
Evaluate strict total deadlines/isolated execution before long production trials.
Use independent tasks and repeated paired samples before outcome or cost claims.

**Implementation:** providers.py:OpenRouterRunner/_NoRedirect,
experiments.py:response_usage()/validate_response()/run_experiment(),
coding_bench.py:main(). **Flow:** F-032. **Work item:** WI-013.


## D-023 — CodeBearing identity and verified project-scoped setup

**Decision**

Ship version 0.6.0 as CodeBearing, distribution `codebearing`, commands
`codebearing` and `codebearing-mcp`, and assistant server key `codebearing`.
Keep internal `diffcontext` imports, `.diffcontext` data and legacy command aliases.
Recommend an isolated uv tool installation and add a project-only setup command.

**Context**

The user chose CodeBearing and asked to simplify using the existing engine.
Manual configuration and development commands obscured the actual product.

**Alternatives Considered**

Rename every internal module and storage directory; retain manual copy/paste only;
add a GUI; overwrite global assistant settings; add a TOML writer dependency.

**Why This Approach**

Public names establish the chosen identity without an unrelated storage migration.
An isolated tool keeps dependencies separate and produces a stable executable.
Setup merges only the chosen project's settings, checks the installed MCP server
before writing, refuses conflicting entries and concurrent changes, and publishes
atomically. Existing servers/settings survive and identical setup is repeatable.
Codex TOML uses Python 3.11's standard parser and appends a validated table to
preserve comments. Claude/Cursor JSON includes the explicit stdio transport.
Official assistant documentation establishes the project paths. Preservation tests
and a clean-wheel protocol/setup test provide measurable checks without model cost.

**Trade-offs**

Automatic Codex setup requires Python 3.11; manual configuration supports 3.10.
Internal names and the GitHub URL retain DiffContext. No PyPI publication or name
ownership has been established: installation currently uses Git or a built wheel.
The installed environment must remain available. Hosts still require project trust
and tool approval. A protocol check does not prove a host used the tools or fixed
code successfully. JSON formatting is normalized when adding a new entry.

**Future Reconsideration**

Publish to PyPI once publisher credentials and package ownership are established.
Change internal names only when their benefit justifies compatibility migration.
Add onboarding UI only if observed user trials show the two commands insufficient.
Measure an actual assistant task before claiming better coding outcomes.

**Implementation:** onboarding.py:main()/prepare_config()/save_config(),
connect.py:configuration()/check_connection(), pyproject.toml.
**Flow:** F-033. **Work item:** WI-014.


## D-024 — Pin Tree-sitter 0.25.2 after a real-project native crash

**Decision**

Replace the 0.26.0 parser binding pin with 0.25.2 in patch release 0.6.1.
The TypeScript/JavaScript grammar pins and indexing semantics remain unchanged.

**Context**

BookMyShow setup discovers tools but its search request loses the server. Direct
faulthandler indexing reproduces a Windows access violation in _File.text(), from
_call_facts() on config/redis.ts. The same Python 3.13 interpreter and project
index successfully with binding 0.25.2, returning 316 symbols.

**Alternatives Considered**

Skip the offending source; remove member-call analysis; change Python immediately;
retain the Tree explicitly; pin the previous compatible binding.

**Why This Approach**

Changing only the binding version fixes the observed project without silently
omitting relevant code or weakening dependency analysis. Explicit Tree retention
was tested and did not prevent the crash, so that attempted code change was
reverted. Validate the established language regressions and actual project setup.
Existing cache fingerprints include dependency versions, invalidating old facts.

**Trade-offs**

Uses an earlier binding release. The precise native-library defect is not proven;
the observed version comparison establishes a workaround, not an upstream diagnosis.
The user's original uv trampoline error was not reproduced on retry and must not
be conflated with the verified indexing crash.

**Future Reconsideration**

Test later releases against this project and language regressions before upgrading.
Reduce a redis.ts-style reproducer without copying private project code if filing
an upstream report becomes necessary. Improve grouped connection diagnostics in a
separate change.

**Implementation:** pyproject.toml optional typescript dependency.
**Flow:** F-034. **Work item:** WI-015.
