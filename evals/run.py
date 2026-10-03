"""Small deterministic smoke evaluation. Not evidence of general task success."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from diffcontext.context import compile_context, search
from diffcontext.index import build_index


def main():
    index = build_index(ROOT / "examples" / "refunds")
    cases = json.loads((ROOT / "evals" / "cases.json").read_text())
    results = []
    for case in cases:
        expected = set(case["expected"])
        context = compile_context(index, [case["seed"]], budget=4000)
        graph = {r["id"] for r in context["included"]} - {case["seed"]}
        lexical = {r["id"] for r in search(index, case["seed"].split(":")[1], limit=20)} - {case["seed"]}
        results.append({
            "case": case["name"],
            "graph_recall": len(graph & expected) / len(expected),
            "lexical_recall": len(lexical & expected) / len(expected),
            "missing": sorted(expected - graph),
            "estimated_tokens": context["estimated_tokens"],
        })
    print(json.dumps({"label": "Synthetic smoke fixture, 2 cases; not an independent benchmark or equal-budget comparison", "results": results}, indent=2))
    return 1 if any(r["missing"] for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
