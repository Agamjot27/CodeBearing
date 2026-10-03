# Development workflow

These are the user's standing development requirements for this repository.

## Session continuity — read first

- At the start of every session, read `HANDOVER.md` after this file. Then read the
  linked active work-item record, relevant DECISIONS.md entries, and affected
  FLOW.md paths. Check Git status before modifying files.
- Keep HANDOVER.md a short living snapshot: completed capabilities, current work,
  blockers/broken behavior, next steps, verification, and things to avoid. Update
  it during meaningful milestones and before ending or handing off a session.
- Replace outdated current-state text; put detailed history in work-item records
  and Git. Do not dump transcripts, secrets, or unverified success claims into it.
- Record interrupted work honestly: exact files/functions touched, current failures,
  commands already run, and the next concrete action. Mark planned work as planned.

## Per-feature and per-bug records

- Before implementing a feature or meaningful bug fix, create one dedicated record
  at `docs/work-items/<stable-id>-<slug>/FEATURE.md` or `BUG.md`. Keep that same record
  through completion rather than replacing it with a final summary.
- Use the templates in `docs/templates/`. Record scope/discovery, actual execution
  path, affected files/functions, attempts and outcomes (including unsuccessful
  approaches), verification evidence, remaining limits, and related decisions.
- Update the record as work progresses. Do not invent attempts, causes, metrics,
  or historical reasoning. Label reconstructed baseline notes explicitly.
- Link active work from HANDOVER.md and identify affected flows in FLOW.md.
  Include the work-item record with its implementation/tests/documentation commit.
- A commit cannot contain its own final hash. Find introducing/modifying commits
  with `git log --oneline -- <record-path>`; record earlier hashes when relevant.

## Comments for non-obvious logic

- Comment non-obvious logic while writing or changing it: its purpose, why it is
  needed, callers or downstream assumptions, ordering constraints, and edge cases.
- Explain intent rather than restating syntax. Put comments beside the logic and
  use function/module docstrings for contracts. Keep them synchronized with code.
- Use FLOW.md for cross-file execution and DECISIONS.md for design rationale;
  comments should make the local implementation understandable without duplicating
  those entire documents. Do not add noise to obvious statements.

## Meaningful commits

- Commit regularly after a logically complete module, API, database change,
  retrieval/indexing feature, MCP tool, evaluation component, meaningful fix,
  architectural refactor, or feature test set. Do not wait for an entire feature
  area or project to finish.
- Group trivial edits with the meaningful change they support; do not manufacture
  small or incomplete commits for appearance.
- Use clear conventional messages, e.g. `feat(indexer): ...`, `fix(memory): ...`,
  `test(context): ...`. Inspect staged changes and exclude local artifacts/secrets.
- Include implementation, relevant tests, and synchronized documentation together.
- Preserve real history. The first commit is a baseline of the existing prototype;
  do not fabricate a sequence of earlier development decisions or backdate commits.

## DECISIONS.md

- Record meaningful architectural, technical, implementation, and design choices
  during the development cycle, including the actual reason for choosing them.
- Every entry needs Decision, Context, Alternatives Considered, Why This Approach,
  Trade-offs, and Future Reconsideration. Use stable D-XXX IDs.
- Consider simplicity, correctness, maintainability, cost, latency, observability,
  evaluation requirements, scalability, developer experience, and current scope.
- Do not invent retrospective reasoning or experiments. Identify gaps honestly.
- Never silently erase a changed decision. Mark it `Superseded by D-XXX` and add
  the replacement decision with its rationale.

## FLOW.md

- Document actual execution at file/class/function level, not generic layer arrows.
- Each important flow needs Trigger, Execution Path, Data Transformation, Database
  Interaction, External Interaction, and Output. State explicitly when there is
  no database, network, worker, or model interaction.
- Cover indexing/re-indexing, task and diff localization, graph traversal, context
  and budget selection, lesson proposal/review/retrieval/freshness, evaluation,
  API/MCP requests, investigation loops, frontend requests, and trace loading as
  each is implemented. Mark planned capabilities as not implemented until then.
- Include actual paths, function names, table names, and return behavior. Mermaid
  diagrams are optional supplements; text paths remain required.

## Explainable implementation

Before adding significant libraries, infrastructure, databases, agent frameworks,
retrieval strategies, or abstractions, answer:

1. What problem does this solve?
2. Is it needed now?
3. What simpler alternative exists?
4. What measurable benefit should it provide?
5. How will that benefit be tested?

Update DECISIONS.md and FLOW.md in the same cycle and, where possible, the same
commit as the relevant code. Keep docs honest about implemented vs planned scope.
Git history plus these files must explain what changed, why, how it executes, and
which commit introduced it. Run checks appropriate to the change and report limits.
