# Current handover

Updated 2026-10-06 (Asia/Calcutta). Read AGENTS first; history is in work items/Git.

## Active work

WI-031 namespace migration complete: source renamed to codebearing/, imports/launch configs
and active guides updated. Source version 0.10.0; existing global 0.9.0 tool and
BookMyShow configuration untouched. D-038/F-047; docs/NAMING.md. .diffcontext data
paths preserved to avoid losing lessons/cache. Open checkout root stays registered
as DiffContext; close/rename/reopen instructions provided.
WI-032 alternatives comparison complete: researched Aider, Serena, CodeGraphContext, Cursor
and Claude Code primary docs; docs/ALTERNATIVES.md has sourced trade-offs,
interview answer and proposed fair benchmark protocol. D-039. No competing-tool or new model trial performed.
WI-033 CI stale-wheel fix: scoped; synchronize checker filename to new release.

## Verification

188 renamed-source tests passed in 74.560s; clean 0.10.0 wheel with optional
JS/TS passed CLI/config/setup/six-tool stdio/cache checks. Only new namespace
shipped. Current guide links and original README example checked. Prior evidence:
188 tests passed; 32 smaller-model trials retained unchanged. Original results
favor lexical packets; no general superiority established. WI-030 README redesign
pushed as b216c0e and rendered/linked/example checked.

## Product and limits

Six read-only local MCP tools, Python and optional JS/TS indexing, conservative
static graph, diff/deleted evidence, budgeted excerpts, confirmed/hash-fresh SQLite
lessons and bounded traces. Assistants edit/test. No hosted UI/API or PyPI release.
Memory review is manual; graph misses dynamic/type/runtime/global wiring. Text
estimate excludes JSON/host scaffolding. Source hashes over-invalidate lessons.

## Avoid

Do not rewrite historical trial artifacts/fingerprints, edit original projects,
read credentials or alter shared dependencies. Do not commit .eval-runs/.test-tmp/
.diffcontext/dist. Keep Tree-sitter 0.25.2 pinned (0.26 crashed real redis.ts).
Run .venv/Scripts/python.exe -m unittest discover -s tests -v for source checks.
