# Development workflow

These are the user's standing development requirements for this repository.

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
