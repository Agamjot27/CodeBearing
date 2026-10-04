# WI-020 — Smaller-model paired repair trial

Status: complete; one exploratory pair, benchmark claims not established
Opened: 2026-10-04

## Request and scope

User asks to evaluate lower GPT models for users with limited tokens/access.
Hypothesis: context localization helps a smaller model repair code. This is not
yet a demonstrated cost or quality benefit. Use available gpt-6-luna with low
reasoning in both fresh chats, fixed behavioral task, identical seeded copies,
independent six-check oracle, and no original project edits or live services.
Model is explicitly selected in create_thread; settings acceptance and observed
tool activity will be recorded. No direct paid API or credential access.

## Starting state / execution path

Reuse WI-019 calibrated booking durability/rollback task and D-026 isolation.
F-038 remains the actual source/oracle path. Prepare new copies from untouched
captured baseline, not the earlier solvers' repairs or test files. Same three seeds
and independent acceptance. Smaller model settings are the new experimental factor.

## Decisions / verification plan

One paired smoke trial first, rather than claiming a benchmark from many settings.
Keep task, input, reasoning effort and acceptance equal; treatment differs only
in required CodeBearing usage. Fresh chats may read files and write mocked tests.
Context text budget and response bytes are not model billed tokens. Current thread
reader does not expose per-run usage, so do not claim measured token/cost savings.
Record limitations and exact IDs; independently grade both and remove trial entry.

## Attempts and outcomes

Copied 68 whitelisted files per condition from the untouched WI-019 baseline.
No traversal of node_modules junctions. Same three seeds applied; independently
calibrated candidate/control each 2 passed, 4 failed. Prior untouched baseline 6/6.
Registered temporary codebearing_luna bound only to candidate.

create_thread accepted explicit model=gpt-6-luna, thinking=low for both fresh chats:
assisted 01a1074f-36ae-7383-ac0e-b17d72e4efea, control
01a1074f-471b-7f31-b900-05844604b999. Same behavioral prompt and regression/typecheck
requirements; assisted must investigate first, control prohibits CodeBearing.
Settings requested and accepted; no actual token billing telemetry collected.
Final results and tool traces still pending. D-028; F-038 reused.

During execution both encountered Node/esbuild sandbox spawn restrictions. Control
ended with a contradictory report claiming writes failed despite changed files and
a saved TRIAL_RESULT.md. Assisted continued correcting a test double that mocked
the behavior under test. Interim independent oracle: assisted 6/6, control 3/6;
68 original hashes unchanged. This is not a clean treatment comparison because of
incomplete execution and infrastructure confusion. Saved interim results/report.
Sent BOTH chats the same environment-only clarification authorizing scoped
escalated writes/mock test processes, reminding them to complete original scope
and verify saved files. No implementation hints or oracle results were supplied.
Control resumes; assisted receives clarification during its ongoing work.

## Handoff

Next prepare/calibrate new copies, register candidate-bound temporary MCP,
dispatch matched gpt-6-luna/low chats, inspect and grade, preserve original hashes.

## Final verification and outcome

Both chats finish. Independent finalize.py reruns the frozen acceptance against
final saved source: assisted 6/6, control 3/6. All 68 original hashes unchanged.
Removed temporary codebearing_luna. Saved initial/final results, acceptance
outputs and all three control-turn trace metadata in ignored local evidence.
Assisted one actual investigate observed before source reads; control zero MCP.
Assisted four own checks and source typecheck pass; control three own checks and
source/test typechecks pass, but real cleanup and two discard assertions fail
independent grading. Control only handles 08-class discard; exact original error
identity is preserved. Private application files are not committed.

Control continuation interrupted with systemError; resume message supplied only
continuation instructions. Both got identical environment clarification; no
oracle results or repair hints supplied. Assisted initially mocked the behavior
under test and corrected it. Control's eventual pre-fix check temporarily restores
the old wrapper after edits, not the requested successful before-edit sequence.
These limits preclude causal/latency claims. No automatic approval rejection.

Public report docs/demos/LUNA_BOOKING_TRIAL.md, D-028/F-039. Explicit settings
requested/accepted, execution model identity not independently available. No
per-run billed tokens/cost collected. One task and correlated checks do not
establish general improvement. Assisted reported localization of booking-total
rather than the core symbols: prioritize better task localization and fixed-runner
repeated independent trials; reuse existing coding harness rather than inventing
another framework. WI-018 release 031fac4; protocol introducing commit 646d94a.
