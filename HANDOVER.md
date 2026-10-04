# Current handover

Updated: 2026-10-04 (Asia/Calcutta). Read after AGENTS.md at session start.
This is a current-state record; history is in Git, decisions and work items.

## Product and completed capabilities

CodeBearing is a local context engine/MCP server for coding assistants. It provides
six read-only tools; the assistant edits/tests code. Python and optional JS/TS
syntax indexing, conservative call/import graph, tracked Git changes/deleted source,
hybrid lexical/graph retrieval, budgeted context, confirmed fresh SQLite lessons,
bounded investigation and observable trace are implemented. CLI/service reports
remain full. Install/setup is project-scoped for Claude/Cursor/Codex; legacy aliases
and internal diffcontext imports/storage are retained. Public repository now is
https://github.com/Agamjot27/CodeBearing.git; no PyPI publication yet.

## Active work

WI-020: user requests smaller-model benefit testing. New matched fresh chats
request gpt-6-luna/low (accepted): assisted 01a1074f-36ae-7383-ac0e-b17d72e4efea,
control 01a1074f-471b-7f31-b900-05844604b999. Both new copies calibrated 2/6 before
dispatch; same WI-019 booking task/oracle, D-028/F-038. Temporary codebearing_luna
bound to .eval-runs/bookmyshow_luna_20261004/candidate. Next inspect traces, grade,
compare originals, remove this temporary entry. Per-run billed tokens unavailable;
do not conflate payload byte reduction with cost/quality improvements.

WI-018: 0.7.0 compact MCP presentation implemented, installed and committed 031fac4. detail=compact
(default) samples diagnostics with counts and references equal trace data; full
returns complete fresh evidence. Source/status/critical gaps preserved. Context
and verification appear before verbose search metadata. D-027/F-037.
Frozen BookMyShow structured JSON 292449→40259 bytes; SDK response 649084→101729.
160-test full suite passes, then all six presentation tests pass after a final
order regression. Clean wheel install/setup/stdio/cache checks pass.
Upgrade required stopping only old read-only CodeBearing MCP processes holding
Windows interpreter files open. Existing chats need reconnect/restart for 0.7.0.

WI-019: harder isolated booking durability/rollback paired trial completed.
Read docs/work-items/WI-019-booking-failure-trial/FEATURE.md. Local ignored assets:
.eval-runs/bookmyshow_harder_20261004. Baseline 6/6; seeded copies 2/6, four failures.
Both fresh chats fix all three faults and pass six independent checks; assisted
eight own regressions/control seven pass; source typechecks pass. Assisted actual
investigate observed twice before reads; control has no MCP calls. All 68 original
hashes unchanged; temporary codebearing_trial removed. F-038; public report
docs/demos/BOOKING_FAILURE_TRIAL.md. No correctness advantage demonstrated.
Task-based compact response still clipped due to unbounded search metadata; focused
symbols response useful, partial/token_budget disclosed. No live services/secrets.

## Evidence and next steps

WI-017 paired event-list demo: both conditions fix two seeds and pass five
independent mocked checks/typecheck. Real assisted investigate observed; no
correctness advantage demonstrated. Original BookMyShow unchanged. Results:
docs/demos/BOOKMYSHOW_TRIAL.md; D-026/F-036. Prior missing-await trial is user-reported.
BookMyShow's user-level codebearing entry is bound to that project, even in other
projects. Keep it; temporary trial entries should be removed after experiments.
Native Tree-sitter 0.26.0 crashes on real redis.ts; 0.25.2 pin fixes observed input
(D-024/F-034). Don't upgrade without real-project regression validation.
Next prioritize bounding verbose ranking metadata, independently chosen tasks and memory demonstration;
model/evaluation infrastructure does not justify adding databases/frameworks alone.

## Limits / avoid

No frontend/HTTP API/worker, autonomous edit agent or independent benchmark is
implemented. Static graphs miss dynamic/type/runtime relationships. Global index
warnings can make an otherwise useful investigation partial. Text token estimate
excludes JSON/transport overhead. Full-detail reruns are new snapshots, not persisted
previous reports. Lesson freshness uses whole-file hashes and may over-invalidate.
Authored paired trials and synthetic harness calibration aren't quality/cost claims;
mocked SQL/Redis isn't live integration. Solver isolation relies on instructions.
Do not change original projects, read credentials, edit shared dependency junctions,
or commit .eval-runs/.test-tmp/.diffcontext/generated files. Record actual decisions,
flows, work-item attempts and appropriate verification with meaningful commits.

## Useful checks

.\.venv\Scripts\python.exe -m unittest discover -s tests -v
python scripts/check_wheel.py dist/codebearing-0.7.0-py3-none-any.whl --typescript
git status --short
