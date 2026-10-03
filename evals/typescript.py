"""Model-free TypeScript retrieval fixture, not a coding-benefit benchmark."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from diffcontext.context import compile_context, estimate_tokens
from diffcontext.index import build_index


def main():
    index = build_index(ROOT / "examples" / "typescript-refunds")
    expected = {"billing.ts:refundTotal", "billing.ts:roundTotal", "checkout.ts:cancelOrder"}
    if not expected <= index.symbols.keys():
        print(json.dumps({"error": "Fixture symbols unavailable; install the typescript extra",
                          "warnings": index.warnings}, indent=2))
        return 1
    results = []
    for budget in (128, 2000):
        packet = compile_context(index, ["billing.ts:refundTotal"], budget=budget, depth=1)
        selected = {row["id"] for row in packet["included"]}
        whole_excerpts = all(index.symbols[key].source in packet["text"] for key in selected)
        results.append({
            "budget": budget,
            "estimated_tokens": estimate_tokens(packet["text"]),
            "expected_recall": len(selected & expected) / len(expected),
            "included": sorted(selected),
            "missing": sorted(expected - selected),
            "whole_excerpts": whole_excerpts,
            "budget_respected": estimate_tokens(packet["text"]) <= budget,
        })
    print(json.dumps({
        "label": "One authored TypeScript fixture, two budgets; no model calls or coding-quality measurement",
        "results": results, "warnings": index.warnings,
    }, indent=2))
    return int(any(not row["whole_excerpts"] or not row["budget_respected"] for row in results)
               or bool(results[-1]["missing"]))


if __name__ == "__main__":
    raise SystemExit(main())
