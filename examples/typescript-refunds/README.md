# TypeScript refund example

Small source-only fixture for indexing and context compilation. It needs no npm
installation and is not an executable application or a coding benchmark.

Install the project's `typescript` extra, then run from the project root:

```powershell
python -m diffcontext --repo examples/typescript-refunds compile --symbol billing.ts:refundTotal --max-tokens 2000
```

The expected packet contains `refundTotal`, its `roundTotal` helper and the
`cancelOrder` caller. The `.js` import points to a local TypeScript source file.
Static analysis does not resolve the dynamic built-ins `Math.round` or `reduce`.
