# BookMyShow booking-failure paired trial

Observed 2026-10-04. WI-019; isolation protocol D-026; execution F-038.

Three deliberate regressions were introduced in two files of isolated copies of
the user's TypeScript/Express backend: confirmation leaking a Redis cleanup error
after a durable commit, rollback errors replacing the original payment error, and
failed rollback clients being returned to the pool rather than discarded. No
credentials were copied. The original project's 68 captured files remained unchanged.

Two fresh chats received identical behavioral symptoms and expected contracts,
without seed edits or the independent oracle. The assisted chat used the
candidate-bound CodeBearing 0.7 MCP server before source inspection; the control
used normal file tools and no CodeBearing. Both wrote failing mocked regressions
before production edits. Default chat settings were retained; exact model parity,
token usage and cost were not collected. Isolation relied on instructions.

| Condition | Independent checks | Solver regressions |
| --- | --- | --- |
| Correct baseline | 6 passed, 0 failed | Not applicable |
| Identical seeded copies | 2 passed, 4 failed each | Not applicable |
| Assisted after repair | 6 passed, 0 failed | 4 failures before; 8/8 afterward |
| Control after repair | 6 passed, 0 failed | 3 failures before; 7/7 afterward |

Both source typechecks passed in the retrieved command traces. Independent checks
were rerun by the orchestrator after the fixes. They execute actual
`bookings.service.ts:confirm`, repository functions, `transactions.ts:withTransaction`
and `seat-holds.ts:checkOrRelease` with synthetic SQL/Redis doubles. They verify
durable success despite cleanup failure, original payment error preservation,
single discard on failed rollback, normal success order, healthy rollback reuse,
and exact original error identity. They do not establish live database, Redis,
network or HTTP-server correctness. Solver tests separately invoke the real HTTP
error mapper with a mocked response. Their CJS/MJS files require explicit commands
and are not selected by the existing TypeScript-only npm test glob.

Retrieved tool metadata shows two actual `codebearing_trial.investigate` calls,
before file reads: symptom localization (298 ms) and a focused symbols request
(129 ms). These individual durations are not a latency benchmark. The control
trace contains no MCP calls. The assisted solver reports these run IDs:

- `6a612b0f6e164abeafe15627ff1d7fcd`: partial/token_budget, 3909 estimated context tokens.
- `6d5171a0a7ad4b3585936e8d1bb7dce9`: partial/token_budget, 5959 estimated context tokens.

The thread reader exposes invocation metadata, not complete MCP response bodies;
response details here are solver-reported. Compact diagnostics retained samples
and counts, but the first tool display still clipped at approximately 36400 output
tokens. Whole-response search metadata remains outside the context budget. The
focused call disclosed 192 context warnings (8 shown) and 190 index warnings
(8 shown), missing imports, omitted symbols and an unexpanded frontier. These
limits remained explicit; the assistant inspected source and tested its changes.

Both conditions solved the task. This is a real integration demonstration with
three authored faults, not evidence of better correctness, speed, cost or token
use than an unassisted assistant. A repeated set of independently selected tasks
is still needed for those claims. Response-size reduction measured separately in
WI-018 applies to its frozen report, not every invocation in this trial.

Fresh chats: `BookMyShow booking failures with CodeBearing`
(`01a10741-f7a5-78a0-9000-344930674852`) and
`BookMyShow booking failures without CodeBearing`
(`01a10742-08f6-7021-a460-e6bf90246926`). Temporary `codebearing_trial` was removed;
the user's original `codebearing` entry was preserved. Local private evidence stays
ignored under `.eval-runs/bookmyshow_harder_20261004`: copies, oracle, calibration,
independent-results.json, acceptance outputs, hashes, trace-metadata.json and each
solver's TRIAL_RESULT.md. No original application changes or copied source are committed.
