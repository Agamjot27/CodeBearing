# WI-017 — Fresh-session BookMyShow controlled trial

Status: completed
Opened: 2026-10-04

## Scope

User authorizes checking BookMyShow, introducing bugs and prompting fresh sessions.
Preserve their uncommitted controller fix/test and other local work. Isolated
backend copies exclude credentials; use synthetic configuration and mocked queries,
no live database, email or Redis changes. Compare an authored two-regression task
with CodeBearing against the same task without it, in fresh sessions.

## Execution / preparation evidence

Current backend snapshot → baseline/candidate/control copies → independent
acceptance.mjs → actual controller → service → repository → mocked pool.query.
Untouched baseline: five passed. Identical faulty copies receive two seeded changes;
candidate independent checks: zero passed, five failed before solver dispatch.
Checks cover one-based offsets, public/upcoming and admin/all flags, type filter
parameters and response metadata, not live PostgreSQL execution.
Full copies and oracle remain ignored under .eval-runs/bookmyshow_trial_20261004.
Solvers may read only their assigned copy, not sibling/original/evaluator files.
This instruction-based separation is not a security sandbox. No secrets copied.

## Attempts

Dependencies are workspace-hoisted: backend/node_modules assumption failed;
corrected to root node_modules junction. Solvers must not edit shared dependencies.
Node runner first required subprocess permissions; an absolute Windows --import
path needed URL handling, so calibrated using --import tsx from the copy backend.
A record update briefly failed on Windows default encoding; explicitly use UTF-8.

## Fresh sessions

Candidate: 01a10727-1eeb-7962-b08b-049f3c00fda6.
Control: 01a10727-30d3-7b23-9cb4-55d91d320ff2.
Temporary codebearing_trial server is bound to candidate only. Candidate must use
real MCP investigate before file reads; control must use no CodeBearing tool/CLI.
Same symptoms, expected behavior and testing constraints. Neither receives seeded
changes or independent acceptance checks. Await actual evidence and outcomes.

## Limits / handoff

Authored integration demonstration, not an independent benchmark or statistical
improvement claim. Prior await trial is user-reported. After sessions finish inspect
tool activity/patches, rerun independent checks, verify original hashes and remove
temporary server. Git trace: git log --oneline -- this record path.

## Observed outcome

Both fresh sessions completed. Assisted trace contains one codebearing_trial
investigate call before source reads (954 ms); control trace contains no MCP calls.
Both solvers added regression tests and restored the two production lines. Session
commands show failing-before/passing-after regressions and successful typecheck.
Orchestrator independent acceptance: five passed/zero failed in EACH condition.
Baseline-equivalent production source restored; only tests added (formatting differs).
Original backend hashes unchanged. Temporary trial MCP entry removed; original
BookMyShow server retained. Direct trace metadata and independent output saved
locally; public concise results are docs/demos/BOOKMYSHOW_TRIAL.md.

Assisted solver reports partial context, index_warnings stop and display truncation;
full MCP response is not supplied by read_thread, so these are reported details.
Both conditions succeeded: no demonstrated correctness advantage. No live SQL,
HTTP integration, token/cost comparison or general speed/quality claim. Default
session settings were retained; exact model equality was not independently verified.
Next test warning/context usability and a harder independent task; memory remains
a separate demonstration. Git trace remains discoverable via this record path.
