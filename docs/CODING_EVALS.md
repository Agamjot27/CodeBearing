# Controlled coding-task experiments

The harness checks executable fixes on three synthetic development repositories:
refund rounding, pagination offsets and retry exhaustion. This is a local experiment
framework, not a held-out benchmark or evidence that DiffContext improves a model.

A separate interactive smaller-model smoke trial requested matched GPT-6 Luna/low
settings: assisted 6/6 independent checks, control 3/6 on one authored booking task.
Own tests passed in both; process restrictions and test-harness mistakes required
continuation. No billed usage or causal benefit is established. See
[the full trial record](demos/LUNA_BOOKING_TRIAL.md). This is distinct from the
one-response packet harness below; reuse its fixed grading boundary for broader
model comparisons rather than treating chat workflow timing as model latency.

Grading and command adapters use bounded file-backed subprocess I/O and owned
process-tree/group cleanup on timeout (D-020/F-030). Cleanup adds bounded time to
the deadline; retained output is limited but temporary disk output has no quota.
Windows cleanup is tested locally; POSIX/hosted CI remains unverified here.

## Run the model-free self-check

From the project root:

```powershell
python evals/coding_bench.py self-check
python evals/coding_bench.py self-check --condition-set hybrid
```

The self-check verifies that each original bug fails tests, then runs 12 reference
trials and 12 unchanged-code trials across four conditions. References should pass;
unchanged code should fail. It checks that confirmed synthetic lessons enter memory
context and stale lessons do not. No model/provider is called. Artifacts go into
an ignored `.eval-runs/self-check-<id>` directory unless you specify `--output`.
The opt-in hybrid set runs 21 reference and 21 unchanged trials across seven
conditions, including six fresh and six stale memory checks. These are calibration
outcomes, never model-success statistics.

Acceptance tests (`checks.py`) and reference fixes (`reference.json`) live outside
each task's `repo/`. Only source/public tests from `repo/` are copied and indexed.
Reference fixes are read only by calibration or explicitly scripted test runners.
Model packet preparation does not read their contents. This separation prevents
accidental retrieval leakage; it is not OS access isolation.

## Conditions and fairness

| Condition | Evidence supplied |
| --- | --- |
| `lexical` | Existing lexical search ranks matched files; complete files are packed without graph expansion or lessons |
| `graph` | Bounded investigator gathers related symbols; no lesson database |
| `memory` | Same investigator with an explicit confirmed pre-task synthetic lesson |
| `stale_memory` | Same fixture lesson, then an evidence-file comment change makes it stale before retrieval |
| `hybrid` | Code-aware lexical/graph ranking, with no lesson database |
| `hybrid_memory` | Hybrid ranking and scoped lesson reservation with confirmed synthetic memory |
| `hybrid_stale_memory` | Hybrid with the same stale-evidence control; stale advice is excluded |

The first four retain legacy policies and remain the default. Add
`--condition-set hybrid` to prepare/run/self-check for all seven. This adds three
calls per task before retries. Use the same condition set when preparing and
replaying. Reports compare graph/hybrid, fresh and stale counterparts, and advice
controls within hybrid; only tasks scored on both sides enter a pair.

All conditions use the same task description, editable-source rules, requested
model ID, temperature 0, maximum estimated full-prompt input budget and declared
output-token budget. The context budget reserves task/instruction overhead. They
can consume different actual token counts. The byte heuristic is not a real model
tokenizer. Runner-reported usage is recorded, not independently verified; missing
usage/cost stays null. An adapter must actually honor the requested model/settings.
Reported output above the declared budget is an unscored budget violation.

Manifest queries are preassigned development localization hints, not a zero-shot
localization benchmark. Conditions rotate deterministically across tasks to reduce
a fixed order effect. Three tasks are too few for statistical conclusions, and
there are no repeated stochastic model samples yet.

The lesson text is authored as **synthetic pre-task fixture data**, not claimed to
come from an actual prior agent correction. Confirmation is still an attestation,
not proof a correction happened. These conditions test retrieval/freshness plumbing.
Real memory-benefit claims require earlier observed corrections and later unseen tasks.
Stale evidence changes only a comment; this intentional control changes source hashes.

## Prepare packets for independently collected responses

```powershell
python evals/coding_bench.py prepare --model YOUR_MODEL_ID --output .eval-runs/trial-01
```

This writes 12 JSON requests into `requests/`. Each contains `prompt`, declared
settings, editable paths, source hashes, trial ID and a stable `request_hash`.
Send only `prompt` as task evidence to the selected model; envelope metadata is not
part of the estimated prompt budget. Do not give the model acceptance/reference
assets or change tests. The model should return JSON with an `edits` mapping of
relative filenames to full replacement source text. This is a one-response editing
evaluation, not an interactive tool-using coding-agent comparison.

Collect responses in UTF-8 JSON:

```json
{
  "schema_version": 1,
  "responses": {
    "refund-rounding:graph": {
      "schema_version": 1,
      "model": "YOUR_MODEL_ID",
      "request_hash": "COPY_FROM_THE_CORRESPONDING_PACKET",
      "status": "ok",
      "edits": {"refunds.py": "FULL REPLACEMENT SOURCE HERE"},
      "usage": {"input_tokens": null, "output_tokens": null, "cost_usd": null}
    }
  }
}
```

Use an entry for each task/condition. The example is a format illustration, not a
valid fix or completed response. Replay the collected edits:

```powershell
python evals/coding_bench.py run --model YOUR_MODEL_ID --output .eval-runs/trial-01 --replay responses.json
```

Model ID and request hash must match exactly. Replay grades recorded edits without
calling a model. Incomplete responses remain unscored errors, not fabricated failures.
You may fill in missing responses and rerun using the same replay path/configuration.

## Connect an external model adapter

For live trials, provide a local command that reads one request JSON from stdin
and writes exactly one response JSON to stdout, following the same envelope above.
The adapter sends `prompt` to the chosen model, honors model/temperature/output
settings, parses its edits, and wraps them with the exact model/request hash and
provider usage. Diagnostics belong on stderr. An optional built-in OpenRouter
adapter now uses the standard library; no account/model has been verified here.

For OpenRouter, set `OPENROUTER_API_KEY` locally and select an exact model ID.
Never put the key in command arguments or tracked files. Local preflight:

```powershell
python evals/coding_bench.py check-provider --model YOUR_EXACT_MODEL_ID
```

This makes no network calls and does not validate account/model availability.
When ready for actual provider calls:

```powershell
python evals/coding_bench.py run --openrouter --model YOUR_EXACT_MODEL_ID --condition-set hybrid --output .eval-runs/live-openrouter-01
```

This dispatches up to 21 calls on the three authored tasks before retries, sequentially.
Optional `--provider PROVIDER_SLUG` pins provider-only routing. Strict returned-model
equality rejects canonical aliases/variants that differ from the requested string;
no silent equivalence is assumed. JSON mode and supported-parameter requirements
can exclude models. No automatic fallback model or retry is requested. Model/API
errors remain unscored; paid unusable responses retain validated reported usage.
Missing costs stay unknown. Per-attempt provider/generation metadata is saved.
`--runner-timeout` limits socket operations for this direct HTTP adapter, not a
strict total deadline. We have only tested with fake transport responses so far.

Field contracts follow official [completion API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion),
[routing](https://openrouter.ai/docs/guides/routing/provider-selection) and
[usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

For a different provider, the existing custom-command boundary still works:

```powershell
'["python", "adapter.py"]' | Set-Content -Encoding utf8 runner.json
python evals/coding_bench.py run --model YOUR_MODEL_ID --output .eval-runs/live-01 --command-file runner.json
```

The command file is a UTF-8 JSON argument array, avoiding nested native shell
quoting; `--command-json` also accepts an array directly. Command arguments are
passed directly to subprocess without a shell. Use a new
output directory for a different adapter/configuration. Adapters should return
`status: "rate_limited"` or `"provider_error"` with matching model/request hash for
transient failures. A quota response stops further dispatch immediately. There
are no automatic retries or parallel calls. `--runner-timeout` defaults to 60s;
timeout/process/format errors stay distinct from executable task failures.

## Results, checkpoints and scoring

`manifest.json` pins task/source/grader/reference provenance and requested settings.
Policy version 2 also pins selected conditions and every package Python source
hash. Old version-1 outputs require a new directory; changed execution source
rejects resume even if a particular packet's text remains identical.
`runner.json` records adapter identity. `requests/` stores input packets, `trials/`
stores atomic per-trial checkpoints, and `report.json` contains condition summaries
and matched-task comparisons. Candidate edits are stored for reproducibility.
Transient attempt history is retained on resume. Reported cost covers checkpointed
attempts only, and stays unknown if any earlier attempt lacks usage/cost.
Successful delivery does not imply the fix passed tests.

Each trial starts from a fresh copy, confirms the original fails tests, applies only
allowed source edits (200 KB total limit), then runs unchanged public and acceptance
tests in a Python subprocess. Test outcome, diagnostic tails, context-preparation
time, runner wall time, grader time and reported usage are recorded. Repeated
acceptance-failure IDs are a coarse regression signal, not proof of an agent's
reasoning or that it repeated the same underlying mistake.

Passed/test_failed/candidate-timeout/invalid-source-edit outcomes are scored.
Provider/quota/runner/protocol/budget/grader infrastructure errors are unscored and
excluded from success denominators. Matched comparisons include only tasks scored
in both conditions. There are no arbitrary merge thresholds for model success.

Rerunning the same command reuses scored checkpoints and retries unscored trials.
Changed task assets, settings, adapter identity or packet fingerprints require a
new output directory. Checkpoint persistence is atomic per trial; it is not an
exactly-once billing guarantee if interrupted after a provider call but before save.
Recorded replays and reference calibrations are labeled distinctly from live runs.

CLI exits 0 when a complete experiment was delivered, even if every candidate
failed; 1 means failed calibration or unscored/incomplete experiment; 2 means a
configuration/file error. Inspect `report.json`, not just process exit status.

## Execution boundary

Only use trusted local fixtures/candidates here. Python subprocesses isolate imports
and have a grading timeout; they retain the caller's filesystem/network privileges.
This is not a container or security sandbox. The harness edit allowlist does not
limit side effects of executed code. Hostile tasks/candidates require stronger
isolation before execution. Grader output capture is not an adversarial memory cap.

CI runs the model-free self-check. To make a real performance claim, next collect
paired live responses, repeat model samples, and add temporally separated held-out
tasks with genuine prior corrections, executable outcomes and exact usage accounting.
