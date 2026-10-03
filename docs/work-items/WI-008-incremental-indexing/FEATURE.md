# WI-008 — Persistent incremental indexing

Status: implemented and verified locally
Opened / updated: 2026-10-04

## Request and scope

Persist parsed functions and dependency facts, reuse unchanged files, update edits,
additions and deletions, and verify full-rebuild parity. Measure cold/warm/edit
latency without inventing improvement. Product is a context engine exposed as
an MCP server with six tools; no skill/plugin framework is needed.

## Starting state and execution path

Clean main at 53dd799. index.py scans/parses every request; AST and syntax trees
are transient. service.py and investigation.py call build_index(); changes.py
rebuilds historical/current graphs. SQLite previously stored lessons only.
F-028 now extends F-002/F-013/F-016/F-018/F-019/F-025-F-027; rationale D-018.

## Implementation and decisions

- index.py:capture_sources()/build_index(cache=True) capture fresh bytes and call
  index_store.py:build_cached_sources(). IndexStore.load() validates content,
  parser/runtime/adapter version and payload checksum before providing JSON units.
- Python _python_unit() and TS _parse_unit() produce symbols/imports/exports/call
  facts. Unchanged files skip parsing; all facts relink against current symbols.
- SQLite metadata/files/symbols/edges persist derived state atomically. Changes
  prune removed files. Unchanged generations avoid publishing identical rows.
- --cache opt-in propagates through CLI/service/investigation/MCP/launcher configs
  and connection checks. Optional indexing counters survive report summaries.
- Git filtering precedes current parsing; historical snapshots remain uncached.
  No memory DB writes, new server dependency, pickle, watcher or mtime trust.
- Version 0.4.0, installed cache-reuse check, CI authored indexing eval, setup,
  language/current-limit corrections, saved measured artifact and regressions.

## Attempts and outcomes

Delegated per-file Python/TS facts and tests while root implemented storage and
integration. First Python extraction left a stale qualified-map assignment and
failed with NameError; removed it, reran, and baseline parity check passed for
52 captured Python files/232 symbols/298 edges before later additions.
Initial cache test assertions passed but five cleanup errors on Windows came
from unclosed test SQLite connections; explicit closing fixed them. A full suite
started before that test correction imported the earlier tests and showed those
five errors. Final full rerun passed. New config test initially omitted its fixture
write helper; added it and reran in the final suite. Review corrected cache
connection cleanup ordering so malformed-fact reparsing can still publish repair.
Initial timing protocol was noisy and fixed-order; changed to separate warmup,
alternating paired order and explicit unflushed OS-cache caveat. Older preliminary
numbers are superseded by the saved final-protocol measurement below.

## Verification

- Final full suite with MCP and parser extras: 108 tests PASS.
- Two later CLI/Git cache tests PASS; 110 tests covered total.
- Core-only cache suite: 12 PASS, one optional TS test skipped.
- Parser facts: four Python and three TS unit tests prove zero parsing on warm
  JSON reload and edit/deletion relinking. Existing TS adapter tests still pass.
- Real MCP cache test: cold search, warm compilation and changed source refresh;
  no lesson DB created. CLI test proves persistence across separate processes.
- Corrupt payload/schema/parser/root/database, failed publication and symlink
  refusal paths preserve fresh evidence; engineering-memory bytes stay unchanged.
- Existing Python retrieval two fixtures PASS; investigation six PASS; TS authored
  two-budget retrieval PASS (all expected functions at 246 estimated tokens).
- evals/indexing.py: authored120 Python files/960 functions, three repetitions,
  exact full/cache parity throughout, warm0 parses/120reuse; edit1parse/119reuse.
  Saved indexing-local.json: medians full105.255ms, empty-cache276.860ms,
  warm30.950ms, full-edit99.242ms, cached-edit69.762ms. Full timing includes capture.
  No latency threshold, production scalability, model-success or competitor claim.
- Clean wheel0.4.0 with both extras PASS outsidecheckout: installed indexing,
  compilation, three config formats, real MCP discovery/search and cache reuse
  between installed CLI/MCP processes. No memory DB or host settings writes.

## Handoff / completion

Current implementation and scope verified; no known failing application check.
Cache only parsing incrementally: all source is read, graph relinked, and changed
SQLite generations rewritten. Git historical parsing is uncached. Fresh capture
is not atomic. Empty-cache initialization is slower in the measured fixture.
No actual assistant-host integration, public publication or live coding evaluation.
Next: hybrid retrieval measured under matched budgets, then paired live trials.
See docs/INDEXING.md for usage/counters/limits and HANDOVER.md for continuity.

## Git trace

Use git log --oneline -- docs/work-items/WI-008-incremental-indexing/FEATURE.md.
Implementation, tests and synchronized rationale/flow records are committed together.
