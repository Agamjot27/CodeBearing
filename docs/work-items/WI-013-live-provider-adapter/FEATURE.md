# WI-013 — Accountable live provider adapter

Status: completed
Opened: 2026-10-04

## Scope / baseline

At 4a71cde, paired trials require a user-written command adapter. Add an explicit
OpenRouter HTTP adapter using the standard library, preserving requested model,
temperature and output limit; classify quota/HTTP/protocol/model errors, retain
reported usage even when a paid response is unusable, and checkpoint provider
identity. No account/key/model selected and no paid call is authorized by this
implementation alone. Credentials stay in OPENROUTER_API_KEY, never arguments.

## Execution and rationale

coding_bench.py:main() → providers.py:OpenRouterRunner → fixed HTTPS completion
endpoint → checked edits envelope → existing experiment grading/checkpoints.
Official API/routing/accounting docs inspected; no provider SDK needed. D-022/F-032
will explain the implementation. Offline transport tests exercise all calls.

## Verification / handoff

Implemented providers.py:OpenRouterRunner with fixed HTTPS endpoint, no redirects,
environment-only key, JSON mode, requested settings, optional provider pinning,
parameter support and strict returned-model check. No retries/fallback model.
CLI --openrouter and check-provider are explicit; local preflight proves settings
only, not API availability. response_usage() now precedes status validation to
retain paid failures; settings and per-attempt typed provider metadata are saved.
Unknown costs remain null and malformed usage is rejected, including falsy
non-mappings previously accepted as empty usage. No SDK added.

Seven offline tests cover transport/request contracts, quotas, model mismatch,
partial/refused/malformed/oversize output, secret exclusion, local preflight and
paid-failure cost retention. First six focused tests passed, then full 149-test
suite passed in 123.820 seconds with extras and process permissions. Final focused
accounting checks add per-attempt provenance/cost retention across resume and
falsy-usage rejection: seven provider and nine legacy experiment checks passed
after those final changes. No live requests, actual model outcome or savings claim.
Official API docs used redirect to newer canonical URLs; documentation links use
the resolved completion/accounting pages. No substantive failed implementation
experiment occurred in this slice. Independent benchmark requirements documented
in docs/INDEPENDENT_EVALS.md; import/isolated grading remain unimplemented.

Public datasets need independent selection and isolated executable environments;
our three authored tasks remain development. User provider/model choice pending.
Next select/configure a model locally and integrate an independent execution/data
protocol. No key or account was inspected during this work.
Use git log --oneline -- docs/work-items/WI-013-live-provider-adapter/FEATURE.md.
