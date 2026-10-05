# WI-030 — Redesign the public README

Status: complete
Opened / updated: 2026-10-06

## Request and scope

Make the README beautiful and engaging, inspired by Reef's visual hierarchy.
Use original assets, explain actual output, retain straightforward onboarding
and link evidence without inventing product capabilities or comparative claims.
No runtime, infrastructure, model calls or package release changes.

## Starting state and execution path

README.md currently has a text title, install commands, a capability list and
documentation links. F-045 describes the real setup/investigate path. The user
approved the presentation redesign after a read-only comparison with Reef.

## Implementation and decisions

Implemented: original repository-local SVG banner and architecture graphic, grouped
navigation, tool and memory tables, and a clearly labeled excerpt captured from
the public refund fixture. D-037 records presentation decisions; F-045
references the new entry points without claiming a runtime change.

## Attempts and outcomes — update during work

Read the existing README, release record, onboarding flow, tool signatures and
public demo. Found older 0.8.0 references in linked MCP instructions; synchronize
those installation examples with the current 0.9.0 release in this cycle.
Also found a CI wheel-check command still targeting 0.8.0. Left CI unchanged
and recorded the known follow-up in HANDOVER rather than fold a runtime check
into styling. A separate bug record is required before implementing that fix.

## Verification

Checked 50 README destinations (local files and section anchors all valid).
Both SVGs parse as XML, have accessible title/description elements, and contain
no scripts or remote asset dependencies. Re-ran the public compile command via
.venv/Scripts/python.exe: README excerpt is verbatim within result.text; five
symbols, 514 estimated tokens, 2000 allowance and disclosed warning match.

Rendered upper and lower local Markdown previews in headless Edge at 1280x2200
and inspected both images: banner, diagram, source block and tables are readable.
Initial sandboxed Edge failed Windows IPC permissions; an approved headless run
succeeded. Preview uses local substitutes for remote Shields badges and
GitHub-like CSS, so it is not a live GitHub rendering verification. Preview files
and browser profile are ignored under .test-tmp. git diff --check passes.
No backend tests rerun for this documentation-only change.

## Handoff / completion

Complete: README.md, docs/assets/codebearing-banner.svg and architecture.svg,
docs/README_EXAMPLE.md, linked MCP 0.9.0 examples, D-037, F-045 and HANDOVER.md.
Product behavior and release version are unchanged. Shields availability and
GitHub rendering remain external; no hosted site or recorded video introduced.

## Git trace

Predecessor release documentation commit 928e24d. Find this change with
`git log --oneline -- docs/work-items/WI-030-readme-presentation/FEATURE.md`.
