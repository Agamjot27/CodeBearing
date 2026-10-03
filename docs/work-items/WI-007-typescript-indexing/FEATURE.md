# WI-007 — TypeScript and JavaScript context indexing

Status: implemented and verified locally
Opened: 2026-10-04

## Request and scope

Start the measurable infrastructure roadmap with language support beyond Python.
Add optional TypeScript/TSX and JavaScript/JSX syntax-tree extraction, conservative
ESM calls, shared snapshots, Git localization, memory and MCP context reuse.
Incremental caching, hybrid retrieval, graph database and live model evaluation
remain future slices. Branding is unchanged pending a selected name.

## Starting state and execution path

Clean main at 8bfe195. Python-only captured-source parsing; .py Git filters;
shared Index feeds context, memory and investigation. .venv held the 0.2.0 wheel.
Relevant earlier rationale D-008/D-009/D-016; new decision D-017; execution F-027
extends F-002/F-013-F-018/F-026.

## Implementation and decisions

- index.py:is_source_path()/build_index_from_sources() dispatch captured bytes to
  the unchanged Python AST logic and optional typescript.py:extend_index().
- Tree-sitter bindings 0.26.0, TS grammar 0.23.2 and JS grammar 0.25.0 are pinned
  in the extra. No Node runtime or target-code execution. Core stays stdlib-only.
- Extract named functions, assigned arrows/expressions and class methods. Resolve
  conservative direct local/relative ESM/this calls; refuse ambiguous, shadowed
  and reassigned bindings. Failed parsing retains bytes, no symbols/hash.
- Git historical/current selection shares eligibility. Existing service, lesson
  freshness and MCP contracts work without a new storage or service layer.
- Missing parser and actual gaps warn explicitly; universal limitations appear
  in compiler metadata. JSX syntax is not component-relationship resolution.
- Version 0.3.0, clean-wheel TS compilation, Linux/Windows CI extras/checks,
  language/setup/release guides, tests and authored retrieval fixture added.

## Attempts and outcomes

Consulted official parser/grammar documentation; inspected existing shared contracts.
Restoring editable mode with --no-build-isolation failed because the target venv
lacked setuptools.build_meta. Normal isolated editable installation succeeded.
Tests found missing anonymous-default export disclosure and named-expression private
name false import edges; adapter fixes and focused reruns passed. Review also added
module-reassignment/type-export guards. Initial TS MCP test could not create Windows
pipes in the default sandbox; approved elevated execution passed. No model API call.

## Verification

- Full optional MCP/parser-enabled suite: 85 tests PASS.
- Subsequently added TS subprocess MCP test: 1 test PASS (86 covered total).
- Missing-parser boundary: 2 core tests PASS without optional parsers.
- Existing retrieval fixtures: 2 PASS; investigation development fixtures: 6 PASS.
- TS authored fixture: 128-token budget includes seed only (106 estimated tokens);
  2,000-token budget includes all three expected functions (246 estimated tokens).
  Both keep whole excerpts and respect the estimated budget. This is not a
  held-out benchmark, exact tokenizer count, coding-success or superiority metric.
- Wheel 0.3.0 built; clean environment install with both extras PASS: installed
  TypeScript indexing/compilation, client configuration and real MCP discovery/search
  outside the checkout, with no memory database creation.

## Handoff / completion

Supports web-language context through the same six MCP tools. Unsupported runtime,
framework, type-checker, package/alias, CommonJS and re-export relationships remain
visible limitations (docs/LANGUAGES.md). No public publication/real assistant host
integration/graph DB/live coding trials claimed. Next: persistent incremental indexing
with full-rebuild parity and latency measurements, then hybrid retrieval/live evals.

## Git trace

Use git log --oneline -- docs/work-items/WI-007-typescript-indexing/FEATURE.md.
Implementation, tests, rationale and flow are committed together.
