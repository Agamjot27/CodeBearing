# Current handover

Updated2026-10-05 (Asia/Calcutta). Read after AGENTS.md, then the relevant work item,
decisions and flows. This is the current snapshot; detailed history lives in Git.

## Product/current release

CodeBearing0.9.0 is a local MCP context engine with six read-only tools. Coding
assistants edit/test. Python and optional JS/TS indexing, conservative static call/
import graph, diff/deleted evidence, hybrid retrieval, whole-source budget packing,
confirmed/hash-fresh SQLite lessons and bounded investigation traces are implemented.
Project setup supports Claude Code/Cursor/Codex. Public repository:
https://github.com/Agamjot27/CodeBearing.git. No PyPI publication/frontend/HTTP API.

0.9.0 wheel validated outside checkout and user tool upgraded. Actual configured
interpreter imports installed0.9.0; codebearing --help and six-tool stdio check pass.
Existing chats require reconnect/new chat after stopping only the old read-only
connector tree for Windows locks. Existing BookMyShow user MCP entry preserved.
Release record docs/work-items/WI-029-codebearing-090-release/FEATURE.md; F-046.
Final documentation/release commit and push pending at this snapshot.

## Four authorized phases completed

- WI-024 connected task evidence: captured Luna replay now fits total/confirm/
  transaction at2884/3000 estimated text tokens; still partial with15 omitted
  nonseeds. D-032/F-040; docs/work-items/WI-024-connected-task-evidence/BUG.md.
- WI-025 measured smaller-model packets:32/32 actual calls completed/scored,
  two requested models/four authored tasks/two policies/two repetitions. GPT6Luna
  lexical7/8 vs hybrid5/8; GPT5.6Luna8/8 vs7/8. No advantage established. Observed
  scaffolding-inclusive usage published; USD/backend-attested model IDs unknown.
  D-034/F-043; docs/work-items/WI-025-observed-codex-trials/FEATURE.md;
  docs/demos/SMALL_MODEL_PACKET_TRIALS.md/JSON. No tasks/checks changed after results.
- WI-026 memory continuity: authored analogy to actual recorded agent test gap,
  proposal excluded, explicit operator review, fresh-process retrieval/compilation,
  stale exclusion. No authenticated human or later-model benefit claim. D-033/F-042;
  docs/work-items/WI-026-memory-continuity-demo/FEATURE.md; scripts/demo_memory.py.
- WI-027 quickstart/public demo/README: simpler existing MCP workflow,38 local
  links checked; reproducible storyboard is not a recorded video. D-035/F-045;
  docs/work-items/WI-027-v1-user-guide/FEATURE.md; docs/QUICKSTART.md,docs/DEMO.md.

Additional observed defect WI-028 fixed: referenced conservative local Python
exception declarations/ancestors join complete budgeted excerpts. Separate8/8
retry-only post-result checks pass, not held-out evidence; original32-call matrix
retained. D-036/F-044; docs/work-items/WI-028-python-exception-evidence/BUG.md.

## Verification/next action

Full188 tests passed in81.338s after compiler changes; six investigation fixtures,
two TypeScript budget fixtures and clean wheel/install/setup/stdio/cache checks pass.
Meaningful commits so far e6b7fbb retrieval,9b00438 memory,7ffc2f1 measured trials,
65aa91b exception evidence. Finish release/docs commit, push and verify clean state.
Next research is independent held-out tasks/actual assistant outcomes; don't invent
additional required product phases or claim superiority from authored checks.

## Limits/avoid

Static graphs miss dynamic/type/runtime wiring and general globals. Exceptions
only include conservative same-module declarations; complete modules aren't promised.
Text estimate excludes JSON/CLI scaffolding. Total MCP transport isn't capped;
full-detail reports are new snapshots. Whole-file hashes over-invalidate lessons.
CLI trial temperature is default/output allowance postchecked; solver isolation
is not a hostile-code sandbox. Prior real authored trials and original68 source
hash checks are recorded in docs/demos; don't generalize their metrics.
Do not edit original projects/read credentials/shared dependency junctions or commit
.eval-runs/.test-tmp/.diffcontext/dist artifacts. Tree-sitter0.25.2 remains pinned:
0.26 crashed real redis.ts. Relevant check: .\.venv\Scripts\python.exe -m unittest discover -s tests -v.
