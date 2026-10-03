"""Authored paired retrieval cases; not held-out evaluation or model outcomes."""

import json
import shutil
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from diffcontext.context import compile_context, estimate_tokens, search
from diffcontext.index import build_index
from diffcontext.memory import Memory


def fixture(root):
    sources = {
        "billing.py": "def round_line(amount):\n    return round(amount, 2)\n\ndef refund_total(amounts):\n    return sum(round_line(amount) for amount in amounts)\n",
        "checkout.py": "from billing import refund_total as calculate\n\ndef cancel_order(items):\n    return calculate(items)\n",
        "ledger.py": "def reconcileBalance(amount):\n    return amount\n",
        "a_noise.py": "def refund_documentation():\n    text = 'refund total refund total refund total refund total'\n    return text\n",
        "evidence.py": "def check_rounding():\n    return True\n",
    }
    for name, text in sources.items():
        (root / name).write_text(text, encoding="utf-8")
    store = Memory(root)
    try:
        lesson = store.add(build_index(root), "billing.py:refund_total",
                           "Chargeback settlement requires final rounding", "evidence.py")
        store.set_status(lesson, "confirmed")
        return lesson
    finally:
        store.close()


def seeds(matches):
    if not matches:
        return []
    best = [row["id"] for row in matches if row["score"] == matches[0]["score"]]
    return best if len(best) <= 3 else []


def metrics(packet, matches, expected, elapsed_ms, eligible_lessons):
    selected = {row["id"] for row in packet["included"]} if packet else set()
    first_relevant = next((number for number, row in enumerate(matches, 1) if row["id"] in expected), None)
    return {
        "recall": len(selected & expected) / len(expected) if expected else None,
        "precision": len(selected & expected) / len(selected) if selected else None,
        "reciprocal_rank": (1 / first_relevant if first_relevant else 0) if expected else None,
        "included": sorted(selected), "missing": sorted(expected - selected),
        "unexpected": sorted(selected - expected), "latency_ms": elapsed_ms,
        "estimated_tokens": estimate_tokens(packet["text"]) if packet else 0,
        "budget_respected": packet is None or estimate_tokens(packet["text"]) <= packet["budget"],
        "included_lessons": packet["included_lessons"] if packet else [],
        "eligible_memory_only": packet is None or set(packet["included_lessons"]) <= eligible_lessons,
        "lesson_scope_present": packet is None or not packet["included_lessons"] or "billing.py:refund_total" in selected,
    }


def main():
    from diffcontext.retrieval import hybrid_search, rank_candidates, eligible_lessons

    scratch = (ROOT / ".test-tmp").resolve()
    scratch.mkdir(exist_ok=True)
    root = (scratch / f"hybrid-{uuid.uuid4().hex}").resolve()
    if not root.is_relative_to(scratch):
        raise RuntimeError("Retrieval fixture escaped workspace")
    root.mkdir()
    results = []
    try:
        lesson_id = fixture(root)
        cases = [
            ("identifier-snake", "refund total", {"billing.py:refund_total", "billing.py:round_line", "checkout.py:cancel_order"}, 1500, False),
            ("identifier-camel", "reconcile balance", {"ledger.py:reconcileBalance"}, 1000, False),
            ("legacy-exact-with-distractor", "refund_total", {"billing.py:refund_total", "billing.py:round_line", "checkout.py:cancel_order"}, 1500, False),
            ("distractor-tight-budget", "refund", {"billing.py:refund_total", "billing.py:round_line", "checkout.py:cancel_order"}, 250, False),
            ("no-match", "xyzzynonexistent", set(), 1000, False),
            ("memory-fresh", "chargeback settlement", {"billing.py:refund_total"}, 1000, False),
            ("memory-stale", "chargeback settlement", set(), 1000, True),
        ]
        for name, task, expected, budget, make_stale in cases:
            if make_stale:
                (root / "evidence.py").write_text("def check_rounding():\n    return False\n", encoding="utf-8")
            index = build_index(root)
            store = Memory(root, read_only=True)
            try:
                lessons = store.list()
            finally:
                store.close()
            eligible = {record["id"] for record in lessons if record["status"] == "confirmed" and not record["stale"]}
            started = time.perf_counter()
            legacy_matches = search(index, task, 50)
            legacy_seeds = seeds(legacy_matches)
            legacy_packet = compile_context(index, legacy_seeds, budget, 1, lessons) if legacy_seeds else None
            legacy_ms = round((time.perf_counter() - started) * 1000, 3)
            started = time.perf_counter()
            hybrid_matches = hybrid_search(index, task, 50, lessons)
            hybrid_seeds = seeds(hybrid_matches)
            hybrid_packet = None
            if hybrid_seeds:
                candidates = rank_candidates(index, task, hybrid_seeds, 1, lessons)
                scopes = {row["id"] for row in candidates}
                valid = eligible_lessons(index, [record for record in lessons if record["scope"] in scopes])
                matched_ids = [lesson_id for row in candidates for lesson_id in row.get("lesson_ids", [])]
                valid.sort(key=lambda record: (record["id"] not in matched_ids, record["id"]))
                hybrid_packet = compile_context(index, hybrid_seeds, budget, 1, valid,
                    candidates=candidates, lesson_budget=budget // 5, require_lesson_scope=True)
            hybrid_ms = round((time.perf_counter() - started) * 1000, 3)
            old = metrics(legacy_packet, legacy_matches, expected, legacy_ms, eligible)
            new = metrics(hybrid_packet, hybrid_matches, expected, hybrid_ms, eligible)
            results.append({"case": name, "task": task, "budget": budget, "depth": 1,
                            "expected": sorted(expected), "legacy": old, "hybrid": new,
                            "recall_regression": bool(expected and new["recall"] < old["recall"]),
                            "memory_fixture_id": lesson_id})
    finally:
        shutil.rmtree(root)
    print(json.dumps({
        "label": "Seven authored development cases, same captured index/task/budget/depth per pair; no held-out, embedding or model-quality claim",
        "metric_scope": "Recall/precision apply to compiled code IDs; MRR to localization rank over five nonempty relevance sets. Empty relevance sets have no reciprocal rank and are checked for abstention separately. Latency is one local retrieval call, excluding index/memory capture; fixed legacy-first order, no repeats",
        "aggregate": {
            "cases": len(results),
            "ranked_cases": sum(bool(row["expected"]) for row in results),
            "recall_regressions": [row["case"] for row in results if row["recall_regression"]],
            "legacy_mrr": sum(row["legacy"]["reciprocal_rank"] for row in results if row["expected"]) / sum(bool(row["expected"]) for row in results),
            "hybrid_mrr": sum(row["hybrid"]["reciprocal_rank"] for row in results if row["expected"]) / sum(bool(row["expected"]) for row in results),
        },
        "results": results,
    }, indent=2))
    return int(any(not row[policy]["budget_respected"] or not row[policy]["eligible_memory_only"]
                   or (policy == "hybrid" and not row[policy]["lesson_scope_present"])
                   or (row["case"] in {"no-match", "memory-stale"} and bool(row[policy]["included"]))
                   for row in results for policy in ("legacy", "hybrid")))


if __name__ == "__main__":
    raise SystemExit(main())
