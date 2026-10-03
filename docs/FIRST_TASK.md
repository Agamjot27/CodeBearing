# Your first CodeBearing-assisted change

This is a hands-on walkthrough, not a recorded model-quality result.

1. Install CodeBearing using the README, then open a supported project you own.
2. Run `codebearing setup --client cursor` in that project (or claude/codex).
3. Open/restart the assistant and enable/approve CodeBearing.
4. Give it a specific real bug and its observable expected behavior. Ask:

   > Use CodeBearing's investigate tool for this bug before changing code. Show
   > the selected functions, important dependencies, applicable lessons and gaps.
   > Explain the fix, apply it, and run the existing tests.

5. Check that its tool activity actually names CodeBearing. Read cited files and
   omissions; a connected server does not guarantee the assistant used it.
6. Review the diff and test results. Save the original task, tool response, diff
   and test output if you want a reproducible demonstration.

For practice, copy `evals/coding_tasks/refund-rounding/repo` to a separate folder
and open that copy. Keep the evaluation inputs unchanged. Ask:

> Refunds must match the invoice's per-line rounding. For ["0.005", "0.005"],
> both totals should be Decimal("0.02"). Investigate why the refund returns 0.01,
> fix it and add a regression test while keeping the preview response unchanged.

The fixture currently rounds the sum instead of rounding each line. Its existing
public tests cover whole-cent refunds and do not catch this fractional-cent bug.
This is an authored example, not independent evidence of improved coding
performance. No assistant has run this walkthrough as a measured trial yet.

If CodeBearing cannot identify the intended function, ask the assistant to use
search_symbols and choose an exact symbol ID. If it reports partial context,
inspect omissions and warnings before making the change. Static graphs miss
some runtime/framework relationships.
