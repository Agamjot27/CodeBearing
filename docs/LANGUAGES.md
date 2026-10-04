# Language support

Python uses the standard-library AST parser. TypeScript and JavaScript use an
optional syntax-tree adapter. Install both MCP and parser extras for those projects:

```powershell
python -m pip install ".[mcp,typescript]"
python -m diffcontext --repo examples/typescript-refunds compile --symbol billing.ts:refundTotal --max-tokens 2000
```

For installation from Git, use
`python -m pip install "codebearing[mcp,typescript] @ git+https://github.com/Agamjot27/CodeBearing.git"`.
The same launcher and six MCP tools work with either language. No Node runtime,
build, model key, or execution of the target repository is required.

| Source | Extracted evidence | Resolved relationships |
| --- | --- | --- |
| Python `.py` | Top-level functions and class methods | Existing static local/imported calls and self/cls methods |
| TypeScript `.ts`, `.mts`, `.tsx` | Named top-level functions, assigned arrows/function expressions, class methods | Direct local calls, relative ESM named/default/namespace imports, same-class `this.method` |
| JavaScript `.js`, `.mjs`, `.jsx` | Same callable forms | Same conservative ESM relationships |

TSX/JSX parsing preserves source excerpts; it does **not** resolve component
references or calls inside JSX. Anonymous default functions, nested callback
bodies, CommonJS, re-exports, package imports, tsconfig aliases, inheritance and
type-checker/runtime dispatch are not resolved. Destructuring, shadowing,
reassignments and ambiguous module choices prevent guessed edges. Relative
extensionless/index imports and `.js` to TypeScript source mapping resolve only
when there is a unique candidate. This is not a TypeScript language server.

Declaration files `.d.ts`/`.d.mts`, `.min.js`/`.min.mjs`, hidden paths and excluded
directories such as node_modules are ignored. Files larger than 1 MB and symbolic
links are skipped with warnings. Invalid syntax or non-UTF-8 web source keeps its
captured bytes but receives no symbols/hash; it cannot validate memory evidence.
Without the parser extra, Python still works and web files produce an explicit
unindexed-files warning. Inspect warnings and unresolved Git changes.

All adapters feed the same snapshot, graph traversal, token-budget compiler,
Git old/current comparison and confirmed-memory freshness checks. The compiler
also includes recognized referenced same-module Python exception declarations
and local exception ancestors. Those declarations share the complete excerpt's
budget; imported/dynamic/ambiguous classes and general globals remain unresolved.
Mixed-language repositories can be indexed, but HTTP calls, generated clients and other
cross-language runtime relationships are not inferred. Go, Java, Rust and other
languages have no adapters yet. A ready investigation means selected static graph
coverage, not a complete semantic model of the application.

Verification: `tests/test_typescript.py`, `tests/test_language_boundary.py`,
and `evals/typescript.py`. The evaluation has one authored fixture and two budgets;
it measures expected-symbol retrieval and estimated budget compliance, not coding
accuracy or superiority over another project. Decisions D-017; execution F-027.
