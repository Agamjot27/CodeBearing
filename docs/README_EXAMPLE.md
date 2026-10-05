# Reproduce the README context example

From this repository's root, using a development Python environment with the
package installed:

```shell
python -m codebearing --repo evals/coding_tasks/refund-rounding/repo compile --symbol refunds.py:refund_total --max-tokens 2000
```

Originally captured on 2026-10-06 with source version 0.9.0. The command above
uses the current renamed package; the original excerpt and counts are retained. The README shows two source
sections verbatim from `text`, not a fabricated MCP transcript. The full result
contains five symbols: `refund_total`, `round_line`, `refund_preview`,
`invoice_total` and `PublicTests.test_whole_cent_refund`. Recorded values:
`budget=2000`, `estimated_tokens=514`, `complete=true`, empty `omitted`,
`missing_seeds` and `included_lessons`, plus the static-call warning.

`complete` describes selected graph evidence, not correctness of a repair.
The estimator is `ceil(UTF-8 bytes / 3)` and covers text only. Results may change
when source, compiler behavior or defaults change. No model call, lesson write
or source edit is involved. A future assistant performs the repair separately;
see [the demo](DEMO.md).
