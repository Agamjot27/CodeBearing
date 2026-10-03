# WI-002 — Git-diff localization and context

Status: complete
Opened / updated: 2026-10-03 (Asia/Calcutta)

## Request and scope

Automatically identify affected Python symbols from tracked changes between a
selected commit and the working tree. Cover modifications, additions, deletions,
and changes outside functions; connect localization to impact and compilation.
Preserve the old graph for deleted symbols. Keep explicit-symbol commands working.
Untracked files, semantic rename detection, and non-Python analysis are out of scope
and must be disclosed rather than silently treated as covered.

## Starting state and execution path

`cli.py:main()` requires explicit symbols for `context.py:impact()` and
`compile_context()`. `index.py:build_index()` reads current files only. F-002, F-004,
F-005, and F-006 will be updated. Baseline `fa2dd36`; continuity workflow `c213c74`.

## Implementation and decisions

`index.py:build_index_from_sources()` shares the analyzer between disk and Git
blobs (D-008). `changes.py:localize_changes()` reads immutable base blobs and tracked
current sources, maps line changes with `_mapped()`, records fallback/unresolved
changes, and recovers surviving old callers. `changes_impact()` expands both graphs;
`compile_changes()` labels each version and shares the estimated budget (D-009).
`cli.py:main()` accepts `changes --ref` and alternative `--ref` selectors on
impact/compile, reusing current lesson retrieval. F-013–F-015 trace these paths.

## Attempts and outcomes

1. Inspected handover, instructions, indexer, CLI, and Git state. Working tree is
   clean. Historical call edges are necessary because deleted callees disappear
   from the current graph; current-line mapping alone would miss their callers.
2. Extracted `build_index_from_sources()` and retained captured source bytes.
   Disk/snapshot parity, historical encoding, parse-failure retention, excluded
   paths, and existing behavior pass in a 13-test run. No failed attempt occurred.
3. Implemented Git localization and exercised real temporary repositories. The
   first 25-test run had 12 errors, all during cleanup: Windows read-only Git
   objects prevented `shutil.rmtree()`. Assertion bodies passed, but that run was
   correctly treated as failed. Changed fixture cleanup to clear the read-only
   flag only within its verified UUID directory; no project files are involved.
4. Added revision CLI paths, old/current budget packing, renames-as-delete/add,
   import fallback, and current-only memory checks. Recovered old direct callers
   as current seeds so deleted functions do not hide present consumers. Depth
   validation also runs with empty seed sets.
5. Final 29-test run passed. The existing 2-case smoke evaluation passed. Manual
   `changes --ref HEAD` on this repository correctly reported CLI edits and
   untracked new module/test exclusions before staging. Updated all related docs.

## Verification

Passed: `python -m unittest discover -s tests -v` — 29 tests, including 16 revision
checks and 4 source snapshot checks alongside the original 9 regressions.
Passed: `python evals/run.py` — 2 synthetic cases, no missing expected IDs.
Passed: CLI localization on the actual working repository.
Passed: relative Markdown link validation and staged whitespace checks.

Fixtures verify modifications, additions, deleted functions/files, deleted lines
outside functions, old callers, tracked staged/unstaged semantics, excluded
untracked files, staged deletion with leftover disk file, syntax failures,
non-Python gaps, import/constant fallback, paths with spaces, invalid refs/root/depth,
rename disclosure, CLI JSON, shared budgets, and current-only memory.
These checks establish deterministic localization behavior, not end-to-end coding
agent gains. Full benchmark/model execution was not performed.

## Handoff / completion

Feature complete. Remaining limits: non-atomic working capture; static call graph;
whole-file fallback without complete module/class excerpts; untracked exclusion;
syntactic delete/add renames; per-blob Git overhead; heuristic token counts;
current-first packing can omit prior evidence. These are explicitly disclosed.
Next planned work: read-only MCP integration, in a new work-item record.

## Git trace

`git log --oneline -- docs/work-items/WI-002-git-diff-localization/FEATURE.md`.
Source snapshot module: `f09d471` — `refactor(indexer): support captured source snapshots`.
The revision integration commit will be discoverable through the record's Git log.
