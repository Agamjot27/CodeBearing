# WI-024 — Connected complementary evidence loses the small context budget

Status: resolved for connected complementary seed priority; graph/budget limits remain
Opened: 2026-10-05

## Discovery and reproduction

Read-only replay of WI-020's exact task against its captured unchanged baseline,
with 3000 estimated tokens and eight steps: seeds are booking-total, confirmation,
and parseInput. The last seed adds only the body word `preserve`; transaction's
body adds `rollback`, but its lower marginal rare-term gain loses seed priority.
The final packet is 2962 estimated tokens and explicitly omits withTransaction.
This is development evidence from an authored task, not held-out performance.

## Affected execution path

RepositoryService.investigate → investigation.run → hybrid_search →
select_task_seeds → rank_candidates → compile_context. F-040/F-029/F-018.
The transaction is statically called by the selected confirmation function.
No original app, model, network or database mutation is involved in replay.

## Investigation and attempts

Inspected ranked matched fields, packet inclusion and source/import byte lengths.
Both distracting parseInput and relevant transaction add one body-only term;
arbitrary vocabulary stopwords or minimum term counts would hide legitimate
single-term disconnected evidence. Prefer complementary lexical evidence with
a direct static relationship to an already selected seed before disconnected
coverage. Preserve fallback for disconnected aspects and all selector contracts.

## Root cause and fix

Implemented: optional captured Index in select_task_seeds; direct caller/callee
relationships break the connected-versus-disconnected coverage preference,
followed by existing inverse-frequency term gain and input order. At most three
seeds and exact/top ties remain unchanged. Expose relation reason in selection.
No unrelated zero-gain neighbor is injected. Packing stays whole-source and all
budget omissions stay visible. Root decision/flow entry coordinated by parent.

## Verification

14 retrieval-ranker tests pass in 0.020s; 14 investigation tests pass in 4.010s.
Added checks for connected-versus-disconnected preference, zero-gain neighbor
exclusion, deterministic selection, disconnected fallback, exact-name/ID ties,
and a 300-token packet retaining connected code with an explicitly missing seed.
Existing legacy, explicit-symbol and revision tests pass unchanged.

Exact captured Luna replay now selects total, confirmation and transaction.
All three complete seed excerpts fit at 2884/3000 estimated text tokens; parseInput
is no longer a seed. This remains partial/token_budget with 15 nonseed omissions
(previously seven): making the widely shared transaction helper a seed exposes
additional callers at depth one. No omissions, source truncation, graph warnings
or missing seeds are hidden. No model call, original application edit or token
usage/quality improvement claim was made. No compiler/budget heuristic changed.

## Handoff / resolution

Ready for parent integration and full-suite verification. Static relation is evidence, not semantic certainty;
connected distractors remain possible and insufficient budgets still report gaps.

## Git trace

Prior baseline: 8ad5fea (WI-021). Use git log --oneline -- this record for history.
