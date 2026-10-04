# A reproducible CodeBearing demonstration

This is a recording plan and hands-on walkthrough. **No video is included or
claimed to have been recorded.** Use the public authored refund fixture, so the
demo needs no private application source, credentials, database or model API key
for CodeBearing. Your coding assistant uses its own account.

## Prepare a separate practice project

Clone the CodeBearing repository if you do not already have it. From its root:

```powershell
Copy-Item -Recurse evals/coding_tasks/refund-rounding/repo ../codebearing-demo
Set-Location ../codebearing-demo
python -m unittest discover -v
codebearing setup --client codex
```

Use `--client claude` or `--client cursor` for your assistant. The commands above
are PowerShell; on macOS/Linux use `cp -R` instead of `Copy-Item` and `cd` instead
of `Set-Location`. Keep the original evaluation fixture unchanged.
Existing tests pass despite the bug: they cover whole cents and do not exercise
the fractional-cent case. There is no Git history in this copied fixture, so
demonstrate task investigation rather than Git revision tools.

Open the practice project in your assistant, approve/enable CodeBearing and start
a fresh chat. Use this prompt:

> Refunds must match the invoice's per-line rounding. For ["0.005", "0.005"],
> both totals should be Decimal("0.02"). The refund currently returns 0.01.
> Use CodeBearing's investigate tool before editing. Show the relevant source,
> dependencies, confirmed lessons and gaps. Fix the refund, add a regression test
> for this case, and keep the preview response unchanged.

## Capture these moments

| Moment | Show | Explain |
| --- | --- | --- |
| Problem | Task and passing original tests | Passing tests can miss a real boundary case. |
| Evidence | Actual CodeBearing `investigate` invocation | The assistant asks a local context server for evidence. |
| Context | Cited refund and rounding source, dependencies, warnings/omissions | The package exposes what was selected and what is missing. |
| Repair | Assistant's diff and new regression | The assistant edits; CodeBearing does not. |
| Verification | Test command and output | Executable tests establish this repair's behavior. |

Do not script fake tool activity or remove an inconvenient warning. If localization
misses the intended symbol, show the recovery: `search_symbols`, then investigate
an exact returned ID. Record any manual intervention. Save the task, tool output,
diff, regression and test output together if you want others to reproduce it.

The fixture is deliberately authored and its expected answer is public. A
successful demo is **not** a held-out quality evaluation or proof of token savings.
For the correction-memory segment, use the verified
[memory continuity walkthrough](demos/MEMORY_CONTINUITY.md). It reproduces a
recorded agent test gap in wholly authored code, proposes a lesson, and shows it
absent before review, present after explicit operator review in a fresh process,
and excluded after source changes. The operator flag is a deliberate demo action,
not authenticated human approval or automatic learning. A fresh process is not a
later LLM session, and this demonstrates storage/retrieval rather than model
efficacy. Keep those distinctions in the narration.

## Evidence you can responsibly show

- [Original BookMyShow comparison](demos/BOOKMYSHOW_TRIAL.md): both conditions passed
  five independent checks. Real MCP use was observed; no correctness advantage.
- [Booking-failure comparison](demos/BOOKING_FAILURE_TRIAL.md): both conditions
  passed six independent checks. It exercises durable confirmation and rollback
  behavior with mocked SQL/Redis, not live integration.
- [Exploratory Luna comparison](demos/LUNA_BOOKING_TRIAL.md): requested matched
  smaller-model settings, one authored task; assisted passed 6/6 independent
  checks and control 3/6. Workflow interruptions complicate the comparison.
  These are correlated checks on one task, not a general success rate.
- [Compact MCP evidence](work-items/WI-018-compact-mcp-evidence/FEATURE.md): one frozen
  BookMyShow report's JSON went from 292,449 to 40,259 bytes; its complete SDK
  response went from 649,084 to 101,729 bytes. This measures presentation bytes,
  not model tokens, billing or coding quality. Short reports can grow from
  disclosure metadata.

- [Repeated smaller-model packet comparison](demos/SMALL_MODEL_PACKET_TRIALS.md):
  32 actual calls with observed usage and frozen independent graders. Lexical
  passed15/16 and hybrid12/16 across two requested models; no general advantage
  demonstrated. A missing exception declaration was repaired and eight separately
  labeled same-task retry checks passed. Original results remain unchanged.

Actual usage includes CLI scaffolding and cache effects. USD remains unknown;
do not turn the packet allowance or presentation bytes into a cost claim.

A concise description for the demo:

> CodeBearing is a local MCP context engine for coding assistants. It combines
> static code relationships, bounded context selection and developer-confirmed
> correction memory, with visible omissions and executable evaluation tooling.

Avoid saying it is an autonomous coding agent, supports every stack, eliminates
hallucinations, or has a proven general win rate.
