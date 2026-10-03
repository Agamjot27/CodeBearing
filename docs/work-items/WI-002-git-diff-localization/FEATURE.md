# WI-002 — Git-diff localization and context

Status: in progress
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

First make indexing reusable for immutable in-memory sources so historical code
can use the same analyzer without checkout or executing code. Then add Git snapshot
reading, old/new line mapping, and CLI integration. Record D-008 and D-009 as the
choices become concrete; keep old and current evidence visibly distinct.

## Attempts and outcomes

1. Inspected handover, instructions, indexer, CLI, and Git state. Working tree is
   clean. Historical call edges are necessary because deleted callees disappear
   from the current graph; current-line mapping alone would miss their callers.
2. Extracted `build_index_from_sources()` and retained captured source bytes.
   Disk/snapshot parity, historical encoding, parse-failure retention, excluded
   paths, and existing behavior pass in a 13-test run. No failed attempt occurred.

## Verification

Passed: `python -m unittest discover -s tests -v` — 13 tests after source adapter.
Pending: temporary Git fixtures for edits/additions/deletions, changes outside functions,
special paths, invalid revisions, tracked/untracked semantics, and CLI outputs.

## Handoff / completion

Source-based index entry point complete; next implement diff service and CLI selectors.
Update HANDOVER.md and affected FLOW.md entries as each unit is completed.

## Git trace

`git log --oneline -- docs/work-items/WI-002-git-diff-localization/FEATURE.md`.
