"""Deterministic evidence-gathering controller; no model, edits, or test execution."""

from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from pathlib import Path
from typing import Callable

from .changes import compile_changes, localize_changes
from .context import compile_context, impact, search
from .index import Index, build_index, select_symbol
from .retrieval import eligible_lessons, hybrid_search, rank_candidates, select_task_seeds


def _identity(index: Index) -> str:
    # Hash captured bytes, including unparseable sources, rather than rereading
    # disk. This identifies evidence; it is not a commit or an atomic snapshot.
    files = {path: hashlib.sha256(source).hexdigest() for path, source in sorted(index.sources.items())}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def _frontier(index: Index, candidates: list[dict]) -> list[str]:
    selected = {row["id"] for row in candidates}
    adjacent = {target for caller in selected for target in index.edges[caller]}
    adjacent.update(caller for caller, targets in index.edges.items() if targets & selected)
    return sorted(adjacent - selected)


def run(
    root: Path, *, task: str | None = None, symbols: list[str] | None = None,
    ref: str | None = None, max_tokens: int = 4000, max_depth: int = 3,
    max_steps: int = 7, max_seconds: float = 30,
    lesson_reader: Callable[[set[str]], list[dict]] | None = None,
    clock: Callable[[], float] = time.monotonic,
    cache: bool = False,
    retrieval: str = "hybrid",
) -> dict:
    """Locate once, widen depth while observable graph evidence is missing, then stop.

    Time is cooperative: an in-flight filesystem/Git operation cannot be preempted.
    Operation limits count capture, task search, and each compile round, not events.
    """
    if sum(value is not None for value in (task, symbols, ref)) != 1:
        raise ValueError("Supply exactly one of task, symbols or ref.")
    if retrieval not in {"legacy", "hybrid"}:
        raise ValueError("Retrieval must be legacy or hybrid.")
    if task is not None and (not task.strip() or len(task) > 2000):
        raise ValueError("Task must be nonempty and at most 2000 characters.")
    if ref is not None and (not ref.strip() or len(ref) > 2000):
        raise ValueError("Ref must be nonempty and at most 2000 characters.")
    if symbols is not None and (not 1 <= len(symbols) <= 20 or any(not s.strip() or len(s) > 2000 for s in symbols)):
        raise ValueError("Supply 1–20 nonempty symbols, each at most 2000 characters.")
    if not 128 <= max_tokens <= 32000 or not 0 <= max_depth <= 5 or not 2 <= max_steps <= 10:
        raise ValueError("Budget must be 128–32000, depth 0–5, and steps 2–10.")
    if not math.isfinite(max_seconds) or not 0.1 <= max_seconds <= 120:
        raise ValueError("Seconds must be finite and between 0.1 and 120.")

    started = clock()
    operations = 0
    report = {
        "schema_version": 1, "run_id": uuid.uuid4().hex,
        "selector": {"task": task, "symbols": symbols, "ref": ref},
        "limits": {"max_tokens": max_tokens, "max_depth": max_depth,
                   "max_steps": max_steps, "max_seconds": max_seconds, "deadline": "cooperative"},
        "snapshot": {}, "seeds": {"current": [], "historical": []},
        "search_matches": [], "context": None, "verification": {}, "trace": [],
    }

    def event(stage, **data):
        report["trace"].append({"sequence": len(report["trace"]) + 1, "stage": stage,
                                "elapsed_ms": round((clock() - started) * 1000, 3), **data})

    def exhausted():
        if clock() - started >= max_seconds:
            return "time_limit"
        if operations >= max_steps:
            return "step_limit"
        return None

    def finish(status, reason):
        report.update(status=status, stop_reason=reason)
        event("stop", status=status, reason=reason)
        report["usage"] = {"operations": operations, "elapsed_ms": round((clock() - started) * 1000, 3)}
        return report

    reason = exhausted()
    if reason:
        return finish("partial", reason)
    changed = (localize_changes(root, ref, cache=True) if cache else localize_changes(root, ref)) if ref is not None else None
    current = changed.current if changed else (build_index(root, cache=True) if cache else build_index(root))
    historical = changed.historical if changed else None
    operations += 1
    report["snapshot"] = {"current": _identity(current)}
    if historical is not None:
        report["snapshot"].update(historical=_identity(historical), base_commit=changed.report["base_commit"])
    # Capture memory once for this run. A concurrent developer edit must not
    # inject advice from different source bytes into the captured code evidence.
    lessons = lesson_reader(set(current.symbols)) if lesson_reader else []
    for record in lessons:
        record["stale"] = record["stale"] or (
            current.hashes.get(record["evidence"]) != record["evidence_hash"] or
            current.hashes.get(record["scope"].split(":", 1)[0]) != record["scope_hash"]
        )
    event("capture", snapshot=report["snapshot"], symbols=len(current.symbols), warnings=current.warnings)
    if current.indexing:
        report["indexing"] = current.indexing
    reason = exhausted()
    if reason:
        return finish("partial", reason)

    if task is not None:
        matches = hybrid_search(current, task, limit=50, lessons=lessons) if retrieval == "hybrid" else search(current, task, limit=50)
        operations += 1
        report["search_matches"] = matches
        report["retrieval"] = {"policy": retrieval, "scope": "Lexical, static graph and reviewed memory; no embeddings or semantic correctness guarantee."}
        event("locate", method=retrieval, matches=matches)
        reason = exhausted()
        if reason:
            return finish("partial", reason)
        if not matches:
            return finish("needs_input", "no_matches")
        best = [row["id"] for row in matches if row["score"] == matches[0]["score"]]
        if retrieval == "hybrid":
            selection = select_task_seeds(matches)
            report["retrieval"]["seed_selection"] = selection
            event("select", **selection)
            best = [row["id"] for row in selection["selected"]]
            ambiguous = selection["ambiguous"]
        else:
            ambiguous = len(best) > 3
        if ambiguous:
            return finish("needs_input", "ambiguous_matches")
        report["seeds"]["current"] = best
    elif changed is not None:
        report["seeds"] = {"current": changed.report["current_seeds"], "historical": changed.report["historical_seeds"]}
        event("locate", method="revision", seeds=report["seeds"], unresolved=changed.report["unresolved"])
    else:
        report["seeds"]["current"] = sorted({select_symbol(current, seed) for seed in symbols})
        event("locate", method="explicit", seeds=report["seeds"])

    if not any(report["seeds"].values()):
        if changed and (changed.report["unresolved"] or changed.report["excluded_untracked"]):
            report["verification"] = {"unresolved_changes": changed.report["unresolved"],
                                      "excluded_untracked": changed.report["excluded_untracked"]}
            return finish("partial", "unresolved_changes")
        return finish("no_changes", "no_changed_symbols")

    for depth in range(max_depth + 1):
        reason = exhausted()
        if reason:
            return finish("partial", reason)
        graphs = {"current": (current, report["seeds"]["current"])}
        if historical is not None:
            graphs["historical"] = (historical, report["seeds"]["historical"])
        candidates = {version: impact(index, seeds, depth)["candidates"] if seeds else []
                      for version, (index, seeds) in graphs.items()}
        hybrid = task is not None and retrieval == "hybrid"
        if hybrid:
            candidates["current"] = rank_candidates(current, task, report["seeds"]["current"], depth, lessons=lessons)
        scopes = {row["id"] for row in candidates["current"]}
        relevant = [record for record in lessons if record["scope"] in scopes]
        if hybrid:
            valid = eligible_lessons(current, relevant)
            lesson_ids = [lesson_id for row in candidates["current"] for lesson_id in row.get("lesson_ids", [])]
            # Query-matched advice receives first chance at the bounded reserve;
            # remaining fresh scoped lessons may use ordinary leftover space.
            valid.sort(key=lambda r: (r["id"] not in lesson_ids, r["id"]))
            package = compile_context(current, report["seeds"]["current"], max_tokens, depth, valid,
                                      candidates=candidates["current"], lesson_budget=max_tokens // 5,
                                      require_lesson_scope=True)
            package["retrieval"] = {"policy": "hybrid", "lesson_reserve_limit": max_tokens // 5,
                                    "candidates": candidates["current"]}
        else:
            package = compile_changes(changed, max_tokens, depth, relevant) if changed else compile_context(current, report["seeds"]["current"], max_tokens, depth, relevant)
        package["excluded_lessons"] = [{"id": r["id"], "status": r["status"], "stale": r["stale"]}
                                      for r in relevant if r["status"] != "confirmed" or r["stale"]]
        report["context"] = package
        operations += 1
        event("compile", depth=depth, candidates={v: [r["id"] for r in rows] for v, rows in candidates.items()},
              estimated_tokens=package["estimated_tokens"])
        packages = {version: package[version] for version in graphs} if changed else {"current": package}
        frontier = {version: _frontier(index, candidates[version]) for version, (index, _) in graphs.items()}
        verification = {
            "depth": depth, "frontier": frontier,
            "missing_seeds": {v: p["missing_seeds"] for v, p in packages.items()},
            "omitted": {v: p["omitted"] for v, p in packages.items()},
            "unresolved_changes": changed.report["unresolved"] if changed else [],
            "excluded_untracked": changed.report["excluded_untracked"] if changed else [],
            "index_warnings": list(dict.fromkeys(w for index, _ in graphs.values() for w in index.warnings)),
            "scope": "Static graph coverage for selected seeds; not semantic task correctness.",
        }
        report["verification"] = verification
        event("verify", **verification)
        # Never deepen a package that already omits required evidence: more
        # candidates cannot repair packing under the same fixed token budget.
        if clock() - started >= max_seconds:
            return finish("partial", "time_limit")
        if any(p["omitted"] or p["missing_seeds"] for p in packages.values()):
            return finish("partial", "token_budget")
        # Localization/parser gaps cannot be repaired by graph traversal, but
        # do not discard reachable evidence. Finish widening before flagging them.
        if not any(frontier.values()) or depth == max_depth:
            if verification["unresolved_changes"] or verification["excluded_untracked"]:
                return finish("partial", "unresolved_changes")
            if verification["index_warnings"]:
                return finish("partial", "index_warnings")
        if not any(frontier.values()):
            return finish("ready", "graph_covered")
        if depth == max_depth:
            return finish("partial", "depth_limit")
        event("expand", next_depth=depth + 1, reason="Unexplored static callers/callees", frontier=frontier)

    raise AssertionError("Investigation must terminate within its configured depth.")
