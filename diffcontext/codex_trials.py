"""Opt-in Codex packet trials; distinct from capped API-provider experiments.

Uses saved CLI sign-in without inspecting credentials. CLI temperature is default
and output tokens are checked after completion, not capped at the provider. Token
usage includes Codex scaffolding; no dollar estimate or verified model ID is made.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .coding import apply_edits, grade, trial_workspace
from .experiments import fingerprint, make_request, write_json
from .processes import run_bounded

PROTOCOL = "codex-packet-v1"
CONDITIONS = ("lexical", "hybrid")
RESPONSE_INSTRUCTION = (
    "\nCODEX PACKET RESPONSE CONTRACT: Do not inspect files or invoke tools, MCP, "
    "shell commands, web search, subagents or skills. All available repository "
    "evidence is above. Return only JSON with an edits array; each element has "
    "path (an editable relative path) and content (full replacement source). "
    "This array replaces the earlier edits-mapping output instruction.\n"
)


def output_schema(paths):
    return {"type": "object", "properties": {"edits": {"type": "array", "items": {
        "type": "object", "properties": {"path": {"type": "string", "enum": list(paths)},
        "content": {"type": "string"}}, "required": ["path", "content"],
        "additionalProperties": False}}}, "required": ["edits"], "additionalProperties": False}


def engine_hashes():
    import hashlib
    package = Path(__file__).resolve().parent
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(package.glob("*.py"))}


def grader_hash(task):
    import hashlib
    return hashlib.sha256((task.directory / "checks.py").read_bytes()).hexdigest()


def parse_events(text: str) -> dict:
    """Fail closed on truncation/malformed traces and any tool interaction.

    Empty working roots/config isolation reduce accidental extra evidence; the
    trace check establishes that accepted responses used no external tool. It is
    detection after execution, not a security sandbox for hostile models/code.
    """
    try:
        events = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not events or any(not isinstance(event, dict) for event in events):
            raise ValueError
    except (ValueError, TypeError):
        return {"status": "invalid_trace", "usage": None}
    allowed_events = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error",
                      "item.started", "item.updated", "item.completed"}
    if any(event.get("type") not in allowed_events for event in events):
        return {"status": "invalid_trace", "usage": None}
    finished = [e for e in events if e.get("type") == "turn.completed"]
    usage = None
    if len(finished) == 1 and isinstance(finished[0].get("usage"), dict):
        raw = finished[0]["usage"]
        usage = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
            value = raw.get(key)
            usage[key] = value if type(value) is int and value >= 0 else None
        if (usage["cached_input_tokens"] is not None and usage["input_tokens"] is not None
                and usage["cached_input_tokens"] > usage["input_tokens"]):
            return {"status": "invalid_usage", "usage": None}
    items = [e.get("item", {}) for e in events if str(e.get("type", "")).startswith("item.")]
    if any(not isinstance(item, dict) or item.get("type") not in {"reasoning", "agent_message"} for item in items):
        return {"status": "tool_contamination", "usage": usage}
    if len(finished) != 1 or any(e.get("type") in {"turn.failed", "error"} for e in events):
        return {"status": "provider_error", "usage": usage}
    messages = [e["item"].get("text", "") for e in events if e.get("type") == "item.completed"
                and isinstance(e.get("item"), dict) and e["item"].get("type") == "agent_message"]
    try:
        candidate = json.loads(messages[-1])
        if not isinstance(candidate, dict) or set(candidate) != {"edits"} or not isinstance(candidate["edits"], list):
            raise ValueError
        edits = {}
        for row in candidate["edits"]:
            if (not isinstance(row, dict) or set(row) != {"path", "content"}
                    or not isinstance(row["path"], str) or not isinstance(row["content"], str)
                    or row["path"] in edits):
                raise ValueError
            edits[row["path"]] = row["content"]
    except (ValueError, TypeError, KeyError, IndexError):
        return {"status": "invalid_candidate", "usage": usage}
    return {"status": "ok", "usage": usage, "edits": edits, "tool_calls": 0}


class CodexPacketRunner:
    def __init__(self, binary=None, timeout=180):
        self.binary = binary or shutil.which("codex")
        if not self.binary or not 1 <= timeout <= 300:
            raise ValueError("Install/sign into Codex CLI; timeout must be 1–300 seconds.")
        self.timeout = timeout

    def __call__(self, request):
        # Never inherit API key overrides into an account-auth experiment. Let
        # Codex itself use existing saved sign-in; do not read/copy auth files.
        child_env = os.environ.copy()
        for name in ("CODEX_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
            child_env.pop(name, None)
        with tempfile.TemporaryDirectory(prefix="codebearing-codex-packet-") as directory:
            cwd = Path(directory)
            schema = cwd / "response.schema.json"
            schema.write_text(json.dumps(output_schema(request["editable_files"])), encoding="utf-8")
            command = [str(self.binary), "exec", "--json", "--ephemeral", "--ignore-user-config",
                       "--skip-git-repo-check", "--sandbox", "read-only", "--color", "never",
                       "--model", request["model"], "-c", 'model_reasoning_effort="low"',
                       "--output-schema", str(schema), "-"]
            started = time.monotonic()
            try:
                version = run_bounded([str(self.binary), "--version"], timeout=10, env=child_env)
                result = run_bounded(command, timeout=self.timeout, cwd=cwd,
                                     input_text=request["prompt"], stdout_limit=500_000, env=child_env)
            except subprocess.TimeoutExpired:
                return {"status": "provider_timeout", "usage": None}
            except OSError:
                return {"status": "runner_error", "usage": None}
            response = parse_events(result.stdout) if not result.stdout_truncated else {"status": "invalid_trace", "usage": None}
            if result.returncode != 0 and response["status"] == "ok":
                response["status"] = "runner_error"
            response.update(elapsed_ms=round((time.monotonic() - started) * 1000, 3),
                            cli_returncode=result.returncode, cli_version=version.stdout.strip() if version.returncode == 0 else None)
            # Raw stdout has only public fixture evidence and generated messages;
            # do not retain stderr because provider errors may contain auth data.
            response["events"] = result.stdout if not result.stdout_truncated else None
            return response


def prepare_trials(tasks, output: Path, scratch: Path, model: str, repetitions=2,
                   context_budget=3000, output_budget=4000):
    if not 1 <= repetitions <= 10 or not model.strip():
        raise ValueError("Choose an explicit model and 1–10 repetitions.")
    if (output / "manifest.json").exists():
        raise ValueError("Use a fresh output directory; prepared trials are immutable.")
    rows = []
    for repetition in range(1, repetitions + 1):
        # Reverse both orders on alternate repetitions to reduce a simple warm
        # cache/order confound. Repetitions are not independent new tasks.
        ordered_tasks = tasks if repetition % 2 else list(reversed(tasks))
        conditions = CONDITIONS if repetition % 2 else tuple(reversed(CONDITIONS))
        for task in ordered_tasks:
            for condition in conditions:
                with trial_workspace(task, scratch) as root:
                    # Reserve the explicit no-tool/array contract in the same
                    # estimated total allowance for both treatments.
                    from .context import estimate_tokens
                    reserve = estimate_tokens(RESPONSE_INSTRUCTION) + 2
                    request, diagnostics = make_request(task, root, condition, model, context_budget - reserve, output_budget)
                    request["prompt"] += RESPONSE_INSTRUCTION
                    request["trial_id"] += f":r{repetition}"
                    request["protocol"] = PROTOCOL
                    request["temperature"] = None
                    request.pop("max_output_tokens")
                    request["output_tokens_postcheck_limit"] = output_budget
                    request["max_input_estimated_tokens"] = context_budget
                    request["model_identity"] = "requested_cli_model_not_provider_attested"
                    request["settings"] = {"reasoning_effort": "low", "temperature": "CLI default",
                                           "provider_output_cap": "not exposed by CLI",
                                           "config": "ignore-user-config", "sandbox": "read-only"}
                    request.pop("request_hash")
                    request["request_hash"] = fingerprint(request)
                    diagnostics["prompt_estimated_tokens"] = estimate_tokens(request["prompt"])
                    row = {"id": f"{task.id}-{condition}-r{repetition}", "task": task.id,
                           "condition": condition, "repetition": repetition,
                           "request": request, "diagnostics": diagnostics}
                    rows.append(row)
                    write_json(output / "requests" / (row["id"] + ".json"), row)
    manifest = {"protocol": PROTOCOL, "model": model, "task_ids": [t.id for t in tasks],
                "repetitions": repetitions, "conditions": list(CONDITIONS),
                "order": [r["id"] for r in rows], "context_budget_estimated": context_budget,
                "output_budget_postcheck": output_budget, "cost_usd": None,
                "engine_hashes": engine_hashes(), "grader_hashes": {t.id: grader_hash(t) for t in tasks}}
    write_json(output / "manifest.json", manifest)
    return manifest


def run_trials(tasks, output: Path, scratch: Path, runner):
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["protocol"] != PROTOCOL:
        raise ValueError("Unsupported Codex packet protocol.")
    task_map = {task.id: task for task in tasks}
    # Check acceptance and engine provenance before checkpoint reuse as well as
    # new calls. A resumed summary must never mix changed scoring definitions.
    if manifest.get("engine_hashes") != engine_hashes():
        raise ValueError("Engine changed since preparation; use a fresh experiment.")
    if any(task_id not in task_map or manifest["grader_hashes"].get(task_id) != grader_hash(task_map[task_id])
           for task_id in manifest["task_ids"]):
        raise ValueError("Grader changed since preparation; use a fresh experiment.")
    results = []
    for trial_id in manifest["order"]:
        row = json.loads((output / "requests" / (trial_id + ".json")).read_text(encoding="utf-8"))
        request = row["request"]
        digest = request.pop("request_hash")
        if fingerprint(request) != digest:
            raise ValueError("Prepared request changed.")
        request["request_hash"] = digest
        result_path = output / "results" / (trial_id + ".json")
        if result_path.exists():
            record = json.loads(result_path.read_text(encoding="utf-8"))
            if record["request_hash"] != digest:
                raise ValueError("Checkpoint belongs to another request.")
            results.append(record)
            continue
        task = task_map[row["task"]]
        with trial_workspace(task, scratch) as root:
            from .coding import source_hashes
            if source_hashes(root) != request["source_hashes"]:
                raise ValueError("Fixture sources changed since preparation.")
            response = runner(request)
            events = response.pop("events", None)
            if events is not None:
                destination = output / "events" / (trial_id + ".jsonl")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(events, encoding="utf-8")
            outcome = response["status"]
            usage = response.get("usage")
            if outcome == "ok" and usage is not None and usage.get("output_tokens") is not None and usage["output_tokens"] > request["output_tokens_postcheck_limit"]:
                outcome = "output_budget_violation"
            verification = None
            if outcome == "ok":
                try:
                    apply_edits(task, root, response["edits"])
                    verification = grade(task, root)
                    outcome = verification["outcome"]
                except ValueError:
                    outcome = "invalid_candidate"
            record = {"id": trial_id, "task": task.id, "condition": row["condition"],
                      "repetition": row["repetition"], "request_hash": digest,
                      "outcome": outcome, "response": response, "verification": verification,
                      "diagnostics": row["diagnostics"]}
            write_json(result_path, record)
            results.append(record)
            print(f"{trial_id}: {outcome}", flush=True)
    summary = {**manifest, "planned": len(manifest["order"]), "completed": len(results), "conditions_summary": {},
               "label": "Authored fixed-packet CLI experiment; not interactive MCP or independent benchmark"}
    for condition in CONDITIONS:
        selected = [r for r in results if r["condition"] == condition]
        scored = [r for r in selected if r["outcome"] in {"passed", "test_failed", "invalid_candidate", "timeout"}]
        totals = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"):
            values = [r["response"].get("usage", {}).get(key) if r["response"].get("usage") is not None else None for r in selected]
            totals[key] = sum(values) if values and all(v is not None for v in values) else None
        summary["conditions_summary"][condition] = {"trials": len(selected), "scored": len(scored),
            "passed": sum(r["outcome"] == "passed" for r in scored), "usage_totals": totals,
            "outcomes": {value: sum(r["outcome"] == value for r in selected) for value in sorted({r["outcome"] for r in selected})}}
    write_json(output / "summary.json", summary)
    return summary
