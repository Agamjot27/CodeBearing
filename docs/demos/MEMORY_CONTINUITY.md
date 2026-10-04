# Engineering memory across requests

Observed 2026-10-05 (Asia/Calcutta), WI-026. This is a runnable persistence and
freshness demonstration using production memory code, not a model-quality study.

The lesson comes from a real recorded agent test gap in
[the Luna booking trial](LUNA_BOOKING_TRIAL.md): the control's cleanup test ran a
synthetic rejected operation after the transaction wrapper instead of calling the
actual confirmation service. Its own three checks passed while independent
checks exposed the remaining service failure. We convert that observed correction
into advice: mock external dependencies, exercise real orchestration, and assert
durable success when post-commit optional cleanup fails.

The small Python booking example is wholly authored for this demonstration. It
does not contain copied BookMyShow code. The JSON transcript records the historical
report's SHA-256 and control chat ID, distinguishing observed provenance from the
authored reproduction. This does not claim the developer previously approved a
lesson, that the agent automatically learned, or that memory improved a later fix.

From a source checkout, use a **new or empty** disposable directory:

```powershell
.\.venv\Scripts\python.exe scripts/demo_memory.py --repo .eval-runs/my-memory-demo
```

That default run fixes the authored example and proposes the lesson, then exits
with **zero eligible lessons**. Proposed advice cannot enter an agent's context.
To exercise all transitions in another empty directory:

```powershell
.\.venv\Scripts\python.exe scripts/demo_memory.py --repo .eval-runs/my-reviewed-memory-demo --review-actor demo-operator
```

The explicit flag invokes operator review in the disposable lesson store. It
records `kind=explicit_operator_demo_review` and `human_approval_claimed=false`.
The review actor is in the demo transcript; the production SQLite lesson schema
does not authenticate reviewers or persist their identities. In a real project,
the developer reviews the proposal and uses `codebearing --repo <project> memory
status <id> confirmed`. The six MCP tools remain read-only and cannot confirm it.

Observed full-demo checks:

| Boundary | Result |
| --- | --- |
| Real entrypoint, buggy authored source | Durable-success assertion fails |
| Real entrypoint, corrected authored source | Assertion passes |
| Proposed lesson, fresh interpreter | No lesson text; proposed exclusion disclosed |
| Operator-confirmed lesson, fresh interpreter | Persisted lesson retrieved |
| Context compilation, fresh interpreter | Lesson text included |
| Scoped file changed later | Lesson excluded as stale |
| Context compilation after source change | Stale lesson text absent |

The later request is a fresh Python process, not a new LLM chat. No models, live
databases, secrets or original application files are used. Each process opens its
own repository service and the existing SQLite store read-only. The only writable
database belongs to the disposable demo directory.

Execution: `scripts/demo_memory.py:run_demo()` →
`check_durable_success()` → `index.py:build_index()` → `memory.py:Memory.add()` →
`fresh_request()` → new interpreter → `service.py:RepositoryService.get_lessons()`
→ `_lessons()` → `Memory(read_only=True).list()`. Explicit review calls
`Memory.set_status()`; `fresh_request(action="compile")` calls
`RepositoryService.compile_context()` → `context.py:compile_context()`. A subsequent
`booking.py` edit changes its hash; `Memory.list()` flags stale and service/context
retrieval exclude its advice. SQLite `lessons` rows retain the original hashes.

Results are saved at `<demo directory>/MEMORY_DEMO_RESULT.json`. The observed run
used `.eval-runs/memory-continuity-20261005` and actor `codex-demo-operator`; that
local generated evidence stays ignored. Three regression tests passed, including
default non-confirmation and refusing to overwrite a nonempty directory.

Whole-file hashing conservatively invalidates even unrelated comments. Capturing
corrections is currently a deliberate proposal/review operation, not an automatic
conversation listener. Trusted human review and later model-behavior benefit
remain separate from this demonstrated storage/retrieval boundary.
