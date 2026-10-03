"""Human-readable metadata views of inline or explicitly saved investigation runs."""

import json
from pathlib import Path

MAX_RUN_BYTES = 10_000_000


def summarize(report: dict) -> dict:
    """Keep evidence citations, decisions and gaps; omit the source text itself."""
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("Expected a full DiffContext investigation report with schema_version 1.")
    try:
        if report["status"] not in {"ready", "partial", "needs_input", "no_changes"}:
            raise ValueError("Invalid investigation status.")
        package = report["context"]
        versions = {v: package[v] for v in ("current", "historical")} if package and "changes" in package else {"current": package} if package else {}
        return {
            "run_id": report["run_id"], "status": report["status"], "stop_reason": report["stop_reason"],
            "selector": report["selector"], "search_matches": report["search_matches"],
            "seeds": report["seeds"], "snapshot": report["snapshot"], "limits": report["limits"],
            "usage": report["usage"], "estimated_tokens": package["estimated_tokens"] if package else 0,
            **({"indexing": report["indexing"]} if "indexing" in report else {}),
            "evidence": {version: [{key: row[key] for key in ("id", "path", "start", "end", "reasons")}
                                    for row in data["included"]] for version, data in versions.items()},
            "included_lessons": {version: data["included_lessons"] for version, data in versions.items()},
            "excluded_lessons": package.get("excluded_lessons", []) if package else [],
            "verification": report["verification"],
            "warnings": list(dict.fromkeys([*(package.get("warnings", []) if package else []),
                         *(warning for event in report["trace"] if event["stage"] == "capture" for warning in event.get("warnings", []))])),
            "trace": [{key: event[key] for key in ("sequence", "stage", "elapsed_ms", "depth", "next_depth", "reason", "status") if key in event}
                      for event in report["trace"]],
        }
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed investigation report; save the full JSON, not --summary output.") from exc


def load_summary(path: Path) -> dict:
    # Saved files are explicit caller input, not a server run database. Bound
    # reads before decoding so a huge/corrupt file cannot consume unlimited memory.
    with path.open("rb") as stream:
        data = stream.read(MAX_RUN_BYTES + 1)
    if len(data) > MAX_RUN_BYTES:
        raise ValueError("Saved run exceeds the 10 MB inspection limit.")
    try:
        report = json.loads(data.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Saved run must be a full JSON report encoded as UTF-8.") from exc
    return summarize(report)
