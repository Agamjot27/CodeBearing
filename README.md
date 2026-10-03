# DiffContext Lab

A local context engine for coding agents, with evidence-backed correction memory.
This is an original implementation inspired by the project direction we discussed;
it is not a clone or an affiliated release of trakshan-mishra/Diffcontext.
The distribution name is `diffcontext-lab`; use a dedicated environment if the
other project's `diffcontext` package is installed.

## What works today

- Parse Python modules into functions, methods, and statically resolved call edges.
- Find seed functions through basic lexical search.
- Follow callers and callees with an explicit depth limit and explain inclusion.
- Compile complete source excerpts, imports, citations, and file hashes under an
  **estimated** token budget. Return omissions and missing seeds explicitly.
- Store repository-local lessons in SQLite. Lessons start as proposed and require
  an explicit developer confirmation before retrieval can include them.
- Flag a lesson as stale if its evidence file or scoped source file changes or
  disappears. Stale, disputed, superseded, and unrelated lessons are not injected.

No API keys or runtime dependencies are needed. Python 3.10+ is required.
The tool parses source; it never imports or executes the target repository.

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
```

Tests cover graph resolution, import aliases, relative imports, shadowed names,
budget omissions, memory confirmation and invalidation, scope filtering, and CLI
behavior. The evaluation is a **two-case synthetic smoke fixture**, not a held-out
benchmark. Its lexical baseline is a simple term-overlap search, not BM25, and the
comparison is not budget matched. No model task-success claim follows from it.
GitHub Actions runs both commands on pushes and pull requests once hosted.

## Current limits

- Python only. Seeds are explicit symbols; Git-diff localization is planned.
- Fresh indexing on every command; no persistent graph cache yet.
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
- Memory evidence currently must be an indexed Python file. Commits, line ranges,
  correction diffs, and test-run artifacts will come later.
- The untrusted-data label is an integration boundary, not a proven prompt-injection
  defense. MCP, model calls, agent orchestration, tracing, and adversarial evals are
  planned, not shipped.

See [the build roadmap](docs/ROADMAP.md) for the progression to the full system.

## Engineering traceability

- [DECISIONS.md](DECISIONS.md): reasons, alternatives, trade-offs, and reconsideration criteria.
- [FLOW.md](FLOW.md): actual execution paths at file and function level.
- [AGENTS.md](AGENTS.md): standing development and commit requirements.

The initial Git commit records the already-written prototype as a baseline.
Subsequent meaningful changes should include their tests and documentation updates.
