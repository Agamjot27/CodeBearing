# WI-019 — Harder booking durability and rollback trial

Status: completed; both conditions pass independent acceptance
Opened: 2026-10-04

## Scope

User authorizes harder fresh sessions and subagents. Reuse D-026 isolation and
paired protocol; no original BookMyShow changes, secrets or live services. Three
seeded regressions span bookings.service.ts and transactions.ts: post-commit Redis
cleanup failure leaks to caller, rollback failure masks payment error, and failed
rollback client is returned to the pool rather than discarded.

## Preparation / flow

Subagent copies 68 whitelisted backend files to local ignored
.eval-runs/bookmyshow_harder_20261004 baseline/candidate/control. Actual confirm,
repository, transaction and hold functions execute under mocked pool/query and
redis.evalShared. Six independent lifecycle assertions stay outside solver copies.
Baseline passes 6/6; identical candidate/control seeded copies each pass 2/6 and
fail 4/6. Original source hashes unchanged. Shared dependency junction is not to
be edited. Avoid existing full/auth/concurrency tests that can contact services.

## Solver protocol

After installing compact CodeBearing, bind a temporary trial-only MCP server to
candidate and create two fresh chats. Give symptoms/contracts only; no oracle,
baseline source or seeded changes. Candidate uses actual investigate first;
control uses no CodeBearing. Require mocked regression tests and source typecheck.
Inspect trace and rerun independent oracle; verify originals and remove trial entry.

## Limits / handoff

Authored, instruction-isolated integration trial, not a held-out benchmark. Mocked
services do not prove PostgreSQL/Redis integration correctness. Record exact fresh
session IDs and outcomes after dispatch. Full application copies remain ignored.

## Dispatch

Installed CodeBearing 0.7.0 transport verified on candidate. Temporary server
codebearing_trial bound to candidate only. Fresh assisted chat
01a10741-f7a5-78a0-9000-344930674852 and control
01a10742-08f6-7021-a460-e6bf90246926 receive behavioral symptoms/contracts, no oracle
or seed edits. Default settings retained; candidate required actual MCP investigate
before reads, control prohibited from all CodeBearing paths. Await independent
post-fix grading and original-hash verification; remove temporary entry afterward.

## Results and actual attempts

Both fresh sessions completed. Assisted trace shows two actual investigate calls
before source reads (task then explicit withTransaction/confirm symbols); control
trace has no MCP calls. Assisted adds eight mocked regressions, four failing before
edits and all passing afterward; control adds seven, three failing before and all
passing afterward. Both source typechecks exit zero. Trial tests use explicit
commands rather than the existing TypeScript-only npm test glob.

Assisted initially reports a namespace metadata lookup unavailable, followed by
successful actual investigations. Control encountered sandbox write/spawn limits,
resolved by scoped approved escalation, and an unsupported PowerShell -NoNewline
write option, corrected with File.WriteAllText. These are actual attempts, not
product failures or automatic approval rejections. No live services were run.

Orchestrator independently reruns acceptance twice after fixes: both 6/6, zero
failures. Finalize script saves outputs and compares SHA-256 for all 68 original
captured files: none changed. Temporary codebearing_trial removed successfully.
Trace metadata and independent-results.json saved in ignored local evidence.
Report: docs/demos/BOOKING_FAILURE_TRIAL.md; exact runtime flow F-038.

## Remaining limits / next work

Both conditions succeed, so no correctness advantage demonstrated. Compact response
still clipped on the assisted task-based call because search metadata is outside
the text budget. The focused call gave useful source and disclosed partial coverage.
Future presentation work should bound repetitive ranking metadata while preserving
citations, total counts and all critical gaps. Independently selected repeated tasks
and an engineering-memory demonstration remain planned, not completed.
