# <WI-ID> — <bug title>

Status: investigating | reproduced | fixing | blocked | resolved
Opened / updated: <date>

## Discovery and reproduction

How found; environment and inputs; reproduction steps; expected versus observed
behavior. Distinguish a suspected bug from a reproduced one.

## Affected execution path

Exact files/functions in call order, relevant FLOW.md IDs, and database/external
interactions. Identify where the path fails and the evidence supporting that claim.

## Investigation and attempts — update during work

Hypotheses, checks performed, observed outcomes, failed fixes, and what each attempt
established. Mark untested hypotheses explicitly; preserve the actual sequence.

## Root cause and fix

Confirmed cause and its evidence; changed files/functions; why the fix addresses
the cause; relevant D-XXX entries; changed flow and local comments.

## Verification

Exact reproduction after the fix, regression checks and results, remaining risks,
and pending verification. A passing unrelated test is not proof of resolution.

## Handoff / resolution

Current blocker or next action while open. When resolved, explain what now works
and any remaining limitation. Update HANDOVER.md and FLOW.md where applicable.

## Git trace

Known related commits and
`git log --oneline -- docs/work-items/<directory>/BUG.md` for this record's history.
