# WI-026 — Observable engineering-memory continuity

Status: complete
Opened / updated: 2026-10-05

## Request and scope

Demonstrate correction → proposal → explicit review → a fresh request retrieving
the lesson → stale exclusion. Ground the lesson in the observed WI-020 control
failure: a cleanup regression tested a synthetic operation after the transaction
rather than invoking the actual confirmation service. No private source, model
calls, original project edits or automatic developer approval are in scope.

## Starting state and execution path

Existing `Memory.add()` stores proposed lessons; `Memory.set_status()` accepts
explicit status changes after checking evidence freshness. It does not authenticate
or record a review actor. `RepositoryService.get_lessons()` opens SQLite read-only
and excludes proposed or stale text (F-007–F-010/F-016). Therefore this demo must
distinguish an operator's simulation review from an actual human confirmation.

## Implementation and decisions

Implemented `scripts/demo_memory.py:run_demo()`: a wholly authored Python analogy in an empty disposable directory;
default leaves a proposed lesson. An explicit `--review-actor` opts into operator
confirmation in that disposable store and records the actor in a JSON transcript.
Fresh interpreter retrieval establishes persistence beyond an in-process object.
The public WI-020 report is the historical provenance, with its SHA-256 recorded.
The analogy is not copied application code or a new independent model benchmark.

## Attempts and outcomes — update during work

Read the public trial and ignored control TRIAL_RESULT.md. The control explicitly
states its cleanup check did not invoke the confirmation service. The independent
trial report documents three failed checks despite three solver tests passing.
The existing schema cannot attest review identity; no schema claim will be made.
Implemented default proposal-only behavior and opt-in operator review. First
targeted run passed all three tests without troubleshooting. Executed the full
demo with actor `codex-demo-operator` in the ignored
`.eval-runs/memory-continuity-20261005` directory. The observed report digest is
`3fb823abe7881f2c0aad14190e9150d5bdd8b1748b7ecd0ef1ab7172dfb6bc4f`.

## Verification

`.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_memory_demo.py -v`:
3 passed. These verify proposal exclusion, explicit operator review/fresh-process
retrieval, compiled inclusion, stale retrieval/compilation exclusion, and refusal
to replace existing files. Each reviewed run executes five fresh interpreter
requests; default run executes one. No model calls or paid usage.

`.\.venv\Scripts\python.exe scripts/demo_memory.py --repo
.eval-runs/memory-continuity-20261005 --review-actor codex-demo-operator`: completed;
real-entrypoint assertion failed before the authored fix and passed after it,
proposed advice was excluded, persisted reviewed advice was retrieved/included,
and a later source comment made it stale/excluded. Actor explicitly operator,
not attested human. Public explanation: `docs/demos/MEMORY_CONTINUITY.md`.

## Handoff / completion

Parent owns root decisions/flows/handover/release and commits. Demo code, demo
documentation and targeted tests are owned here. No core memory code changes.
Complete with limits: existing schema has no reviewer identity or authenticated
approval, correction capture is manual, whole-file edits over-invalidate, and
fresh-process retrieval does not establish later model behavior improvement.

## Git trace

Find introducing commits with `git log --oneline --
docs/work-items/WI-026-memory-continuity-demo/FEATURE.md`.
