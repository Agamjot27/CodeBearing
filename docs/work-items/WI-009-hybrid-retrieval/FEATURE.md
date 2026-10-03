# WI-009 — Explainable hybrid task retrieval

Status: completed
Opened: 2026-10-04

## Request and scope

Improve plain-English task localization using lexical ranking, graph relationships
and developer-confirmed memory. Keep evidence packing bounded and explain each
signal. Compare against legacy search under identical tasks and text budgets.
Embeddings, external models and unmeasured quality claims are outside this slice.

## Starting state and execution path

Clean main at 7de87ec. context.py:search() counts token overlap and does not split
camelCase/snake_case. investigation.py:run() chooses best lexical ties and packs
graph BFS order. Lessons attach only after code-first packing. Optional SQLite
parse caching and six MCP tools existed. Hybrid paths were absent at scope time.
Relevant F-003/F-005/F-006/F-018/F-028; proposed D-019/F-029.

## Implementation and decisions

Implemented retrieval.py token splitting, field-weighted BM25, exact-name priority,
confirmed/fresh captured-hash-validated memory, and seed-first bounded graph ranking.
Investigation ranks task candidates and reserves up to 20% for whole eligible
lessons with included scoped code; seed priority can release the reserve.
Compiler validates the ranked pool and keeps diagnostics outside context text.
CLI/MCP search and investigation default to hybrid with a legacy policy switch.
Explicit symbol/ref compilation retains its prior behavior. Coding-harness graph
and memory controls explicitly retain legacy; hybrid treatments are next work.
D-019 explains defaults/alternatives; F-029 traces file/function/database paths.
Version 0.5.0, CI development evaluation and installed-wheel task checks added.

## Attempts and outcomes

Inspected existing task selection, compiler, memory, investigation and test paths.
Three scoped agents contributed ranker/tests, integration/evaluation, and read-only
Windows timeout diagnosis; root integrated and reviewed their changes.
An initial protocol assertion incorrectly expected legacy to miss a TS fixture
whose body contains the query term; corrected it to compare actual legacy search.
Detailed scoring explanations initially inflated context text; retained them in
metadata and restored compact graph citation reasons in packed evidence.
MRR originally included empty ground truth as zero; corrected the definition to
five nonempty tasks, with the two abstention cases checked separately.
One suite stalled at grading timeout and was stopped after identifying only its
owned processes; Windows wrapper descendants can retain inherited pipes and need
a dedicated follow-up. A completed 135-test run had one Git 30-second timeout;
all 16 Git tests then passed. A restricted rerun had five named-pipe permission
errors, and the cache protocol passed with approved pipe access. Final full run
uses that access. First wheel attempt used .venv's missing pip; built successfully
using the available pip interpreter. Installed task checker was corrected to read
the existing seeds.current response shape.
The approved 135-test run then isolated one flaky existing runner assertion:
invalid JSON was classified as timeout because normal Python startup exceeded
0.2 seconds. Give response/error classification five seconds and retain the
0.2-second deadline only for the sleeping timeout fixture; no runtime change.

## Verification

25 new ranker/integration/protocol tests passed in focused runs. Six investigation
development fixtures pass. Seven authored paired hybrid cases pass budget,
eligibility, scoped-code and abstention gates. Saved hybrid-local.json reports MRR
0.20 legacy / 0.90 hybrid over five nonempty tasks with no recall regression.
Both policies fail the broad refund task; hybrid fresh-memory precision is 1/3
because graph neighbors exceed the declared relevance set. No held-out, live-model,
token-savings, production or competitor superiority claim is justified.
Final approved full suite: 135 tests passed in 163.483 seconds, including real MCP
stdio and optional TS/JS parsers. Core smoke and TypeScript budget checks pass.
Clean wheel 0.5.0 with both extras passed outside-checkout hybrid task retrieval,
generated client configs, six-tool MCP discovery/search and persistent cache reuse.
Editable environment metadata refreshed to 0.5.0. No public package publication.

## Handoff / completion

The product remains a context engine/MCP server. Next add explicit hybrid coding
treatments and held-out tasks, harden Windows timeout cleanup, and obtain paired
real-model evidence once a provider is configured. Publishing/naming remains open.

## Git trace

Related test reliability fix: a514b20 (WI-010); runtime behavior unchanged.
Use git log --oneline -- docs/work-items/WI-009-hybrid-retrieval/FEATURE.md.
