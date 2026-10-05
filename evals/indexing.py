"""Measured authored indexing workload; no model or production scalability claim."""

import json
import shutil
import statistics
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from codebearing.index import build_index


def fixture(root):
    for number in range(120):
        predecessor = (number - 1) % 120
        source = f"from module_{predecessor:03d} import operation_0 as previous\n\n"
        source += "def operation_0(value):\n    return previous(value) + 1\n\n"
        for function in range(1, 8):
            source += f"def operation_{function}(value):\n    return operation_{function - 1}(value) + {function}\n\n"
        (root / f"module_{number:03d}.py").write_text(source, encoding="utf-8")


def measured(root, cache):
    started = time.perf_counter()
    index = build_index(root, cache=cache)
    return index, round((time.perf_counter() - started) * 1000, 3)


def same_graph(left, right):
    left_description = left.describe()
    right_description = right.describe()
    left_description.pop("indexing", None)
    right_description.pop("indexing", None)
    return left_description == right_description


def main():
    scratch = (ROOT / ".test-tmp").resolve()
    scratch.mkdir(exist_ok=True)
    measurements = []
    warmup = (scratch / f"indexing-warmup-{uuid.uuid4().hex}").resolve()
    if not warmup.is_relative_to(scratch):
        raise RuntimeError("Warmup fixture escaped workspace")
    warmup.mkdir()
    try:
        (warmup / "warmup.py").write_text("def warmup(value):\n    return value + 1\n", encoding="utf-8")
        measured(warmup, False)
        measured(warmup, True)
        measured(warmup, True)
    finally:
        shutil.rmtree(warmup)
    for repetition in range(3):
        root = (scratch / f"indexing-{uuid.uuid4().hex}").resolve()
        if not root.is_relative_to(scratch):
            raise RuntimeError("Benchmark fixture escaped workspace")
        root.mkdir()
        try:
            fixture(root)
            cold, cold_ms = measured(root, True)
            # Alternate paired order to reduce ordering bias. Cold means absent
            # persisted facts, not a flushed operating-system filesystem cache.
            if repetition % 2:
                warm, warm_ms = measured(root, True)
                full, full_ms = measured(root, False)
            else:
                full, full_ms = measured(root, False)
                warm, warm_ms = measured(root, True)
            target = root / "module_060.py"
            target.write_text(target.read_text().replace("previous(value) + 1", "previous(value) + 2"), encoding="utf-8")
            if repetition % 2:
                cached_edit, edit_ms = measured(root, True)
                fresh_edit, full_edit_ms = measured(root, False)
            else:
                fresh_edit, full_edit_ms = measured(root, False)
                cached_edit, edit_ms = measured(root, True)
            measurements.append({
                "repetition": repetition + 1,
                "pair_order": "cache-first" if repetition % 2 else "full-first",
                "full_ms": full_ms, "cold_cache_ms": cold_ms,
                "warm_cache_ms": warm_ms, "full_edit_ms": full_edit_ms,
                "single_edit_cache_ms": edit_ms,
                "cold_counts": cold.indexing, "warm_counts": warm.indexing,
                "edit_counts": cached_edit.indexing,
                "cold_parity": same_graph(full, cold),
                "warm_parity": same_graph(full, warm),
                "edit_parity": same_graph(fresh_edit, cached_edit),
            })
        finally:
            shutil.rmtree(root)
    timing_keys = ("full_ms", "cold_cache_ms", "warm_cache_ms", "full_edit_ms", "single_edit_cache_ms")
    print(json.dumps({
        "label": "120 authored Python files, 960 functions, three repetitions; local wall-clock timings, no production or coding-benefit claim",
        "measurement_scope": "Capture, content hashing, parsing or reuse, global relinking and cache writes; all source files are freshly read",
        "warmup": "Separate one-file parser/cache warmup before repetitions; filesystem/OS caches are not flushed. Cold means absent persisted facts. Full/warm and edit-pair ordering alternates across repetitions",
        "median_ms": {key: statistics.median(row[key] for row in measurements) for key in timing_keys},
        "measurements": measurements,
    }, indent=2))
    # Correctness and parse counts are deterministic gates. Host-specific latency
    # is evidence to inspect, never a fixed CI pass/fail threshold.
    return int(any(not all(row[key] for key in ("cold_parity", "warm_parity", "edit_parity"))
                   or row["warm_counts"]["parsed_files"] != 0
                   or row["edit_counts"]["parsed_files"] != 1
                   for row in measurements))


if __name__ == "__main__":
    raise SystemExit(main())
