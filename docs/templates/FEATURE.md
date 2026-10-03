# <WI-ID> — <feature title>

Status: scoped | in progress | blocked | complete
Opened / updated: <date>

## Request and scope

What the user needs, why now, acceptance criteria, and explicit scope limits.

## Starting state and execution path

Existing behavior and actual `file:function → file:function` path. Link affected
FLOW.md IDs. Label proposed paths as proposed until implemented.

## Implementation and decisions

Changed files/functions, data transformations, database/external interactions,
contracts, and relevant D-XXX entries. Explain the real reason for each approach.

## Attempts and outcomes — update during work

For each meaningful attempt: action, observed outcome, what worked or did not,
and the resulting next step. Preserve unsuccessful approaches. If none occurred,
say so; do not invent a troubleshooting history.

## Verification

Exact commands/checks, observed results, what they establish, and limitations.
Keep pending verification separate from completed checks.

## Handoff / completion

Remaining work, blockers, files/functions currently being modified, and next
concrete action. Link HANDOVER.md and update affected flows/decisions in the same
cycle. Completed records must state any remaining limitations.

## Git trace

Record known earlier commits when useful. Find commits for this record using
`git log --oneline -- docs/work-items/<directory>/FEATURE.md`.
Do not insert a fictitious introducing hash or claim a commit was pushed unchecked.
