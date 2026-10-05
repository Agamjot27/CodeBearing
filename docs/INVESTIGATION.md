# Run the local context investigator

CodeBearing now has a bounded evidence-gathering workflow. Give it a task, exact
symbols, or a Git ref. It locates seeds, compiles context, checks visible gaps,
expands static callers/callees, and stops with a trace. It does not edit code, run
tests, or call a model. A coding assistant can use the returned evidence through MCP.

## Try it before using your codebase

From the project root:

```powershell
python -m codebearing --repo examples/refunds investigate --task "refund_total" --summary
python -m codebearing --repo examples/refunds investigate --symbol billing.py:round_line --max-tokens 2000
python evals/investigate.py
```

The first command shows selected seeds, cited evidence, gaps, limits and decisions.
The second returns full JSON with `context.text` and the trace. The investigator
captures source once per run. The example gathers the helper, refund implementation,
consumer and tests as needed to close the selected static graph.

Task localization defaults to code-aware lexical ranking plus fresh, confirmed
memory. It splits snake_case/camelCase identifiers and ranks graph candidates with
visible signals. Up to 20% of the text budget is reserved for whole applicable
lessons, subject to seed priority and inclusion of the lesson's scoped code.
Use `--retrieval legacy` for the original baseline. See [retrieval](RETRIEVAL.md).
There is no semantic planner. For a unique nonexact best candidate, hybrid adds
up to two candidates covering new matched task terms. Inspect
`retrieval.seed_selection` for IDs/reasons/new terms. Exact and tied candidates
keep the prior ambiguity behavior; larger ties/no matches request more input.
Inspect `search_matches` and `seeds`;
switch to exact `--symbol` IDs if the task selected the wrong code.

For tracked Git changes from the actual repository root:

```powershell
python -m codebearing --repo . investigate --ref HEAD --max-tokens 4000 --summary
```

Both current and historical graphs are checked. Deleted code stays labeled as
historical; untracked files remain excluded. Module/configuration changes can still
be unresolved. An unchanged tracked comparison reports `no_changes`.

## Understand the result

| Status | Meaning |
| --- | --- |
| `ready` | Selected static graph is covered within packing limits; semantic relevance/correctness is not proven |
| `partial` | Best available context with explicit budget, depth, step, time or source gaps |
| `needs_input` | Task has no matches or more than three tied top candidates; choose explicit seeds |
| `no_changes` | No changed symbol evidence and no reported unresolved/untracked gaps |

Check `stop_reason`, `verification`, and warnings. `context` can be null if the run
stopped before compiling. In a partial run it retains the last completed package.
`context.complete` only describes that particular packing result; the enclosing
run status also checks graph frontier and limits. Prefer run status for investigation.
Successful JSON delivery exits zero even for partial/needs_input; invalid requests
and file/database/Git failures exit two. Automation should inspect the status.

## Limits

- `--max-tokens`: 128–32000, default 4000, estimated final text budget.
- `--max-depth`: 0–5, default 3. Each depth is attempted at most once, starting at 0.
- `--max-steps`: 2–10, default 7. Counts capture, task search, and compilation rounds.
- `--max-seconds`: 0.1–120, default 30. Cooperative checks between operations; an
  in-flight parse/Git/SQLite operation may exceed this duration before it returns.

Trace/JSON/MCP metadata and host instructions are outside the text budget. Expanding
static graphs does not find dynamic dispatch, missing configuration or all runtime
dependencies. A small budget can omit the seed itself; the result makes this visible.
Confirmed lessons are checked against live files and captured code hashes, and
unreviewed/stale text is excluded. No memory or run storage is automatically created.

## Save and inspect a trace

Save the **full report**, without `--summary`, as UTF-8. In PowerShell:

```powershell
python -m codebearing --repo examples/refunds investigate --task refund_total | Set-Content -Encoding utf8 run.json
python -m codebearing inspect run.json
```

The inspector reads a versioned report, lists evidence citations and decisions, and
omits source text. It does not re-index/re-run or require the original repository.
It accepts UTF-8 with/without BOM and rejects invalid/unsupported reports or files
over 10 MB. Saved full reports contain repository source; keep them where intended.
No run registry, frontend or automatic persistence is implemented.

## Use from an MCP host

Use the server setup in [MCP.md](MCP.md), then call `investigate` with exactly one
`task`, `symbols`, or `ref`. The other arguments match CLI limits in snake_case.
This sixth tool returns compact diagnostics by default and remains read-only.
Compiled source, status and critical gaps remain available. Warning samples/counts
and exact repeated-trace references are disclosed in presentation metadata. Add
`detail="full"` for a complete fresh report; CLI reports remain full. See [MCP.md](MCP.md).

## Evaluation scope

`evals/investigate.py` runs six synthetic development fixtures: task localization,
helper expansion, missing input, budget, depth and step termination. Its seed-only
comparison uses the same selected seeds and maximum text budget. It measures
expected evidence inclusion and controller behavior, not LLM correctness, savings,
injection resistance, or held-out task success. Unit/protocol tests additionally
cover memory, snapshot races, deadlines, Git versions and saved-file inspection.
