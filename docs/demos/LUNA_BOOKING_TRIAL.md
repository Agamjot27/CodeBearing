# Smaller-model booking repair trial

Observed 2026-10-04. WI-020, D-028/F-039; source/oracle execution follows F-038.

User hypothesis: focused repository evidence may help people using smaller models
with limited context or access. Two fresh chats explicitly requested `gpt-6-luna`
and `low` reasoning, accepted by thread creation. Available Luna is the efficient
tier in [official model-selection guidance](https://developers.openai.com/api/docs/guides/model-selection).
The thread reader does not independently expose execution model identity or
per-run billed tokens. No paid API adapter or new credentials were used.

Both conditions started from new copies of the untouched WI-019 captured baseline,
with the same three seeded regressions and same behavioral prompt. They did not
receive seed edits or the independent six-check oracle. The assisted chat was
required to call candidate-bound `codebearing_luna.investigate`; the control was
prohibited from CodeBearing. Ordinary file tools and mocked regressions were
allowed in both. The original 68 captured application files remained unchanged.

| Condition | Independent checks | Solver-written checks |
| --- | --- | --- |
| Prior correct baseline | 6 passed, 0 failed | Not applicable |
| New seeded inputs | 2 passed, 4 failed each | Not applicable |
| Luna with CodeBearing, final | 6 passed, 0 failed | 4 passed; source typecheck passed |
| Luna without CodeBearing, final | 3 passed, 3 failed | 3 passed; source/test typechecks passed |

The independent result differs from each solver's own test result. The control
preserved the original transaction error, but left `bookings.service.ts:confirm`
awaiting fallible cleanup after commit. It only discarded a failed-rollback client
when the error code began with PostgreSQL's `08` class. The frozen oracle uses a
synthetic rollback disconnect without such a code; two client-discard assertions
fail. Its original-error identity assertion does pass, even though the compound
test's title describes that check. Together these produce three failed checks,
representing two remaining behavioral defects. Its cleanup test performs a
synthetic rejected operation after the wrapper rather than exercising actual
confirmation. It therefore misses the real service failure.

The assisted copy catches only post-commit cleanup failure, preserves original
transaction errors, and discards on any failed rollback. Independent tests execute
actual confirmation, transaction, repository and seat-hold functions with mocked
SQL/Redis, checking the original frozen contracts. No live integration is claimed.

## What complicates the comparison

Both chats encountered sandbox process-spawn restrictions. The control initially
stopped claiming writes were denied, despite saved source/test/report files. Its
initial snapshot already scored 3/6; assisted scored 6/6 while still finishing
tests. The orchestrator sent both the same environment-only clarification that
scoped escalation was authorized, with no implementation hints or oracle results.
The control resumed, then hit a systemError interruption and received a resume
message. Assisted completed one turn; control required three turns. These are
material workflow differences; wall time is not a clean speed comparison.

The assisted solver initially mocked the behavior under test and corrected that
harness. Its report says three original-code regressions failed and four final
checks passed. The control ultimately validated its transaction regression by
temporarily restoring the old wrapper after its fix; that is not the requested
successful pre-edit runtime sequence. Original report and intermediate results
are preserved locally rather than erased. No automatic approval rejection occurred.

Retrieved trace proves one actual assisted investigate before source reads, with
max_tokens=3000 and max_steps=8, completed in 506 ms. This single duration is not a
latency benchmark. The solver reports run `49216847fc9d487fa51f5cf21ef76cbd`,
partial/index_warnings. It selected `booking-total.ts:validateBookingTotal`, not
the primary confirmation/transaction symbols. Thus the investigation was incomplete
for the task; successful repair is not proof that localization was good. The
thread reader exposes invocation metadata, not full response bodies. No control
MCP calls appear in any retrieved turn.

## Interpretation and next experiment

This one authored task shows a practical final-result difference under requested
matched smaller-model settings. It does not establish that CodeBearing caused
the difference, a general success rate, or token/cost savings. Six correlated
checks on one task are not six independent benchmark tasks. There are no repeated
samples, reliable usage telemetry or independent held-out tasks in this result.

Next use the existing coding harness's prepared packets/fixed grading boundary,
with independently selected tasks, repeated model/policy pairs and observed
input/output usage. For interactive MCP trials, standardize the Windows runner
and whole-response budgets first. Improve symptom localization and ranking
metadata before claiming that smaller models need less context to succeed.

Fresh chats: `Luna booking repair with CodeBearing`
(`01a1074f-36ae-7383-ac0e-b17d72e4efea`) and
`Luna booking repair without CodeBearing`
(`01a1074f-471b-7f31-b900-05844604b999`). Temporary `codebearing_luna` was removed;
the original `codebearing` entry remains. Private assets stay ignored in
`.eval-runs/bookmyshow_luna_20261004`: copies/oracle, seed manifest, initial/final
independent results and reports, acceptance output, hashes and trace metadata.
