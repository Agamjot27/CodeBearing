# WI-022 — Bounded MCP ranking diagnostics

Status: complete
Opened / updated: 2026-10-05

## Request and scope

Compact MCP investigation output still repeats large ranking explanations. Bound
per-row matched terms and reason text while preserving every ranked identity,
order, numeric score/distance, lesson ID, selected source and coverage gap. Full
detail and service retrieval semantics remain unchanged. No infrastructure added.

## Starting state and execution path

`retrieval.py:hybrid_search()/rank_candidates()` → investigation report →
`mcp_server.py:investigate()` → `presentation.py:present_report()` (F-037).
Existing compaction samples warnings and references equal trace data; it does not
bound ranking diagnostics in search_matches/context.retrieval.candidates.

## Implementation and decisions

Implemented copy-only ranking sampling in presentation.py:present_report():
search_matches, search_symbols top-level matches, context.retrieval.candidates
and distinct trace matches retain
all rows and numeric/identity/lesson fields. reasons retain eight entries of up
to 160 characters; signals.matched_terms retains eight per field of up to 80
characters. presentation.fields records total/shown/omitted item and character
counts plus per-item character limits. Full remains the unchanged service object.
These limits prevent many distinct diagnostics (not just repeated warnings) from
dominating output without touching retrieval semantics or dropping identities.
Only scoped ranking explanations are sampled; source/omission reasons remain.
Parent will synchronize DECISIONS.md/FLOW.md. No database/network/model interaction
in the presentation transformation. This remains no total transport-size cap.

## Attempts and outcomes — update during work

Read current implementation, D-027/F-037 and feature template. No implementation
attempts at the opening milestone. Retrieval rows include reasons strings and
signals.matched_terms. Implemented bounded diagnostic lists and strings, then
tested forty distinct rows and three ranking locations, immutability, score/ID/
lesson preservation, exact omissions and full opt-in. Small rankings remain exact.
Added an actual SDK tool roundtrip test with controlled large ranking diagnostics
and both text and structured channels. First sandbox run passed seven of eight
then-existing tests; stdio errored with Windows pipe PermissionError. Retried with
scoped escalation after adding SDK ranking regression; all nine tests passed.
No automatic approval rejection occurred.

## Verification

`.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -p test_presentation.py -v`
with escalation: nine tests passed in 7.004 seconds, including real stdio warning
flood/full response and in-process SDK ranking flood/full-detail compatibility.
The synthetic distinct-ranking test verifies >3× serialized reduction for that
authored stress input only, not measured model tokens or quality improvement.
Frozen earlier BookMyShow report: old compact JSON 40259 bytes, new 41055 bytes,
full 292449 bytes (json.dumps UTF-8). Three sampling disclosures increase metadata
on that smaller input; selected source and all search IDs match exactly. This
feature bounds worst-case explanations rather than guaranteeing every report
shrinks. Full suite and release packaging remain parent's verification scope.

Parent review caught a missed early-stop contract: investigate context is null
before compilation, while the first implementation assumed a dictionary. Fixed
with explicit dictionary guards preserving null context/status/stop reason. Added
direct and real SDK no_matches tests (needs_input remains a successful tool result),
plus a search_symbols top-level matches sampling test after inspecting its actual
service shape. This was an implementation regression caught before release, not
an existing product bug. Latest scoped escalated command above: all twelve tests
pass in 12.050 seconds, including real stdio and null-context MCP behavior.

## Handoff / completion

Complete within assigned scope. Parent must update HANDOVER.md/DECISIONS.md/FLOW.md
and run combined checks before release. Limits: source, gaps, number of rows and
lesson IDs remain unbounded by presentation; counts themselves incur overhead.
No claims about billed tokens, model quality or general benchmark improvement.

## Git trace

Parent will commit implementation, tests and synchronized docs together.
