# WI-004 — Bounded context investigation

Status: in progress
Opened / updated: 2026-10-03 (Asia/Calcutta)

## Request and scope

User wants the agent workflow completed before trying a real codebase. Implement
the local context investigator: task/symbol/ref → locate → compile → verify
observable gaps → expand or stop. Expose it through CLI/MCP, return an inspectable
run trace, and verify on controlled fixtures without requiring provider quota.
This is evidence gathering, not an autonomous code editor or an LLM planner.

Acceptance: reuse one captured index/localization per run; include current reviewed
memory; check both versions for revisions; bound rounds, depth, estimated context,
and cooperative elapsed time; no repeated identical expansion; explain partial
results and ambiguous/no matches; test CLI and real MCP; preserve core behavior.

## Starting state and execution path

`98c7517` is pushed and the workspace is clean. Five MCP tools call RepositoryService;
compilation is one-shot. `context.py:impact()` already expands bounded call graphs,
and `compile_context()`/`changes.py:compile_changes()` report packing omissions.
No investigation coordinator or application run trace exists. Current flows F-016,
F-017 are affected; proposed new path: service → investigation.run → core functions.

## Implementation and decisions

Use a deterministic controller and existing retrieval, rather than introducing a
model provider/framework before controlled outcome evidence. Planned D-012 records
this choice, snapshot identity, measurable verifier rules, and honest time limits.
Return trace inline to preserve read-only MCP; user can explicitly redirect CLI JSON.

## Attempts and outcomes

1. Read session instructions, handover, roadmap, service/core/memory/transport,
   existing test fixtures and flow/decision records. Confirmed previous commits
   were pushed; update the outdated handover push note in this cycle.
2. Implemented run controller/service entry and nine focused tests. Eight initially
   passed. Deleted-function test wrongly assumed no unresolved changes; the diff
   also removed lines outside the symbol. Diagnostic verification showed the
   existing conservative module-gap warning, not a missing historical graph.
3. Adjusted controller to gather reachable graph evidence before reporting source
   gaps, while keeping token/deadline stops immediate. Corrected the deletion test
   to expect partial/unresolved with both frontiers covered. All nine tests passed.

## Verification

Passed: nine controller tests including capture count, unique depths, task ties,
limits, memory mismatch/nonmutation, fixed snapshot, deletion and configuration
gaps. Controller milestone full suite: 46 discovered, 42 passed and four optional
MCP skips (49.948s). Pending: CLI/MCP integration and fixture evaluation; rerun the
complete MCP-enabled suite after transport changes.

## Handoff / completion

Implement controller first with regression tests/docs in one meaningful commit;
then expose CLI/MCP and controlled fixtures in another. Broader web frontend,
LLM planning and independent coding-outcome benchmarks remain planned.

## Git trace

`git log --oneline -- docs/work-items/WI-004-investigation/FEATURE.md`.
