# WI-028 — Python packets omit referenced local exception declarations

Status: resolved for narrow same-module exception evidence
Opened: 2026-10-05

## Discovery and reproduction

The fixed-packet smaller-model experiment's hybrid retry replacements omitted
the module's `TransientError` declaration. The existing syntax call graph contains
function/method symbols and imports but no class declaration for this pass-only
exception, so graph-covered does not mean standalone editable-file completeness.
The pre-fix experiment remains published unchanged; this fix is development work
informed by those failures, not independent benchmark improvement.

## Affected execution path

RepositoryService.investigate → investigation.run → context.compile_context →
whole symbol excerpts with module imports, but no local exception declaration.
Input is Index.sources captured bytes. No filesystem reread, model, network or
database interaction is introduced.

## Investigation and attempts

Inspected index._python_unit, context.compile_context and retrying.py. The exception
class has no indexed methods and is absent from the packet despite an except
reference. Proposed narrow same-module AST declaration inclusion, with complete
declarations charged inside the symbol section's existing budget. Avoid general
global-variable resolution, schema changes, or entire-file fallback.

## Root cause and fix

Implemented in context._python_exception_declarations and
context._referenced_exceptions: detect unshadowed references to top-level exception
classes whose inheritance is statically rooted in built-in exception names;
include their captured complete declarations and local exception ancestors.
Other classes/globals and imported/qualified/dynamic bases remain outside scope.
Decorated classes, metaclass keywords, star imports and ambiguous class/base
rebinding are conservatively excluded. Class declarations and local exception
ancestors carry captured path/line citations and are bundled with the complete
symbol excerpt before its existing indivisible budget check. Ancestor discovery
uses a finite fixed point over top-level classes; no file reads or execution.
Per-file declaration parsing is cached only inside this compile call.

This selects a bounded category of declaration, not every class or global value.
Whole classes may contain additional global references this narrow fix does not
resolve. Existing static coverage warnings/semantic limitations still apply.

## Verification

Five new exception-context tests pass (0.007s initially; 0.008s after adding a
star-import case): complete local/ancestor citations, whole-budget seed omission,
argument/assignment/import shadowing, ambiguous/dynamic/decorated declaration
exclusion and captured-source/language boundaries. Core 9/9 and investigation
14/14 regressions pass. diff check reports no whitespace errors.

Read-only retry packet reconstruction now includes the complete TransientError
declaration before run_with_retry. Its make_request prompt estimate is 509 tokens,
versus 474 when declaration selection is patched off, under the same 3000-token
allowance. Status remains ready/graph_covered with its existing scoped meaning.
No model run was made here, and pre-fix matrices were not changed. Actual CLI
tokens/model repair benefit require a separate explicitly labeled post-fix run.

## Handoff / resolution

Ready for parent integration/full-suite verification. Do not change or rerun
existing matrix records as if pre-fix. General constants/classes/global resolution
is intentionally not implemented; replacement-file completeness is not promised.

## Git trace

Parent integration: eight separately labeled post-result retry-only model checks
(two policies ×two repetitions ×two requested models) all passed; five acceptance
checks per candidate. No tools/operational/budget exclusions. This is same-task
development verification, not independent improvement. Records:
docs/demos/PYTHON_EXCEPTION_POSTFIX.json. Original32-call WI-025 results retained.
Full integrated suite188 tests passed in81.338s after this change. D-036/F-044.

Use git log --oneline -- this work-item path for related commits.
