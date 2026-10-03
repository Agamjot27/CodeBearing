# WI-010 — Runner classification test depends on startup speed

Status: fixed during WI-009 verification
Opened: 2026-10-04

## Discovery and reproduction

The approved 135-test WI-009 run failed
tests/test_experiments.py:ExperimentTests.test_command_runner_json_errors_and_timeout:
runner_timeout was returned where invalid_response was expected. The same test
passed earlier runs. A 0.2-second deadline covered interpreter startup even for
the quick invalid-JSON and nonzero-exit fixtures.

## Attempts and resolution

Do not change runtime classification or enlarge the actual timeout fixture.
Allow five seconds for invalid JSON/nonzero exit and retain 0.2 seconds for the
sleeping candidate. Added an intent comment. This separates response semantics
from startup timing while still exercising the real subprocess boundary.

## Execution path and verification

test_command_runner_json_errors_and_timeout() → experiments.py:CommandRunner.__call__()
→ subprocess.run() → RunnerError outcome → classification assertions.
No database or network. Runtime execution flow and architecture are unchanged.
Final full-suite verification is recorded in WI-009 and HANDOVER.md.

## Remaining limits

This does not fix Windows wrapper descendants retaining pipes after timeout.
That separate harness issue remains a follow-up before live provider trials.

## Git trace

Use git log --oneline -- docs/work-items/WI-010-runner-timeout-fixture/BUG.md.
