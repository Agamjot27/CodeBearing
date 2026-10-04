# WI-020 — Smaller-model paired repair trial

Status: paired fresh chats running
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
Results, regressions and tool traces still pending. D-028; F-038 reused.

## Handoff

Next prepare/calibrate new copies, register candidate-bound temporary MCP,
dispatch matched gpt-6-luna/low chats, inspect and grade, preserve original hashes.
