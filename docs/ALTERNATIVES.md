# Where CodeBearing fits

Reviewed 2026-10-06 using the primary sources linked below. This is a documented
capability comparison, not a head-to-head performance benchmark. Tools change;
claims about other projects are limited to the cited documentation.

## Overlap is real

Code search, dependency graphs, bounded context and persistent memory already
exist in this space. CodeBearing does not claim to have invented them.

| Alternative | Documented approach and reason to choose it | CodeBearing's different scope |
| --- | --- | --- |
| [Aider repo map](https://aider.chat/docs/repomap.html) | Repository symbols/signatures, graph-ranked into a token budget as part of Aider's coding workflow. Choose it for the integrated terminal assistant and repo overview. | A separate MCP evidence service with whole selected excerpts, tracked-change/deleted evidence, reviewed lessons and explicit omissions; not an editing assistant. |
| [Serena](https://github.com/oraios/serena#readme) | Symbol retrieval, references, editing/refactoring, LSP or JetBrains backends, broad language support and persistent memory. Choose it for IDE-style semantic navigation and modification. | Conservative Python/JS/TS static analysis and read-only tools. Our lesson eligibility uses explicit confirmation and source-hash freshness; we do not claim memory itself is unique or semantic resolution is stronger. |
| [CodeGraphContext](https://github.com/CodeGraphContext/CodeGraphContext#readme) | Tree-sitter/optional SCIP indexing, persistent graph databases, call-chain and hierarchy queries, MCP/CLI and file watching. Embedded backends are available; it does not necessarily require a database server. | Bounded context compilation with reviewed lessons and visible omissions, using an in-memory graph plus optional SQLite parse cache. Not a graph analytics/visualization platform. |
| [Cursor search](https://cursor.com/docs/agent/tools/search) | Current docs describe local Instant Grep indexes, regex search and an Explore subagent. Choose built-ins for integrated exploration without extra MCP setup. | A portable context response with citations, graph-selection reasons, packing omissions and reviewed source-validated lessons. Extra setup can be unnecessary when built-ins suffice. |
| [Claude Code](https://code.claude.com/docs/en/how-claude-code-works) | Searches and reads files, edits/tests, manages context, supports auto memory and optional code-intelligence plugins. Choose its normal workflow when those tools solve the task. | An optional evidence layer within that workflow. We do not assume Claude lacks memory or blindly loads entire repositories, or describe its search as a mandatory persistent codebase index. |

Documentation that does not describe a feature is not proof that a tool cannot
provide it. Configurations, plugins and custom workflows can close these gaps.

## The specific engineering choice

CodeBearing combines a **read-only, inspectable context compiler** with
**developer-reviewed lessons whose source evidence is checked before retrieval**.
It exposes why code was selected, what did not fit, and why investigation stopped.
This is a concrete interface and policy choice; it is not proof of better repairs.

Use it when you want to inspect or experiment with that context/memory policy
across supported assistants. Use Serena for stronger semantic editing, Aider for
its integrated workflow, or a graph platform for richer graph analysis. If the
assistant already finds sufficient evidence, adding another retrieval layer may
only add overhead.

An interview answer:

> I built this to explore a specific boundary: a coding assistant can ask a
> separate service for budgeted source evidence and reviewed engineering lessons,
> with citations and explicit gaps. Aider already has graph-ranked repo maps,
> Serena has semantic navigation and memory, and assistants already search code.
> My contribution is the compiler/review/freshness contract and the evaluation
> machinery around it. Whether that combination improves a real workflow is a
> question to measure, not a feature-table conclusion.

## What the existing results establish

The [32-call study](demos/SMALL_MODEL_PACKET_TRIALS.md) compares our own lexical
full-file packets with hybrid excerpts on four authored exact-symbol tasks.
It is not Aider versus CodeBearing, Serena versus CodeBearing, or an evaluation
of Cursor/Claude's normal exploration. Its results and negative outcomes remain
unchanged. The [memory demo](demos/MEMORY_CONTINUITY.md) checks persistence and
stale exclusion, not downstream model success.

## A fair head-to-head protocol — proposed, not executed

Two questions require different experiments:

1. **Retriever comparison:** Freeze repository revisions and independent tasks.
   Compare CodeBearing packets, Aider maps plus a declared source-loading policy,
   and Serena/CodeGraphContext query policies. Share a tokenizer and supplied-text
   budget; preserve headers/metadata in the allowance. A map is not full source,
   so disclose representation differences rather than score missing bodies as a
   tool failure. Assess dependency coverage, irrelevant content, cold/warm latency
   and total supplied tokens against reviewer-checked evidence.
2. **Assistant workflow comparison:** For each host separately, run its normal
   built-ins, then the same host with CodeBearing, Serena or CodeGraphContext.
   Hold model/settings/task fixed; leave built-ins available in all arms. Do not
   compare different provider models as if only retrieval changed. Treat Aider's
   full workflow as a separate system-level comparison.

Pre-register tasks, acceptance checks, time limits and failure rules before
running. Use untouched project copies, blind executable graders, repeated trials
and counterbalanced ordering. Record tool calls, setup/indexing cost, cold/warm
cache conditions, wall-clock repair time, input/output/cached token usage and
actual reported charges when available. Unknown billing stays unknown.

Measure memory separately: no lesson, relevant confirmed lesson, proposed lesson,
and stale lesson, with the same correction information available to competing
memory mechanisms. Do not give CodeBearing a hidden answer and call the outcome
a retrieval win. Report solved tasks, regressions and intervals, not individual
assertions as independent successes. Avoid tuning on the held-out suite.

No automatic competitor installer, live provider run or benchmark result is
included here. A documentation comparison answers architectural trade-offs; this
protocol describes the evidence needed to answer time, token and repair quality.
