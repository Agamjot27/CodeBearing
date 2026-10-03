# WI-011 — Timeout cleanup can wait forever on descendant pipes

Status: completed
Opened: 2026-10-04

## Discovery / scope

WI-009 verification stalled at a grading timeout. Inspection found the Python
virtual-environment wrapper had exited while a grader descendant remained.
Both coding.grade() and experiments.CommandRunner.__call__() use subprocess.run()
with captured pipes; Windows timeout recovery kills the immediate process then
communicates without a deadline. A descendant holding the pipe can prevent EOF.
This is a diagnosed mechanism; no production incident or hostile-code containment
claim is made. Fix both callers through one owned-process helper, then verify
ordinary output, timeout, descendant cleanup and output-size classification.

## Plan / actual rationale

Use temporary-file input/output instead of inherited capture pipes, bounded wait,
and process-tree cleanup for the launched PID on Windows / new process group on
POSIX. No new dependency. D-020 and F-030 will describe the actual choices.
Do not change public outcomes or model packet contracts.

## Attempts / verification

Baseline inspected at 3738e3a. Implemented processes.py:run_bounded(), _stop_tree()
and _tail(); both callers preserve timeout/error classifications and the runner
rejects output truncation before JSON parsing. stdout retention is byte bounded;
grader keeps a 64 KB tail and runner 250 KB, stderr 4 KB. Temporary disk output
has no quota. Restored universal-newline normalization after a Windows assertion
failed. Initial test setup omitted the shared write() helper; corrected it.
Restricted process-tree tests reported cleanup errors (not clean timeouts);
approved process/grading tests pass. Process tests prove a child actually started
then cannot write its delayed marker after timeout, rather than relying on a
timeout that might occur before startup. Final approved checks: three process,
four grading and nine experiment tests pass (16 total). Windows only; POSIX
behavior is implemented but not locally executed. No model calls.

## Handoff / Git trace

Completed fix. Next: hybrid coding-harness conditions. Retained limits are in
D-020; detached workers on successful exit and disk quotas remain outside scope.
Use git log --oneline -- docs/work-items/WI-011-bounded-subprocesses/BUG.md.
