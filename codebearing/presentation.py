"""MCP-only diagnostic compaction; core reports and cited evidence stay intact."""

from __future__ import annotations

from copy import deepcopy
from typing import Literal

Detail = Literal["compact", "full"]
WARNING_LIMIT = 8
RANKING_ITEM_LIMIT = 8
RANKING_REASON_CHAR_LIMIT = 160
RANKING_TERM_CHAR_LIMIT = 80
_LIMITATION_PREFIXES = (
    "Static ", "TypeScript/JavaScript ", "Untracked files ", "Renames are ",
)


def present_report(report: dict, detail: Detail = "compact") -> dict:
    """Bound diagnostics and reference repeated trace data without changing evidence.

    Full detail returns the service report as-is. Compact detail works on a copy:
    source text, selected citations, status and all observable coverage gaps are
    unchanged. Counts disclose sampled warnings and ranking explanations; full detail recomputes
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

    def ranking_diagnostics(rows, path):
        """Trim explanations, never ranked identities or numeric retrieval signals.

        Ranking reasons repeat matched terms and may dwarf selected code. Exact
        counts disclose list sampling and string truncation independently. Scope
        this to ranking rows: source/omission explanations are evidence contracts.
        """
        if not isinstance(rows, list):
            return
        for position, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            row_path = f"{path}[{position}]"

            def bound(items, field_path, char_limit):
                if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                    return items
                shown = [item[:char_limit] for item in items[:RANKING_ITEM_LIMIT]]
                if shown != items:
                    total_chars = sum(map(len, items))
                    shown_chars = sum(map(len, shown))
                    fields.append({"path": field_path, "kind": "ranking_diagnostic_sample",
                                   "total": len(items), "shown": len(shown),
                                   "omitted": len(items) - len(shown),
                                   "total_chars": total_chars, "shown_chars": shown_chars,
                                   "omitted_chars": total_chars - shown_chars,
                                   "item_char_limit": char_limit})
                return shown

            if "reasons" in row:
                row["reasons"] = bound(row["reasons"], f"{row_path}.reasons", RANKING_REASON_CHAR_LIMIT)
            signals = row.get("signals")
            terms = signals.get("matched_terms") if isinstance(signals, dict) else None
            if isinstance(terms, dict):
                for field, items in terms.items():
                    terms[field] = bound(items, f"{row_path}.signals.matched_terms.{field}",
                                         RANKING_TERM_CHAR_LIMIT)

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
        # Different localization snapshots remain present; bound only their
        # scoring explanations using the same policy as canonical search rows.
        ranking_diagnostics(event.get("matches"), f"trace[{position}].matches")
    ranking_diagnostics(result.get("search_matches"), "search_matches")
    ranking_diagnostics(result.get("matches"), "matches")
    # Investigation may stop before compiling any context (no matches, unchanged
    # diff, exhausted time). Preserve its null context and original stop reason.
    context = result.get("context")
    retrieval = context.get("retrieval") if isinstance(context, dict) else None
    if isinstance(retrieval, dict):
        ranking_diagnostics(retrieval.get("candidates"), "context.retrieval.candidates")
    walk(result)
    result["presentation"] = {
        "detail": "compact", "warning_limit": WARNING_LIMIT, "fields": fields,
        "ranking_item_limit": RANKING_ITEM_LIMIT,
        "ranking_reason_char_limit": RANKING_REASON_CHAR_LIMIT,
        "ranking_term_char_limit": RANKING_TERM_CHAR_LIMIT,
        "full_detail": "Repeat this tool with the same arguments and detail='full' for complete diagnostics. The repeat reads fresh repository evidence, not this snapshot.",
        "scope": "Diagnostic warning examples, ranking reasons/matched terms and exact repeated trace data are compacted with counts/references. Ranking identities/order/scores/lesson IDs, source text and coverage gaps are unchanged; total response size is not token-budgeted.",
    }
    # Some hosts clip their displayed JSON before the model/user reaches late
    # fields. Put actionable evidence and coverage gaps ahead of verbose search
    # scoring and trace data; this changes ordering, never selected content.
    priority = ("schema_version", "status", "stop_reason", "run_id", "text", "context",
                "verification", "complete", "budget", "estimated_tokens", "missing_seeds",
                "omitted", "presentation")
    return {key: result[key] for key in (*priority, *(key for key in result if key not in priority))
            if key in result}
