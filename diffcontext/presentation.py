"""MCP-only diagnostic compaction; core reports and cited evidence stay intact."""

from __future__ import annotations

from copy import deepcopy
from typing import Literal

Detail = Literal["compact", "full"]
WARNING_LIMIT = 8
_LIMITATION_PREFIXES = (
    "Static ", "TypeScript/JavaScript ", "Untracked files ", "Renames are ",
)


def present_report(report: dict, detail: Detail = "compact") -> dict:
    """Bound warning examples and reference repeated trace data without changing evidence.

    Full detail returns the service report as-is. Compact detail works on a copy:
    source text, selected citations, status and all observable coverage gaps are
    unchanged. Counts disclose every sampled warning array; full detail recomputes
    a fresh report rather than retrieving a persisted snapshot.
    """
    if detail == "full":
        return report
    if detail != "compact":
        raise ValueError("Detail must be compact or full.")
    result = deepcopy(report)
    fields = []

    def sample(value, path):
        if not isinstance(value, list) or len(value) <= WARNING_LIMIT:
            return value
        # General capability caveats can occur after hundreds of per-call warnings.
        # Reserve space for them so sampling never implies broader graph coverage.
        caveats = [row for row in value if isinstance(row, str) and row.startswith(_LIMITATION_PREFIXES)]
        ordered = list(dict.fromkeys([*caveats, *value]))
        shown = ordered[:WARNING_LIMIT]
        fields.append({"path": path, "total": len(value), "shown": len(shown),
                       "omitted": len(value) - len(shown), "kind": "warning_sample"})
        return shown

    def walk(value, path=""):
        if isinstance(value, dict):
            for key, child in list(value.items()):
                child_path = f"{path}.{key}" if path else key
                value[key] = sample(child, child_path) if key in {"warnings", "index_warnings"} else walk(child, child_path)
        elif isinstance(value, list):
            for position, child in enumerate(value):
                value[position] = walk(child, f"{path}[{position}]")
        return value

    # Trace repeats localization and verification data already available at the
    # report root. Only exact matches become references: earlier, different gaps
    # remain visible. Do this before warning sampling to compare the full evidence.
    for position, event in enumerate(result.get("trace", [])):
        if not isinstance(event, dict):
            continue
        references = {"matches": ("search_matches", report.get("search_matches")),
                      "snapshot": ("snapshot", report.get("snapshot"))}
        if event.get("stage") == "verify":
            references.update({key: (f"verification.{key}", value)
                               for key, value in report.get("verification", {}).items()})
        for key, (target, canonical) in references.items():
            if key in event and canonical is not None and event[key] == canonical:
                original = event.pop(key)
                event[f"{key}_reference"] = target
                fields.append({"path": f"trace[{position}].{key}", "kind": "duplicate_reference",
                               "reference": target, "items": len(original) if isinstance(original, (list, dict)) else 1})
    walk(result)
    result["presentation"] = {
        "detail": "compact", "warning_limit": WARNING_LIMIT, "fields": fields,
        "full_detail": "Repeat this tool with the same arguments and detail='full' for complete diagnostics. The repeat reads fresh repository evidence, not this snapshot.",
        "scope": "Only diagnostic warning examples and exact repeated trace data are compacted. Source text and coverage gaps are unchanged; total response size is not token-budgeted.",
    }
    # Some hosts clip their displayed JSON before the model/user reaches late
    # fields. Put actionable evidence and coverage gaps ahead of verbose search
    # scoring and trace data; this changes ordering, never selected content.
    priority = ("schema_version", "status", "stop_reason", "run_id", "text", "context",
                "verification", "complete", "budget", "estimated_tokens", "missing_seeds",
                "omitted", "presentation")
    return {key: result[key] for key in (*priority, *(key for key in result if key not in priority))
            if key in result}
