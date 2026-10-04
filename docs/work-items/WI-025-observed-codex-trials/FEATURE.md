# WI-025 — Repeated smaller-model packet trials with observed usage

Status: complete; results do not establish a hybrid quality/cost advantage
Opened / updated: 2026-10-05

## Request and scope

Run broader matched smaller-model comparisons after the exploratory Luna chat.
Use all four authored coding tasks, lexical and hybrid packets, repeated fresh
requests, independently maintained acceptance checks and actual reported token
usage. These remain authored experiments, not independent quality or cost proof.
Never inspect credentials or introduce paid API calls as a fallback.

## Starting state and execution path

`experiments.make_request` already freezes bounded packets; `coding.grade` checks
allowlisted candidate replacements. Existing provider runners require temperature
zero and a provider output cap. Codex CLI can report usage but its local help does
not expose those generation controls. A separate explicit Codex trial protocol is
planned so we do not falsely claim those settings were enforced.

## Implementation and decisions

Official documentation opened:
https://learn.chatgpt.com/docs/non-interactive-mode (redirect from developers.openai.com).
It documents `exec --json`, terminal usage events, `--output-schema`, read-only
sandbox, saved CLI authentication and `--ignore-user-config`.
Local `codex exec --help` confirms these flags, plus `--ephemeral`.
Implemented: temporary empty working directory, explicit requested model/low effort,
no user MCP configuration, reject traces containing external/tool execution,
capture input/cached/output usage, grade afterward in the trusted fixture harness.
Temperature remains CLI default; output allowance is checked after generation,
not advertised as an enforced provider cap. Dollars remain unknown.

## Attempts and outcomes — update during work

Documentation and CLI help inspected. Created a separate protocol because the
CLI has no temperature/provider-output-cap controls. Added optional subprocess
environment to processes.run_bounded so API key overrides can be removed without
printing/inspecting credentials. Codex itself uses existing saved sign-in.

Actual two-call gpt-6-luna refund pilot: both acceptance passes, reported usage,
zero observed tools. Pilot excluded from subsequent matrix. Read-only agent audit
identified unfrozen graders/checkpoint mixing; froze checks.py and package hashes,
validate them before checkpoint reuse. Unknown event types now fail closed.

Actual 32 calls: four authored tasks × two policies × two repetitions × two
requested models, all completed/scored, no operational/budget/tool exclusions.
gpt-6-luna lexical7/8 hybrid5/8; gpt-5.6-luna lexical8/8 hybrid7/8.
Observed token totals and per-trial hashes/results are preserved in
docs/demos/SMALL_MODEL_PACKET_TRIALS.json; explanation in sibling Markdown.
The suite did not demonstrate a hybrid advantage. Two hybrid retry outputs dropped
the omitted local exception declaration; transaction failures also occurred in
both policies. A separate WI-028 fix follows rather than rewriting the matrix.
No test/task changed in response to results.

## Verification

Six focused tests pass: unknown/zero usage, contamination, malformed/duplicate
edits, frozen requests/checkpoints, changed acceptance rejection, post-generation
output exclusion. Full source suite: 183 tests pass in135.779s, before WI-028.
Matrix uses codex-cli0.160.0, low effort, default temperature,3,000 estimated
prompt allowance,4,000 observed-output postcheck. Usage includes scaffolding and
cached/reasoning subsets; USD and provider-attested model IDs remain unknown.
Per-task exact-symbol queries do not exercise WI-024 localization or interactive
MCP; four authored tasks and repetitions are not independent benchmark evidence.

## Handoff / completion

Completed files/functions: diffcontext/codex_trials.py:prepare_trials/run_trials,
CodexPacketRunner,parse_events,engine_hashes/grader_hash; processes.py:run_bounded
optional env; evals/codex_bench.py:main; tests/test_codex_trials.py; public artifacts.
Execution F-043, actual rationale D-034; root handover synchronized. Local ignored
.eval-runs/codex-{luna,56luna}-matrix-20261005 holds requests/events/results.
No original projects, configuration or secrets were changed. Post-result repair
must be labeled separately; this matrix remains the pre-WI-028 snapshot.

## Git trace

Use `git log --oneline -- docs/work-items/WI-025-observed-codex-trials/FEATURE.md`.
