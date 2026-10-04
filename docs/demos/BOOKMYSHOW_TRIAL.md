# BookMyShow controlled CodeBearing trial

Observed: 2026-10-04. Work item: WI-017, D-026/F-036.

## What was tested

Two deliberately introduced event-list regressions in isolated copies of the
user's current TypeScript/Express backend: incorrect one-based pagination offset
and public listings disabling the existing upcoming-show filter. Original source,
including uncommitted auth fixes/tests, was preserved. No credentials copied.

Both fresh sessions received the same symptoms and expected behavior. Neither
received the seed edits or the independently authored acceptance checks. The
assisted session was required to use the copy-bound `codebearing_trial` MCP server
before reading files; the control was prohibited from using CodeBearing. Both
could use normal source inspection and add tests. Default chat settings were
retained; exact model/settings parity and token/cost usage were not collected.

## Directly observed results

| Condition | CodeBearing activity | Independent acceptance |
| --- | --- | --- |
| Untouched baseline | None | 5 passed, 0 failed |
| Seeded input before dispatch | None | 0 passed, 5 failed |
| Assisted fresh session | One real MCP investigate before source reads | 5 passed, 0 failed |
| Unassisted fresh session | No MCP calls in retrieved turn trace | 5 passed, 0 failed |

Each solver independently restored the two production lines and added
`backend/tests/events-list.test.ts`. Their added regressions failed before the
fix and passed afterward. Backend source typecheck passed in both session command
traces. The orchestrator reran its separate acceptance checks after both fixes;
source content matched the correct baseline apart from new tests and formatting.
Original BookMyShow backend hashes were unchanged.

Acceptance calls actual controllers through service and repository with a mocked
PostgreSQL query. Cases cover first/second/default pages, type filtering and admin
inclusion; assertions check exact pagination/filter parameters and response metadata.
No live SQL execution, external-service or HTTP integration result is claimed.
Shared node_modules was accessed through a junction with no-edit instructions.

## Tool evidence and useful limitations

Retrieved assisted turn trace shows `codebearing_trial.investigate` completed
before file reads, with task-based localization and max_tokens=9000. Its recorded
tool-call duration was 954 ms for this single invocation; that is not a latency
benchmark. The solver's result file reports localization of event repository and
controller symbols, partial coverage, stop_reason=index_warnings and truncation
of the large returned context in display. These response details are solver-reported;
the thread reader supplies the invocation metadata, not its full response body.
The solver inspected source and tested rather than treating graph coverage as proof.

This is a successful integration demonstration. Both conditions solved the task:
there is no observed correctness advantage on this task. One authored task with
two regressions, unequal solver-written tests and no repeated runs cannot establish
general speed, quality, cost or token savings. Copy separation relies on instructions,
not a security sandbox; independent tasks and repetitions remain future work.

## Evidence and reproduction

Fresh chats are titled `BookMyShow trial with CodeBearing` and
`BookMyShow trial without CodeBearing`.
Their IDs and preparation attempts are recorded in WI-017. Local ignored evidence
is under `.eval-runs/bookmyshow_trial_20261004/`: baseline/candidate/control sources,
acceptance.mjs, original-hashes.json, manifest.json, independent-results.json,
candidate-acceptance.txt, control-acceptance.txt, trace-metadata.json and each
solver's TRIAL_RESULT.md. Full application source is not included in Git.

Set TRIAL_REPO to a copy root, enter its backend directory and run
`node --import tsx --test <absolute-path-to-acceptance.mjs>` with subprocess
permission. The temporary trial MCP registration was removed after completion;
the user's BookMyShow server remains configured. Do not delete dependency junctions
recursively without verifying their targets and Windows filesystem behavior.

Next investigate excessive warning/context output on real TypeScript repositories,
then evaluate a harder independently chosen task. Test memory retrieval separately.
