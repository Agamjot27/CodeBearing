# WI-021 — Task localization drops complementary code

Status: resolved for discarded complementary lexical evidence; semantic limits remain
Opened: 2026-10-05

## Discovery and reproduction

WI-020 Luna reported booking-total as its only task seed. Replayed its exact query
against the untouched captured BookMyShow baseline: hybrid score 1.0 for the short
validateBookingTotal helper, .428 for confirm, .231 for withTransaction. A more
specific symptom query still ranks the helper first. These are development repros,
not independently selected benchmark results. No original application edited.

## Affected execution path

RepositoryService.investigate → investigation.run → hybrid_search → _lexical_rows
→ only highest-score ties become seeds → rank_candidates/compile_context expands
that seed's graph. F-029/F-018. The real confirm graph has withTransaction at depth
one, but confirm never becomes a seed. No network/model/database interaction added.

## Investigation and attempts

Inspected per-field matched terms; short name/path matches beat broad behavioral
body matches. Reproduced both queries. A scratch inverse-frequency coverage selector
adds confirm and parseInput; it does not magically understand intent. Confirm's
existing static edge reaches withTransaction. Rather than tune BM25 weights to this
one app or add a provider/embedding model, test bounded complementary seed coverage.
Keep exact-name ties/legacy/explicit/ref behavior intact and expose chosen terms.

## Root cause and planned fix

Single-best selection throws away ranked evidence for distinct task aspects.
Keep the best seed and greedily add up to two candidates covering previously
uncovered query terms, weighting rare terms within the captured candidate pool.
This remains lexical and may select distractors. Full source budgets/omissions
and ambiguity reporting remain the correctness boundary. Planned D-029/F-040.

## Verification / handoff

Pending: tests reproducing disconnected multi-aspect localization, exact/tied
queries, no added redundant seeds, determinism, legacy parity, and real replay.
Do not claim model improvement or retune held-out data from this authored task.

Implemented select_task_seeds and hybrid run integration. First test run caught
two mistaken fixture expectations: highest payment ties must remain tied rather
than collapse to one; a redundant total helper need not be selected when confirm
already covers its terms. Corrected tests to assert actual contracts. Twelve
ranker tests and thirteen investigation tests pass. Real replay selects helper,
confirm and parseInput (new generic term 'preserve'); at 3000 estimated tokens,
confirm source is now included, withTransaction still omitted. Partial/token_budget
remains explicit (2962 estimated text tokens). Full regression suite passes 167
tests in 123.044 seconds; six investigation fixtures pass. Last three additional
presentation tests validated separately by the delegated agent (12/12). No model
calls, new infrastructure or original application changes. Next fixed-runner
independent localization/repair evaluation; don't treat this replay as held-out.
