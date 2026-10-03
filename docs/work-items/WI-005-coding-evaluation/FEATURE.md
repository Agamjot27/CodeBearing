# WI-005 — Controlled coding-task evaluation harness

Status: complete
Opened / updated: 2026-10-04 (Asia/Calcutta)

## Request and scope

Push WI-004, then continue the proposed coding-task evaluation phase. Build small
buggy repositories, executable acceptance checks separated from retrieval inputs,
paired context policies, explicit pre-task synthetic memory, bounded candidate
application, provider-independent runner/replay contracts, metrics and checkpointing.
Verify the harness locally without fabricating model results or spending API quota.

Acceptance: bugs fail, reference fixes pass, prompts omit acceptance/reference
assets, candidate files are restricted to source allowlists, trials have fresh copies,
same model/config and maximum budgets, memory freshness checks, separate quota/provider
errors, reproducible request fingerprints, and resumable checkpoints.

## Starting state and execution path

Read AGENTS/HANDOVER/WI-004 and current evaluation/decision/flow files. Workspace
clean. Pushed `11ec359` on main; verified main...origin/main is 0/0. Existing
`evals/run.py` and `evals/investigate.py` measure retrieval/controller development
fixtures, not executable fixes. Core context/memory/investigation already work.

## Implementation and decisions

Implemented path: evaluation task loader → fresh source copy → existing context/memory
→ prompt packet → runner or replay → validated edits → trusted grader subprocess
→ structured trial/checkpoint → paired report. No provider SDK is required for the
harness; external adapters can connect a selected model later. Local subprocesses
are process isolation, not a security sandbox for hostile code.

## Attempts and outcomes

1. Pushed the completed investigator and verified remote synchronization. Inspected
   scope and current core; no model credentials/provider choice is assumed.
2. Added three buggy source repositories, public tests, external acceptance checks
   and reference JSON. Implemented task loading, fresh copies, atomic restricted
   edits and timed subprocess grading. Four focused tests passed: untouched bugs
   fail, reference fixes pass, out-of-scope edits are rejected, syntax fails, an
   infinite-loop candidate times out, and subsequent trials remain uncontaminated.
3. Committed fixture/grader milestone as `321d140`. Added paired full-prompt budget
   preparation, explicit memory/stale controls, command/replay envelope validation,
   atomic per-trial outputs, provenance/config/adapter checks and resume. Eight
   initial experiment tests passed without external model calls.
4. Added model-free driver self-check and provider/invalid-edit classification test.
   Self-check passed: all 12 reference trials pass, all 12 unchanged trials fail,
   three confirmed lessons retrieved and three stale lessons excluded. The new
   test initially recursively called its patched mock class; captured the original
   method instead. This was a test setup error, not a harness runtime failure.
5. All nine experiment tests pass (11.783s). Full MCP-enabled regression is running;
   earlier retrieval/controller evaluations still pass. Provider credentials or a
   concrete API adapter are not configured; live outcomes are not claimed.
6. Full MCP-enabled suite passed 63/63 (44.024s). Review added UTF-8 command-file
   input, tested with an adapter filename containing spaces, and retained transient
   attempts across resume. A quota-then-success test now verifies prior unknown
   cost keeps the overall reported cost unknown even when later calls report cost.
   All nine affected experiment tests and the complete model-free self-check pass.

## Verification

Passed: `python -m unittest discover -s tests -p test_coding.py -v`, four checks.
Passed: nine experiment checks, model-free self-check, two existing smoke cases and
six investigator fixtures. Checks cover packets without grading assets, stable
fingerprints, budgets, confirmed/stale text, IPC/timeouts, replay, changed provenance,
checkpoint reuse, quota immediate stop/resume, invalid edits and provider exclusion.
Full regression: `$env:DIFFCONTEXT_REQUIRE_MCP='1'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`:
63 passed, including actual MCP subprocess. After final adapter/history review,
`python -m unittest discover -s tests -p test_experiments.py -v` passes nine tests,
and `python evals/coding_bench.py self-check` passes all calibration/control checks.
Existing `evals/run.py` and `evals/investigate.py` pass. Local Windows/Python 3.13.9
verified; configured Linux CI has not been observed remotely. No live provider,
independent task outcomes or dollar/token improvements are claimed.

## Handoff / completion

Fixture/grader and paired packet/runner/report milestones complete with tests,
README/ROADMAP, CODING_EVALS guide, D-014/D-015, F-021–F-024 and HANDOVER synchronized.
Live model outcomes need a configured adapter or independently collected responses.
Next select/configure an adapter, run paired experiments, add independent temporal
tasks and genuine prior corrections. Execution isolation remains ordinary subprocess
permissions; budgets are estimated/declared and usage is runner-reported.

## Git trace

`git log --oneline -- docs/work-items/WI-005-coding-evaluation/FEATURE.md`.
