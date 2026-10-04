"""Opt-in saved-sign-in Codex trials with actual CLI usage and fixed graders."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diffcontext.coding import load_suite
from diffcontext.codex_trials import CodexPacketRunner, prepare_trials, run_trials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--task", action="append")
    parser.add_argument("--context-budget", type=int, default=3000)
    parser.add_argument("--output-budget", type=int, default=4000,
                        help="Post-generation usage check, not a provider generation cap")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    tasks = load_suite(ROOT / "evals/coding_tasks/suite.json")
    if args.task:
        tasks = [t for t in tasks if t.id in args.task]
        if set(args.task) != {t.id for t in tasks}:
            parser.error("Unknown task requested")
    scratch = ROOT / ".test-tmp/codex-bench"
    if args.action == "prepare":
        if not args.model:
            parser.error("prepare requires an explicit --model")
        result = prepare_trials(tasks, args.output, scratch, args.model, args.repetitions,
                                args.context_budget, args.output_budget)
    else:
        result = run_trials(tasks, args.output, scratch, CodexPacketRunner(timeout=args.timeout))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
