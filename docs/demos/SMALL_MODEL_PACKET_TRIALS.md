# Smaller-model packet trials with observed usage

Observed 2026-10-05, WI-025. **This experiment did not demonstrate a hybrid-context
advantage.** All 32 planned calls completed and were scored; no operational error,
tool contamination or post-generation budget violation occurred.

| Requested model | Context | Passed / scored | Reported input tokens | Cached input subset | Reported output tokens |
| --- | --- | --- | --- | --- | --- |
| gpt-6-luna | Lexical complete matched files | 7/8 | 113,380 | 0 | 845 |
| gpt-6-luna | Hybrid symbol/dependency excerpts | 5/8 | 115,060 | 39,168 | 769 |
| gpt-5.6-luna | Lexical complete matched files | 8/8 | 99,254 | 9,984 | 1,998 |
| gpt-5.6-luna | Hybrid symbol/dependency excerpts | 7/8 | 100,930 | 19,968 | 1,865 |

The [machine-readable artifact](SMALL_MODEL_PACKET_TRIALS.json) records every
request hash, result, observed usage, engine/acceptance hashes and CLI version.
Counts include Codex's system/tool scaffolding, not just the supplied packet.
Cached input is already part of input. Reported reasoning output is a breakdown,
not a separate amount to add: gpt-5.6-luna lexical 1,122, hybrid 1,070;
gpt-6-luna zero. **Dollar cost is unknown** under the existing account sign-in.
Cache differences and model defaults prevent inferring savings from output counts.

## Protocol

Four wholly authored development tasks: refund rounding, pagination offset,
retry exhaustion and transaction rollback. Each model received both conditions
twice in fresh CLI sessions. Task and condition order reverse on repetition two.
Two earlier gpt-6-luna refund pilot calls established usable output/usage; they are
excluded from the 32-call matrix. No task/check was changed after seeing results.

All task queries are exact symbol names, so this does **not** evaluate natural-language
seed selection, held-out repositories, interactive MCP use or engineering memory.
Small authored files make this a narrow fixed-packet comparison. Repetition does
not turn four tasks into 32 independent tasks. It is not a model ranking study.

`codex-cli 0.160.0` received an explicit requested model and low reasoning effort.
Successful completion establishes that the CLI accepted the request; the JSON
event stream does not attest a backend model ID. No fallback model is requested.
Temperature is CLI default. Total supplied prompt allowance is **3,000 estimated
tokens**, using the existing UTF-8 heuristic; actual input is larger because CLI
scaffolding is outside that budget. A 4,000 reported-output-token allowance is
checked **after** generation; it is not an enforced provider generation cap.

The runner uses `--ignore-user-config`, `--ephemeral`, a read-only empty temporary
working directory and saved CLI sign-in. It does not inspect/copy credentials;
API-key overrides are removed from its child environment. It instructs no tools
and rejects observed tool traces; all accepted responses recorded zero tool calls.
This trace check is detection after execution, not a hostile-code sandbox.
These CLI mechanisms follow the [official noninteractive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

Packets, captured source hashes, engine hashes and independent grader hashes are
frozen before calls. Edits are restricted to source allowlists; public tests and
external acceptance checks cannot be changed by the model. The existing bounded
trusted Python grader verifies results. Changing acceptance/engine hashes prevents
checkpoint reuse. Operational errors remain unscored and missing usage stays null.

## What failed and what it tells us

- Both gpt-6-luna hybrid retry replacements omitted the module's `TransientError`
  class. The packet included its referring function but omitted that declaration;
  full-file replacement then made acceptance imports fail. This exposed a real
  excerpt limitation and the full-file editing protocol makes it particularly
  costly. Existing graph-covered status means static call coverage, not sufficient
  source for reconstructing a module. A separate WI-028 fix follows these results.
- gpt-6-luna transaction repetition two failed in **both** conditions: rollback
  failure replaced the original error. Seven independently maintained checks catch
  this; a valid JSON response is not a successful fix.
- gpt-5.6-luna hybrid transaction repetition one discarded a client after a
  successful rollback, failing two checks. Its other transaction response passed.

Hybrid packets used more reported input in this small suite. We cannot claim
smaller-model quality or cost improvement from these results. An interactive coding
assistant can inspect complete target files before editing; that behavior is
deliberately absent here. Post-result repairs must remain separate, labelled
development checks rather than rewriting these results or claiming held-out gains.

## Reproduce from a source checkout

This uses existing signed-in Codex account usage. Preparation is model-free;
`run` makes the explicit calls. Choose a fresh output directory:

```powershell
.\.venv\Scripts\python.exe evals/codex_bench.py prepare --output .eval-runs/my-luna-comparison --model gpt-6-luna --repetitions 2
.\.venv\Scripts\python.exe evals/codex_bench.py run --output .eval-runs/my-luna-comparison
```

Repeat with another exact accessible model and a different directory. Results can
vary. Do not resume a prepared run after modifying engine/check files; the harness
rejects that mix. Raw local request/event/results stay ignored; the public artifact
contains only authored-fixture metrics and hashes, without private project source
or local user traceback paths. The pre-WI-028 engine snapshot is retained in its
hashes; later source versions can produce different packets and results.

## Separate post-result exception check

WI-028 now bundles referenced conservative local Python exception declarations and
their local exception ancestors into the same whole, budgeted excerpt. It does not
resolve all globals or promise a complete replacement module. The existing retry
packet grows474→509 estimated tokens before the Codex response-contract reserve.

After that repair, we ran **eight new retry-only development checks**: two models,
two policies, two repetitions. Each model's lexical and hybrid conditions passed
2/2; every candidate passed all five independent checks, with no observed tools
or operational/budget exclusions. [Separate observed records](PYTHON_EXCEPTION_POSTFIX.json)
preserve usage, hashes and outcomes. These post-result checks reuse the same task,
so they are verification of the identified defect, **not held-out improvement
evidence**. The original32-call table above remains unchanged. Transaction failures
from that matrix have not been retested or erased.
