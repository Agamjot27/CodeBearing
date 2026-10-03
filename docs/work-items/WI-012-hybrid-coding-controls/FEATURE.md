# WI-012 — Explicit paired hybrid coding conditions

Status: completed
Opened: 2026-10-04

## Scope and starting state

At d364adb the coding harness has four legacy conditions; default service
retrieval changed in WI-009, but harness policies were deliberately pinned.
Add an opt-in seven-condition set with hybrid/no-memory/fresh/stale variants,
same tasks and prompt/output budgets, visible paired outcomes, resumable manifests
and model-free calibration. Keep four-condition defaults for cost and clarity.
These authored repositories remain development fixtures, not held-out tasks.

## Implementation path and reasoning

evals/coding_bench.py:main() → selected condition tuple → experiments.py:
export_requests()/run_experiment() → make_request() → service investigation policy
→ request/checkpoint/report. D-021/F-031 record the actual contract.
Provider/model setup and genuine external held-out tasks remain future work.

## Attempts and verification

Implemented HYBRID_CONDITIONS and validated selected tuples; legacy four remains
default. CLI --condition-set hybrid selects all seven in prepare/run/self-check.
make_request() uses explicit policies and four memory controls; diagnostics retain
seeds, included code and lesson origin. Policy-version-2 manifests pin every
package Python source hash; old manifests reject resume and need a new directory.
Reports add five new scored-only pairs, including regression counts; quota stop,
unscored errors and unknown costs retain their existing meanings.

Four new tests passed: same source/settings/budgets, fresh/stale lesson behavior,
seven-trial resume/config rejection, pair regression/provider-error denominator,
and validation before writes. Final full suite passed 142 tests in 132.914s with
MCP/TS extras and Windows process permissions. Hybrid CLI self-check passed three
calibrated tasks, 21 reference successes, 21 unchanged failures, six fresh-memory
and six stale-memory checks. Zero model calls. CI runs both condition sets.
CLI prepare also wrote 21 reviewable packets to the ignored
.eval-runs/hybrid-packets-preview directory with UNCONFIGURED_MODEL, without
executing a model. Rebuilt local 0.5.0 wheel includes processes.py; this packaging
check is distinct from the earlier clean-install validation in WI-009.
No new efficacy failure encountered in this slice; original broad-query miss and
graph-neighbor precision limitation remain documented in WI-009.
No held-out performance, genuine correction-history benefit, real-model quality,
cost savings or competitor superiority is claimed.

## Handoff / Git trace

Completed. Next collect external held-out tasks and real correction history,
configure a provider/model and run paired trials. New fixtures authored by this
same implementation team must be labeled development cases, not held-out evidence.
Use git log --oneline -- docs/work-items/WI-012-hybrid-coding-controls/FEATURE.md.
