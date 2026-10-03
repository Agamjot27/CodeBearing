# WI-005 — Controlled coding-task evaluation harness

Status: in progress
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

Planned path: evaluation task loader → fresh source copy → existing context/memory
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

## Verification

Passed: `python -m unittest discover -s tests -p test_coding.py -v`, four checks.
Pending packet leakage, runner/error/checkpoint tests, paired reports and full suite.

## Handoff / completion

First fixture/application/grading milestone; then paired packets/runners/reports.
Live model outcomes need a configured adapter or independently collected responses.

## Git trace

`git log --oneline -- docs/work-items/WI-005-coding-evaluation/FEATURE.md`.
