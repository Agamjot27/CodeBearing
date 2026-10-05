"""Development fixtures: bounded investigator vs seed-only at the same text budget."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from codebearing.context import compile_context, estimate_tokens
from codebearing.index import build_index
from codebearing.service import RepositoryService


def main():
    repo = ROOT / "examples" / "refunds"
    index = build_index(repo)
    service = RepositoryService(repo)
    cases = json.loads((ROOT / "evals" / "investigation_cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        run = service.investigate(**case["request"])
        package = run["context"]
        seeds = run["seeds"]["current"]
        budget = run["limits"]["max_tokens"]
        selected = {r["id"] for r in package["included"]} if package else set()
        # Give both policies the same selected seeds, code and maximum text
        # budget. This isolates expansion, not task localization or model quality.
        baseline = compile_context(index, seeds, budget, depth=0) if seeds else None
        basic = {r["id"] for r in baseline["included"]} if baseline else set()
        expected = set(case["expected"])
        missing = sorted(expected - selected)
        actual_tokens = estimate_tokens(package["text"]) if package else 0
        passed = (run["status"] == case["status"] and run["stop_reason"] == case["stop_reason"]
                  and not missing and actual_tokens <= budget
                  and run["usage"]["operations"] <= run["limits"]["max_steps"])
        rows.append({"case": case["name"], "passed": passed, "status": run["status"],
                     "stop_reason": run["stop_reason"], "missing": missing,
                     "investigator_recall": len(selected & expected) / len(expected) if expected else None,
                     "seed_only_recall": len(basic & expected) / len(expected) if expected else None,
                     "estimated_tokens": actual_tokens, "operations": run["usage"]["operations"]})
    print(json.dumps({"label": "Six synthetic development fixtures; same seeds and max text budget. Not held-out coding outcomes or model cost evidence.",
                      "results": rows}, indent=2))
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
