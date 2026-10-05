# Task retrieval

Describe the change in plain language; task investigation now defaults to hybrid:

```powershell
python -m codebearing --repo examples/refunds investigate --task "refund total rounding" --summary
python -m codebearing --repo examples/typescript-refunds search "refund total"
```

TypeScript needs the optional parser extra. The same six MCP tools expose this
behavior; `search_symbols` and `investigate` accept `retrieval: "hybrid"` or
`"legacy"`. Use `--retrieval legacy` with CLI search/investigate to compare the
original policy. Explicit symbol and Git selectors keep their existing packing
behavior; they do not acquire task ranking just because hybrid is the default.

1. Code-aware tokens retain full identifiers and split snake_case/camelCase.
   Small suffix variants handle rounding/round and plurals; generic words are
   ignored. This is lexical matching, not semantic understanding.
2. Per-field BM25 scores names, paths and source with initial weights 3/1.5/1,
   using k1=1.2 and b=0.75. Exact symbol names/IDs have priority. Identical names
   stay tied despite different filenames or memory; more than three best ties
   request a clearer selector.
3. Confirmed lessons may contribute only after scope/evidence hashes match the
   captured source bytes. Search adds normalized lexical score plus at most 0.25
   memory score. A matching lesson can locate an otherwise opaque symbol name.
   Proposed, stale, disputed, missing and mismatched evidence cannot boost rank.
4. At each investigation depth, candidates remain within the bounded caller/callee
   graph of the selected seeds. Seeds lead; other candidates combine 0.60 lexical,
   0.30 inverse graph distance and 0.10 memory. This changes packing priority;
   it never introduces an unrelated lesson scope into graph expansion.
5. Whole-excerpt packing reserves up to 20% of the estimated text budget for
   eligible scoped advice. A seed that fits the full budget takes priority over
   the reserve. A lesson appears only when its scoped code is actually included.
   Omissions, missing seeds, scores and lesson IDs remain visible. Detailed rank
   explanations stay in JSON/trace metadata, rather than consuming code-text budget.

Inspect `search_matches[*].signals/reasons` and `context.retrieval.candidates`.
Hybrid task investigation also exposes `retrieval.seed_selection`: a unique
nonexact highest score starts up to three seeds, greedily covering previously
uncovered matched terms using bounded-pool inverse frequency. Exact/tied queries
retain their ambiguity behavior. This can retrieve disconnected aspects, but
generic task words can introduce distractors and more seeds consume source budget.
Search result order/scores themselves are unchanged. D-029/F-040, WI-021.
Scores are ranking heuristics, not confidence probabilities. `ready` still means
selected static graph coverage, not a correct fix or exhaustive task localization.
Cache mode reuses parse facts; query ranking is recalculated from current evidence.
No embedding model, API key, vector database, network call or target execution is
added. Reading an existing memory database is read-only; search does not create it.

## Evaluation and limits

Run `python evals/hybrid.py`. It compares legacy overlap/BFS/code-first packing
with hybrid on the same captured index, task, depth and estimated text budget.
The seven authored development cases cover split identifiers, an exact name,
a distractor, no match, and fresh/stale memory. Five have nonempty relevance sets;
MRR excludes the two abstention cases, which are checked separately. Code recall
and precision inspect compiled IDs. Single-call local timings exclude indexing
and memory capture and use fixed legacy-first order; they are not a robust speed
comparison. The suite checks budgets, lesson eligibility/scope and abstention,
reports regressions, and does not gate on an invented efficacy threshold.

The saved [local result](work-items/WI-009-hybrid-retrieval/hybrid-local.json) has
MRR 0.20 legacy and 0.90 hybrid over five authored tasks, with no recall regression.
Both policies fail to retrieve the expected code for the broad task "refund";
hybrid also includes two graph neighbors outside the declared relevance set in
the fresh-memory case (precision 1/3). These failures remain in the report. This
is not held-out performance, model accuracy, token savings or a competitor result.

Ranking weights and the reserve are engineering defaults, not learned parameters.
Source comments can influence lexical scores; this is not an injection-defense
claim. All symbols are scored in memory each request; repeated graph rounds score
again. Memory loading still reads freshness evidence and may be expensive for many
lessons. Static graphs miss runtime/framework dependencies. The reserve can trade
code coverage for advice, and whole-file hashes can over-invalidate memory.

The existing coding harness explicitly retains `retrieval="legacy"` for its
lexical/graph/memory/stale conditions. Opt into all seven paired controls with
`python evals/coding_bench.py self-check --condition-set hybrid`; see
[coding evaluation](CODING_EVALS.md). These remain authored development fixtures;
held-out tasks and paired real-model results have not yet been collected.

Rationale D-019, actual execution F-029, work item WI-009. BM25 defaults and IDF
reference: [official Lucene documentation](https://lucene.apache.org/core/9_9_1/core/org/apache/lucene/search/similarities/BM25Similarity.html).
