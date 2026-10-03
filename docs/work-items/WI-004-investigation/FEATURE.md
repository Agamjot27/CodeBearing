# WI-004 — Bounded context investigation

Status: complete
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
model provider/framework before controlled outcome evidence. D-012 records
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
4. Committed the controller milestone as `4d81d95` after the complete dependency-free
   suite passed (42 checks, four optional SDK skips). Added CLI/MCP entry points,
   schema_version 1, compact summaries and explicitly saved UTF-8 run inspection.
5. Added three more controller/CLI/inspector checks and an MCP contract check;
   extended actual stdio revision coverage to investigation. Twelve focused tests
   and six development fixtures passed. Added fixture evaluation to core CI.
6. Full MCP-enabled suite passed 50/50 in 44.888s. Both earlier smoke cases passed.
   Reviewed summary behavior and retained task matches/source warnings even for
   runs with no compiled context; bounded-file rejection test added. Reran all
   twelve affected controller/CLI/inspector checks successfully (4.957s).

## Verification

Passed: nine controller tests including capture count, unique depths, task ties,
limits, memory mismatch/nonmutation, fixed snapshot, deletion and configuration
gaps. Controller milestone full suite: 46 discovered, 42 passed and four optional
MCP skips (49.948s). Final commands/results:

- `$env:DIFFCONTEXT_REQUIRE_MCP='1'; .\.venv\Scripts\python.exe -m unittest discover -s tests -v`:
  50 passed, actual local subprocess transport included.
- `python -m unittest discover -s tests -p test_investigation.py -v`: 12 passed
  after final summary adjustments; works without SDK.
- `python evals/investigate.py`: six fixture passes; same selected seeds and max
  text budget as seed-only comparison. `python evals/run.py`: both smoke cases pass.
- `python -m diffcontext --repo examples/refunds investigate --task refund_total --summary`:
  ready/graph_covered, five operations, cited expected code and visible trace.

Local Python 3.13.9/Windows verified; remote Linux CI has not been observed. Fixtures
do not demonstrate model accuracy, cost savings, or independent task outcomes.

## Handoff / completion

Local context investigator complete with source/memory/version checks, CLI/MCP,
inspectable runs and controlled fixtures. D-012/D-013, F-017–F-020, README, ROADMAP,
MCP/INVESTIGATION guides and HANDOVER synchronized. Next real Python-repository
trial and held-out coding outcomes; lexical relevance, module/class/config gaps,
cooperative timeout, metadata budget and atomic capture limitations remain explicit.
Broader web frontend, LLM planning/editor and independent benchmarks are planned.

## Git trace

`git log --oneline -- docs/work-items/WI-004-investigation/FEATURE.md`.
