# DiffContext Lab

A local context engine for coding agents, with evidence-backed correction memory.
This is an original implementation inspired by the project direction we discussed;
it is not a clone or an affiliated release of trakshan-mishra/Diffcontext.
The distribution name is `diffcontext-lab`; use a dedicated environment if the
other project's `diffcontext` package is installed.

## What works today

The coding harness now has an opt-in seven-condition legacy/hybrid comparison,
fresh/stale memory controls and bounded subprocess cleanup. Run
`python evals/coding_bench.py self-check --condition-set hybrid` for model-free
calibration; [evaluation details](docs/CODING_EVALS.md) explain the limits.

- Parse Python modules into functions, methods, and statically resolved call edges.
- Optionally parse TypeScript/JavaScript functions and methods, with conservative
  relative ESM import and call edges. TSX/JSX syntax is supported; component
  relationships and type-checker resolution are not. See [language support](docs/LANGUAGES.md).
- Find seed functions through code-aware lexical ranking and fresh, confirmed memory.
  Task investigation ranks graph candidates and reserves space for applicable lessons;
  `--retrieval legacy` retains the earlier baseline. See [retrieval](docs/RETRIEVAL.md).
- Automatically localize tracked Git changes against a base commit using old and
  current code, retaining deleted symbols and recovering their surviving callers.
- Follow callers and callees with an explicit depth limit and explain inclusion.
- Compile complete source excerpts, imports, citations, and file hashes under an
  **estimated** token budget. Return omissions and missing seeds explicitly.
- Store repository-local lessons in SQLite. Lessons start as proposed and require
  an explicit developer confirmation before retrieval can include them.
- Flag a lesson as stale if its evidence file or scoped source file changes or
  disappears. Stale, disputed, superseded, and unrelated lessons are not injected.
- Expose six read-only MCP tools through a local stdio server, using the same
  service as the CLI. Agent requests cannot confirm lessons or switch repositories.
- Gather evidence automatically with a bounded task/symbol/revision investigator,
  visible gaps, snapshot IDs, stop reasons and an inspectable trace.
- Optionally persist parse facts and the current graph in local SQLite with
  `--cache`; reuse unchanged files and refresh dependencies after edits/deletions.
  See [incremental indexing](docs/INDEXING.md) for setup, counters and measurements.

The core CLI needs no API keys or runtime dependencies. Python 3.10+ is required.
MCP support uses an optional SDK extra; see [connection instructions](docs/MCP.md).
The tool parses source; it never imports or executes the target repository.

## Use with a coding assistant

The installed `diffcontext-lab-mcp` launcher connects the six tools to Claude
Code, Cursor or Codex. Python 3.10+ is required. This release is not published to
PyPI yet; install from a built wheel or this source checkout:

```powershell
python -m pip install ".[mcp]"
diffcontext-lab-mcp --repo "C:\path\to\your-project" --config claude
diffcontext-lab-mcp --repo "C:\path\to\your-project" --check
```

Use `--config cursor` or `--config codex` for those clients. Merge the output
in the appropriate client settings; generation never edits them automatically.
The configuration pins the installed interpreter and selected repository, so the
assistant launches the server without shell activation. `--check` verifies six
tools and a search request without an LLM; it does not prove coding accuracy.
See [setup](docs/MCP.md) for isolated installation, host locations, first-task
prompts and troubleshooting; [release steps](docs/RELEASING.md) describe packaging
and the remaining publication requirements.

## Try the included example

Run these from the project directory:

```powershell
python -m diffcontext --repo examples/refunds index
python -m diffcontext --repo examples/refunds search "refund_total"
python -m diffcontext --repo examples/refunds impact --symbol billing.py:refund_total
python -m diffcontext --repo examples/refunds compile --symbol billing.py:refund_total --max-tokens 2000
```

The compile result is JSON. Send only its `text` field as repository evidence to
an agent; the rest is diagnostic metadata. The budget applies to `text`, not the
JSON wrapper or the agent's own instructions. Check `missing_seeds`, `omitted`, and
`warnings` before deciding whether the package is sufficient.

Multiple `--symbol` flags are supported. Ambiguous short names fail and list the
exact IDs rather than picking an arbitrary function.

## Investigate automatically

```powershell
python -m diffcontext --repo examples/refunds investigate --task refund_total --summary
python -m diffcontext --repo examples/refunds investigate --symbol billing.py:round_line --max-tokens 2000
```

The investigator locates once, gathers reviewed memory, and expands static
dependencies while checking gaps and limits. It returns `ready`, `partial`,
`needs_input`, or `no_changes` with a trace. Task selection combines lexical and
reviewed-memory signals; it has no semantic model. `ready`
means selected static graph coverage, not semantic correctness. This local workflow
does not edit code or call a model. See [the investigation guide](docs/INVESTIGATION.md)
for Git runs, limits, status handling and saving/inspecting results.

## Analyze your Git changes

From the root of a Git repository containing supported source code:

```powershell
python -m diffcontext --repo . changes --ref HEAD
python -m diffcontext --repo . impact --ref HEAD --depth 2
python -m diffcontext --repo . compile --ref HEAD --max-tokens 4000
```

`--ref` compares the selected commit with the tracked working tree, including both
staged and unstaged changes. Stage new files to include them; untracked files are
listed as excluded. `--symbol` and `--ref` are alternative selectors. `changes`
defaults to HEAD. Run this against the actual Git root, not a subdirectory.

The compiler labels current and historical excerpts separately, and uses one
shared estimated text budget. Deleted functions retain historical evidence and
their surviving callers can be retrieved from current code. Applicable confirmed
lessons are attached only to current evidence. Inspect `changes.unresolved` and
the per-version `missing_seeds`/`omitted` fields. Imports, constants, and other
changes outside functions seed the whole file conservatively and are flagged
because complete module/class evidence is not yet compiled. Renames appear as
deletion plus addition. An unchanged comparison returns no symbol evidence.

## Record and review a correction

```powershell
python -m diffcontext --repo examples/refunds memory add --scope billing.py:refund_total --lesson "Round each line before summing to match invoice totals." --evidence test_billing.py
python -m diffcontext --repo examples/refunds memory list
python -m diffcontext --repo examples/refunds memory status 1 confirmed
python -m diffcontext --repo examples/refunds compile --symbol billing.py:refund_total
```

Use the ID returned by `memory add` instead of `1` if you already have lessons.
The tool records the explanation supplied by the developer; it does not infer
intent from a patch or claim a test passed. Confirmation is a developer attestation,
not automated proof. Add a new reviewed lesson when evidence changes; the old
record can be marked `superseded`. Storage lives in `.diffcontext/memory.sqlite3`.

## Verify

```powershell
python -m unittest discover -s tests -v
python evals/run.py
python evals/investigate.py
python evals/indexing.py
python evals/coding_bench.py self-check
```

Tests cover graph resolution, import aliases, relative imports, shadowed names,
budget omissions, memory confirmation and invalidation, snapshot parity, Git
modifications/additions/deletions, staged and untracked behavior, renames, fallback
warnings, old/current budget sharing, and CLI behavior. Git must be installed to
run revision tests. The evaluation is a **two-case synthetic smoke fixture**, not a held-out
benchmark. Its lexical baseline is a simple term-overlap search, not BM25, and the
comparison is not budget matched. No model task-success claim follows from it.
GitHub Actions runs both commands on pushes and pull requests once hosted.
An additional job installs the MCP extra and requires protocol tests to run.
For a model-free client demonstration, follow [docs/MCP.md](docs/MCP.md).
The new investigation evaluation uses six development fixtures and a seed-only
comparison at the same maximum text budget; it is not a held-out coding benchmark.

The coding harness adds three buggy repositories with executable acceptance checks,
paired lexical/graph/memory/stale conditions, request fingerprints, quota-aware
checkpoints and model-adapter/replay contracts. Its self-check uses reference fixes
and unchanged candidates without a model call. See [coding evaluation guide](docs/CODING_EVALS.md)
before collecting live responses. No model performance claim follows from calibration.

## Current limits

- Python and optional TypeScript/JavaScript syntax graphs. Other-language and
  unsupported configuration changes are reported as unresolved.
- Source bytes are freshly read on every request. Opt-in caching reuses parsing;
  all dependency facts still relink and historical Git blobs still parse afresh.
- Revision analysis indexes historical supported-source blobs as well as captured current
  tracked sources. Large repositories may be slow; working-tree reads are not atomic.
- Top-level functions and direct class methods only. Dynamic dispatch, inheritance,
  re-exports, conditional/local imports, nested functions, decorators' behavior,
  module globals, and configuration may be missed. A missing edge is not proof of
  independence. Class context is not yet reconstructed around method excerpts.
- Call analysis is syntactic, not a type checker. Conventional `self`/`cls` method
  calls are resolved to their current class, without polymorphic dispatch.
- Hidden directories, common dependency/build directories, symlinks, and files over
  1 MB are skipped. `.gitignore` rules are not yet interpreted. Review context
  before sending it to an external model; secret redaction is not implemented.
- Token accounting uses `ceil(UTF-8 bytes / 3)`. Real tokenizer counts may differ.
- Whole-file hashes intentionally over-invalidate lessons. This catches edits but
  does not prove semantic validity or detect changes in other dependencies.
- Memory evidence currently must be a successfully indexed source file. Commits, line ranges,
  correction diffs, and test-run artifacts will come later.
- The untrusted-data label is an integration boundary, not a proven prompt-injection
  defense. MCP transport is tested; real coding-assistant task success has not been
  evaluated. Local bounded orchestration and inline traces work; model planning,
  persistent run history, a web dashboard and adversarial evals remain planned.

See [the build roadmap](docs/ROADMAP.md) for the progression to the full system.

## Engineering traceability

- [DECISIONS.md](DECISIONS.md): reasons, alternatives, trade-offs, and reconsideration criteria.
- [FLOW.md](FLOW.md): actual execution paths at file and function level.
- [AGENTS.md](AGENTS.md): standing development and commit requirements.
- [HANDOVER.md](HANDOVER.md): current state and reading order for every new session.
- [Work-item records](docs/work-items/): per-feature and per-bug attempts, outcomes,
  verification, and handoff. New records use [these templates](docs/templates/).

The initial Git commit records the already-written prototype as a baseline.
Subsequent meaningful changes should include their tests and documentation updates.
