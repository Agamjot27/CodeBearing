# WI-032 — Document overlap and a fair comparison protocol

Status: complete
Opened / updated: 2026-10-06

## Request and scope

User requested consistent CodeBearing naming and a defensible comparison with
Aider, Serena, code-graph MCP servers and existing assistant capabilities.
This record covers: document overlap and a fair comparison protocol.

## Starting state and execution path

Baseline b216c0e. Package/imports/launcher module still diffcontext; distribution
and public commands CodeBearing. F-045/F-046 describe setup and wheel checks.
CI checks an obsolete 0.8.0 wheel although released source is 0.9.0.
No competing-tool performance benchmark has been run.

## Implementation and decisions

Scoped before edits. Preserve historical work items and model-result fingerprints.
Current package/docs may change; existing user projects and installed tools will
not be changed. D-038 (namespace) / D-039 (comparison) apply as relevant.

## Attempts and outcomes

Read current package, tests, wheel checker and primary competitor documentation.
Created docs/ALTERNATIVES.md with linked primary sources checked 2026-10-06:
Aider repomap docs; oraios/serena README; CodeGraphContext README; current Cursor
search docs; Anthropic how-Claude-Code-works docs. Includes reason-to-choose
trade-offs, an interview answer, scope of our original trials, and two proposed
comparison tracks (retriever versus matched-host workflow). All are clearly
labeled unexecuted; no competitor/model installation or live trial occurred.

Current Cursor codebase-indexing URL redirects to local Instant Grep/Explore
subagent docs, so avoided stale embedding-index claims. Serena and Claude
already document memory; our review/freshness policy is not claimed unique.
A guessed graph-server URL was inaccessible; used the verified
CodeGraphContext/CodeGraphContext repository instead.

## Verification

Primary-source capability review complete; local documentation destinations
checked. Naming tests/wheel are recorded in WI-031, not competitor validation.
Comparative feature review is not a measured performance benchmark.

## Handoff / completion

Complete: docs/ALTERNATIVES.md and README entry, D-039. Documentation-only;
no runtime path or benchmark result changed. Proposed experiments are unexecuted.

## Git trace

Predecessor b216c0e. Use git log --oneline -- this record for introducing commits.
