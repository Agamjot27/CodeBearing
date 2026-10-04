# WI-023 — Fixed transaction rollback coding fixture

Status: complete
Opened / updated: 2026-10-05

## Request and scope

Extend the existing one-response Python coding harness with a wholly authored
transaction task. Exercise preservation of the original error and disposal of a
client whose rollback fails, without private project code, services, API calls or
model-written runners. This is synthetic development data, not held-out evidence.

## Starting state and execution path

`evals/coding_bench.py:main()` → `diffcontext/coding.py:load_suite()` →
`trial_workspace()` → `grade()` → isolated Python unittest runner. Existing
suite has three tasks; `tests/test_coding.py` asserts that fixed count.
Affected existing flows: F-021/F-022/F-023/F-024/F-030/F-031.

## Implementation and decisions

Added fixture sources, external acceptance checks and privileged reference edit
under `evals/coding_tasks/transaction-rollback/`; added fourth manifest row and
behavioral calibration tests. Existing packet/edit/usage contracts are unchanged.
Python synthetic clients avoid Redis, SQL, Node and Windows esbuild scaffolding.

Actual fixture path: `orders.py:submit_order()` →
`transactions.py:run_transaction()` → pool acquire → client begin → operation →
commit on success or rollback on error → release once. Seeded rollback exceptions
mask the original exception, and release always permits reuse. Correct reference
isolates rollback failure, preserves original identity and discards failed clients.
`checks.py:AcceptanceTests` exercises actual copied code through synthetic clients.
No database or network interaction occurs. Release throwing is explicitly outside
this task's contract. `reference.json` is consumed by calibration only and external
checks/reference stay outside the index root.

`tests/test_coding.py` checks baseline failure and both incomplete fixes, then the
complete reference. Fixture count assertions in that file and
`tests/test_experiments.py` now derive counts from the suite instead of fixing them
at three tasks/twelve trials. Root rationale and flow updates are coordinated by
the parent agent in the same cycle.

## Attempts and outcomes — update during work

Initial inspection found existing grader already separates `repo/` from private
checks/reference assets and supports arbitrary task counts. No production changes
are required.

First unprivileged affected-test execution passed the new fixture regression but
the existing timeout test returned `grader_error` instead of `timeout`. Repeating
with child-process execution permission passed all five tests without changing
production code or weakening the timeout assertion.

Baseline has seven total checks: four pass, two error-preservation checks error,
one disposal assertion fails. Fixing only preservation fails three disposal
assertions (no errors). Fixing only disposal retains two error-preservation errors
(no assertion failures). Correct reference passes all seven. No other unsuccessful
implementation attempts occurred.

## Verification

Completed with `.\\.venv\\Scripts\\python.exe`:

- `-m unittest discover -s tests -p test_coding.py -v`: 5/5 pass (4.164 seconds).
- `-m unittest discover -s tests -p test_experiments.py -v`: 9/9 pass (32.097 seconds).
- `evals/coding_bench.py self-check --condition-set legacy --output .eval-runs/wi023-legacy`:
  passed, four tasks, 16/16 reference passes, 16/16 unchanged failures, four
  confirmed-memory checks and four stale-memory checks.
- `evals/coding_bench.py self-check --condition-set hybrid --output .eval-runs/wi023-hybrid`:
  passed, four tasks, 28/28 reference passes, 28/28 unchanged failures, eight
  confirmed-memory checks and eight stale-memory checks.
- `git diff --check`: passed; Windows LF/CRLF advisories only.

All checks are model-free calibration, with zero model/API calls and no measured
model quality, token savings or cost benefit. Legacy/hybrid results and traces
remain ignored local development artifacts.

## Handoff / completion

Parent agent updates HANDOVER.md, FLOW.md and DECISIONS.md in this development
cycle. Implementation is complete; no production modules or private apps were
modified. Remaining limitation: authored fixture correctness cannot establish model
benefits or real database behavior. Next concrete action is parent review,
documentation synchronization and meaningful commit; actual lower-model trials
remain separate work requiring observed usage and repeated tasks.

## Git trace

Parent synchronized current suite counts in CODING_EVALS.md, INDEPENDENT_EVALS.md
and ROADMAP.md. Actual rationale D-031; precise execution F-041 and existing
F-021–F-024. Both affected harness test modules pass after the fixture addition;
earlier 167-test full-suite run predates it. No whole-suite post-fixture claim.

Find introducing commit with `git log --oneline -- docs/work-items/WI-023-transaction-coding-fixture/FEATURE.md`.
