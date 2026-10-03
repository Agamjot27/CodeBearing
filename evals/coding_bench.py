"""Prepare, run, replay or calibrate synthetic coding-task experiments."""

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from diffcontext.coding import calibrate, load_suite
from diffcontext.experiments import CommandRunner, ReplayRunner, export_requests, run_experiment


class CalibrationRunner:
    kind = "reference_calibration"

    def __init__(self, tasks, reference=True):
        self.tasks = {task.id: task for task in tasks}
        self.reference = reference
        self.identity = "reference" if reference else "unchanged"

    def __call__(self, request):
        task = self.tasks[request["trial_id"].split(":")[0]]
        # Privileged references are consumed only by this explicitly labeled
        # calibration runner, never by prompt preparation or a model adapter.
        edits = json.loads((task.directory / "reference.json").read_text(encoding="utf-8")) if self.reference else {}
        return {"schema_version": 1, "model": request["model"], "request_hash": request["request_hash"],
                "status": "ok", "edits": edits, "usage": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["calibrate", "self-check", "prepare", "run"])
    parser.add_argument("--suite", type=Path, default=ROOT / "evals" / "coding_tasks" / "suite.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--context-budget", type=int, default=4000)
    parser.add_argument("--output-budget", type=int, default=2000)
    parser.add_argument("--runner-timeout", type=float, default=60)
    runner = parser.add_mutually_exclusive_group()
    runner.add_argument("--command-json", help='Argument array, e.g. ["python", "adapter.py"]')
    runner.add_argument("--command-file", type=Path, help="UTF-8 JSON argument array, avoiding native shell quoting")
    runner.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)
    try:
        tasks = load_suite(args.suite)
        scratch = ROOT / ".test-tmp" / "coding-bench"
        if args.action == "calibrate":
            report = calibrate(tasks, scratch)
            passed = report["passed"]
        elif args.action == "self-check":
            output = args.output or ROOT / ".eval-runs" / ("self-check-" + uuid.uuid4().hex)
            calibration = calibrate(tasks, scratch)
            fixed = run_experiment(tasks, output / "reference", scratch, CalibrationRunner(tasks), "calibration:reference")
            unchanged = run_experiment(tasks, output / "unchanged", scratch, CalibrationRunner(tasks, False), "calibration:unchanged")
            memory = [row for row in fixed["trials"] if row["condition"] == "memory"]
            stale = [row for row in fixed["trials"] if row["condition"] == "stale_memory"]
            expected_trials = len(tasks) * 4
            passed = (calibration["passed"] and len(fixed["trials"]) == expected_trials and len(unchanged["trials"]) == expected_trials
                      and all(row["outcome"] == "passed" for row in fixed["trials"])
                      and all(row["outcome"] == "test_failed" for row in unchanged["trials"])
                      and all(row["diagnostics"]["included_lessons"] for row in memory)
                      and all(not row["diagnostics"]["included_lessons"] and any(record["stale"] for record in row["diagnostics"]["excluded_lessons"]) for row in stale))
            report = {"label": "Local harness self-check only; zero model calls and no model improvement claim",
                      "passed": passed, "calibrated_tasks": len(tasks), "reference_trials_passed": sum(row["outcome"] == "passed" for row in fixed["trials"]),
                      "unchanged_trials_failed": sum(row["outcome"] == "test_failed" for row in unchanged["trials"]),
                      "memory_checks": len(memory), "stale_memory_checks": len(stale), "output": str(output)}
        else:
            if args.output is None or not args.model:
                raise ValueError("prepare/run require --output and --model.")
            if args.action == "prepare":
                if args.command_json or args.command_file or args.replay:
                    raise ValueError("prepare does not execute a runner; supply runner options to run.")
                report = export_requests(tasks, args.output, scratch, args.model, args.context_budget, args.output_budget)
                passed = True
            else:
                if not args.command_json and not args.command_file and not args.replay:
                    raise ValueError("run requires --command-file, --command-json or --replay.")
                if args.replay:
                    adapter = ReplayRunner(args.replay)
                else:
                    arguments = args.command_file.read_text(encoding="utf-8-sig") if args.command_file else args.command_json
                    adapter = CommandRunner(json.loads(arguments), args.runner_timeout)
                report = run_experiment(tasks, args.output, scratch, adapter, args.model, args.context_budget, args.output_budget)
                # Exit 0 means the experiment completed, not that every model fix
                # passed. Unscored infrastructure errors make the experiment incomplete.
                passed = report["completed"] == report["planned"] and all(row["outcome"] in {"passed", "test_failed", "timeout", "invalid_candidate"} for row in report["trials"])
        print(json.dumps(report, indent=2))
        return 0 if passed else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"coding-bench: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
