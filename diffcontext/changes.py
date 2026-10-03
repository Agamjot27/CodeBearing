"""Localize tracked commit-to-working-tree changes using both code versions."""

from __future__ import annotations

import difflib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .context import compile_context, estimate_tokens, impact
from .index import Index, MAX_FILE_BYTES, capture_sources, build_index_from_sources, is_source_path


def _git(root: Path, *args: str) -> bytes:
    """Use argument arrays, disable fsmonitor hooks, and bound local Git calls."""
    try:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            capture_output=True, timeout=30,
        )
    except FileNotFoundError as exc:
        raise ValueError("Git must be installed for revision-based analysis.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Git command exceeded 30 seconds.") from exc
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip() or "Git command failed.")
    return result.stdout


def _paths(raw: bytes) -> list[str]:
    return [p.decode("utf-8", errors="surrogateescape") for p in raw.split(b"\0") if p]


@dataclass
class Changes:
    current: Index
    historical: Index
    report: dict


def _mapped(index: Index, path: str, start: int, end: int) -> tuple[list[str], bool]:
    """Map real changed lines, not zero-width deletion anchors, to whole symbols."""
    symbols = [s for s in index.symbols.values() if s.path == path]
    touched = sorted(s.id for s in symbols if start < s.end and end >= s.start)
    # A partially overlapping hunk can include imports/class/global code as well
    # as a function. Keep that ambiguity and conservatively seed the whole file.
    uncovered = any(not any(s.start <= line <= s.end for s in symbols) for line in range(start + 1, end + 1))
    return touched, uncovered


def localize_changes(root: Path, ref: str = "HEAD", *, cache: bool = False) -> Changes:
    root = root.resolve()
    top = Path(_git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
    if top != root:
        raise ValueError("--repo must be the Git repository root for revision analysis.")
    # Resolve once to an immutable commit; a ref beginning with '-' is data, never
    # a Git option. No checkout, temporary worktree, or external diff driver runs.
    commit = _git(root, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").decode().strip()
    entries = _git(root, "ls-tree", "-rlz", "--full-tree", commit)
    old_sources = {}
    historical_warnings = []
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid, size = metadata.split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if not is_source_path(path):
            continue
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            historical_warnings.append(f"Skipped non-regular historical file: {path}")
            continue
        if int(size) > MAX_FILE_BYTES:
            historical_warnings.append(f"Skipped oversized historical file: {path}")
            continue
        old_sources[path] = _git(root, "cat-file", "blob", oid.decode())
    historical = build_index_from_sources(root, old_sources, historical_warnings)
    tracked = set(_paths(_git(root, "ls-files", "--cached", "-z")))
    sources, capture_warnings = capture_sources(root)
    # A staged deletion can leave a file on disk as untracked. Do not resurrect it
    # in the current graph; likewise untracked files are outside this comparison.
    current_sources = {p: raw for p, raw in sources.items() if p in tracked}
    if cache:
        from .index_store import build_cached_sources
        current = build_cached_sources(root, current_sources, capture_warnings)
    else:
        current = build_index_from_sources(root, current_sources, capture_warnings)
    entries = _paths(_git(root, "diff", "--name-status", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", commit, "--"))
    statuses = dict(zip(entries[1::2], entries[::2]))
    untracked = _paths(_git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    current_seeds = set()
    old_seeds = set()
    rows = []
    unresolved = []
    for path, status in statuses.items():
        before = historical.sources.get(path)
        after = current.sources.get(path)
        row = {"path": path, "status": {"A": "added", "D": "deleted", "M": "modified", "T": "type_changed"}.get(status, status), "hunks": [], "fallback": False}
        if not is_source_path(path):
            unresolved.append({"path": path, "reason": "Unsupported source or configuration change; inspect other-language dependencies manually."})
            rows.append(row)
            continue
        if (status != "A" and before is None) or (status != "D" and after is None) or (before is not None and path not in historical.hashes) or (after is not None and path not in current.hashes):
            unresolved.append({"path": path, "reason": "Source missing, skipped, unreadable, or unparseable in one version."})
        # Compare raw lines: Python encoding declarations and non-UTF8 comments
        # preserve their coordinates without an additional decoding policy.
        old_lines = before.splitlines() if before is not None else []
        new_lines = after.splitlines() if after is not None else []
        for tag, a, b, c, d in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            row["hunks"].append({"kind": tag, "old": {"start": a + 1, "count": b - a}, "new": {"start": c + 1, "count": d - c}})
            for index, start, end, destination in [(historical, a, b, old_seeds), (current, c, d, current_seeds)]:
                if start == end:
                    continue
                touched, outside = _mapped(index, path, start, end)
                destination.update(touched)
                if outside:
                    row["fallback"] = True
                    destination.update(s.id for s in index.symbols.values() if s.path == path)
        if row["fallback"]:
            unresolved.append({"path": path, "reason": "Changes outside indexed functions; all file symbols seeded conservatively, module/class context may still be required."})
        if not row["hunks"]:
            row["note"] = "Git reports a change without differing source lines (for example mode or final newline)."
        rows.append(row)
    # Current call resolution cannot find removed callees. Recover old callers
    # and map surviving IDs into the current graph so their present code is shown.
    current_seeds.update(key for key in old_seeds if key in current.symbols)
    current_seeds.update(caller for caller, targets in historical.edges.items() if targets & old_seeds and caller in current.symbols)
    removed = sorted(key for key in old_seeds if key not in current.symbols)
    warnings = list(dict.fromkeys([*current.warnings, *historical.warnings]))
    if untracked:
        warnings.append("Untracked files are excluded; stage new files to include them in revision analysis.")
    warnings.append("Renames are represented as deletion plus addition; semantic rename matching is not implemented.")
    report = {
        "base_ref": ref, "base_commit": commit, "target": "tracked working tree (staged + unstaged changes)",
        "files": rows, "current_seeds": sorted(current_seeds), "historical_seeds": sorted(old_seeds),
        "removed_symbols": removed, "unresolved": unresolved, "excluded_untracked": untracked,
        "warnings": warnings,
        **({"indexing": current.indexing} if current.indexing else {}),
    }
    return Changes(current, historical, report)


def changes_impact(changes: Changes, depth: int = 2) -> dict:
    if not 0 <= depth <= 5:
        raise ValueError("Depth must be between 0 and 5.")
    def expand(index, seeds):
        return impact(index, seeds, depth) if seeds else {"seeds": [], "candidates": [], "warnings": index.warnings}
    return {"changes": changes.report, "current": expand(changes.current, changes.report["current_seeds"]), "historical": expand(changes.historical, changes.report["historical_seeds"])}


def compile_changes(changes: Changes, budget: int = 4000, depth: int = 2, lessons: list[dict] | None = None) -> dict:
    """Pack current and historical evidence under one estimated budget.

    Old excerpts must never masquerade as present code. Current evidence gets
    priority, and omitted historical seeds are reported when the budget runs out.
    """
    if budget < 128:
        raise ValueError("Token budget must be at least 128.")
    if not 0 <= depth <= 5:
        raise ValueError("Depth must be between 0 and 5.")
    text = "CHANGE CONTEXT: historical excerpts are prior code, not current implementation.\n"
    packages = {}
    for label, index, seeds in [
        ("current", changes.current, changes.report["current_seeds"]),
        ("historical", changes.historical, changes.report["historical_seeds"]),
    ]:
        prefix = f"\n=== {label.upper()} EVIDENCE" + (f" at {changes.report['base_commit']}" if label == "historical" else "") + " ===\n"
        remaining = budget - estimate_tokens(text + prefix)
        if not seeds:
            packages[label] = {"included": [], "omitted": [], "missing_seeds": [], "included_lessons": []}
            continue
        if remaining < 128:
            packages[label] = {"included": [], "omitted": [{"id": key, "reason": "shared estimated token budget"} for key in seeds], "missing_seeds": seeds, "included_lessons": []}
            continue
        package = compile_context(index, seeds, remaining, depth, lessons if label == "current" else None)
        text += prefix + package.pop("text")
        packages[label] = package
    return {
        "text": text, "budget": budget, "estimated_tokens": estimate_tokens(text),
        "token_estimator": "ceil(utf8_bytes / 3); actual model token count may differ",
        "changes": changes.report, **packages,
        "complete": not changes.report["unresolved"] and all(not p["omitted"] for p in packages.values()),
        "warnings": list(dict.fromkeys([*changes.report["warnings"], "Static call analysis can miss dependencies; working-tree capture is not atomic."])),
    }
