"""Deterministic code-aware lexical, reviewed-memory, and bounded-graph ranking.

Weights are explicit initial engineering defaults, not benchmark-tuned values.
This module never reads repository files, calls a model, or expands a graph beyond
``context.impact``. Legacy ``context.search`` remains available for comparisons.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import math
import re

from .index import Index

NAME_WEIGHT = 3.0
PATH_WEIGHT = 1.5
BODY_WEIGHT = 1.0
K1 = 1.2
B = 0.75
EXACT_SCORE = 100.0
MEMORY_SEARCH_WEIGHT = 0.25
LEXICAL_RANK_WEIGHT = 0.60
GRAPH_RANK_WEIGHT = 0.30
MEMORY_RANK_WEIGHT = 0.10

STOPWORDS = frozenset("""
a an and are as at be been being by can could did do does for from had has have
how i in into is it its of on or our should so than that the their them then there
these they this those to was we were what when where which who why will with would
you your please fix bug change implement update code function def class const let
var return import export default async await self true false none null undefined
""".split())
WORDS = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+")


def _variants(term: str) -> set[str]:
    """Conservative suffix variants, retaining the original identifier as well."""
    result = {term}
    if len(term) > 5 and term.endswith("ing"):
        result.add(term[:-3])
    if len(term) > 4 and term.endswith("ies"):
        result.add(term[:-3] + "y")
    elif len(term) > 3 and term.endswith("s") and not term.endswith(("ss", "us", "is")):
        result.add(term[:-1])
    return {token for token in result if token and token not in STOPWORDS and not token.isdigit()}


def _tokens(text: str) -> list[str]:
    """Keep full snake/camel identifiers and their useful word-level components."""
    tokens = []
    for word in WORDS.findall(text):
        parts = {word.lower()}
        for piece in word.split("_"):
            parts.update(part.lower() for part in CAMEL.findall(piece))
        variants = set()
        for part in parts:
            variants.update(_variants(part))
        tokens.extend(sorted(variants))
    return tokens


def _bm25(documents: dict, terms: set[str]) -> dict:
    """Standard BM25: k1=1.2, b=.75; saturation limits repeated-token influence."""
    frequencies = {key: Counter(tokens) for key, tokens in documents.items()}
    count = len(frequencies)
    if not count or not terms:
        return {key: 0.0 for key in frequencies}
    average = sum(sum(freq.values()) for freq in frequencies.values()) / count
    document_frequency = Counter(term for freq in frequencies.values() for term in terms if term in freq)
    scores = {}
    for key, freq in frequencies.items():
        length = sum(freq.values())
        score = 0.0
        for term in sorted(terms):
            tf = freq.get(term, 0)
            if not tf:
                continue
            df = document_frequency[term]
            idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
            norm = K1 * (1 - B + B * length / average) if average else K1
            score += idf * tf * (K1 + 1) / (tf + norm)
        scores[key] = score
    return scores


def _validate_limit(limit):
    if type(limit) is not int or limit < 1:
        raise ValueError("Search limit must be a positive integer.")


def _lexical_rows(index: Index, query: str) -> list[dict]:
    terms = set(_tokens(query))
    fields = {
        "name": {key: _tokens(symbol.name) for key, symbol in index.symbols.items()},
        "path": {key: _tokens(symbol.path) for key, symbol in index.symbols.items()},
        "body": {key: _tokens(symbol.source) for key, symbol in index.symbols.items()},
    }
    field_scores = {field: _bm25(documents, terms) for field, documents in fields.items()}
    exact_query = query.strip().casefold()
    rows = []
    for key, symbol in index.symbols.items():
        exact = bool(exact_query) and exact_query in {key.casefold(), symbol.name.casefold()}
        score = (NAME_WEIGHT * field_scores["name"][key] + PATH_WEIGHT * field_scores["path"][key]
                 + BODY_WEIGHT * field_scores["body"][key])
        if not score and not exact:
            continue
        matches = {field: sorted(terms & set(documents[key])) for field, documents in fields.items()}
        # All identical explicit names tie, regardless of path or body length.
        # Exactness also has a separate sort key, so long natural queries can
        # never overcome a user's explicit symbol selection.
        score = EXACT_SCORE if exact else score
        signals = {"exact": exact, "lexical": score, "memory": 0.0, "lesson_ids": [],
                   "matched_terms": matches,
                   "field_scores": {field: field_scores[field][key] for field in fields}}
        reasons = ["exact symbol name or ID"] if exact else []
        reasons += [f"BM25 {field} matches: {', '.join(values)}" for field, values in matches.items() if values]
        rows.append({"id": key, "score": score, "reasons": reasons, "signals": signals})
    return sorted(rows, key=lambda row: (not row["signals"]["exact"], -row["score"], row["id"]))


def lexical_search(index: Index, query: str, limit: int = 10) -> list[dict]:
    """Rank name/path/body BM25 with weights 3/1.5/1 and exact-name priority.

    Identifier splitting and conservative suffix variants support natural tasks.
    Exact queries preserve ambiguity: equal-name symbols receive identical scores.
    Scores are ranking heuristics, not confidence or probability estimates.
    """
    _validate_limit(limit)
    return _lexical_rows(index, query)[:limit]


def eligible_lessons(index: Index, lessons: list[dict] | None) -> list[dict]:
    """Validate review status and hashes against captured bytes, without disk reads.

    A caller-supplied ``stale=False`` flag alone is insufficient: both scope and
    evidence must remain successfully indexed and match the lesson's saved hashes.
    Missing/malformed evidence is excluded rather than treated as trusted memory.
    """
    valid = []
    for lesson in lessons or []:
        if not isinstance(lesson, dict):
            continue
        scope, evidence = lesson.get("scope"), lesson.get("evidence")
        if (lesson.get("status") != "confirmed" or lesson.get("stale") is not False
                or not isinstance(scope, str) or scope not in index.symbols
                or not isinstance(evidence, str) or type(lesson.get("id")) is not int
                or not isinstance(lesson.get("lesson"), str) or not lesson["lesson"].strip()):
            continue
        scope_path = index.symbols[scope].path
        if any(path not in index.hashes or path not in index.sources for path in (scope_path, evidence)):
            continue
        pairs = ((scope_path, lesson.get("scope_hash")), (evidence, lesson.get("evidence_hash")))
        if any(not expected or index.hashes[path] != expected
               or hashlib.sha256(index.sources[path]).hexdigest() != expected for path, expected in pairs):
            continue
        valid.append(lesson)
    return sorted(valid, key=lambda lesson: (lesson["id"], lesson["scope"], lesson["lesson"]))


def _memory_signals(index: Index, query: str, lessons: list[dict] | None) -> dict:
    valid = eligible_lessons(index, lessons)
    scores = _bm25({position: _tokens(lesson["lesson"]) for position, lesson in enumerate(valid)}, set(_tokens(query)))
    maximum = max(scores.values(), default=0.0)
    signals = {}
    for position, lesson in enumerate(valid):
        raw = scores[position]
        if not raw:
            continue
        row = signals.setdefault(lesson["scope"], {"memory": 0.0, "lesson_ids": []})
        # Repeated lessons cannot buy rank: use the strongest relevant lesson,
        # capped at one, while retaining every matched ID for trace inspection.
        row["memory"] = max(row["memory"], raw / maximum)
        row["lesson_ids"].append(lesson["id"])
    for row in signals.values():
        row["lesson_ids"] = sorted(set(row["lesson_ids"]))
    return signals


def hybrid_search(index: Index, query: str, limit: int = 10, lessons: list[dict] | None = None) -> list[dict]:
    """Blend normalized lexical score + .25 * normalized reviewed-memory score.

    Memory can introduce a valid scope with opaque code names, but contributes at
    most .25 and cannot break explicit-name ties. No embedding/provider is used.
    """
    _validate_limit(limit)
    lexical = _lexical_rows(index, query)
    maximum = max((row["score"] for row in lexical if not row["signals"]["exact"]), default=0.0)
    rows = {row["id"]: row for row in lexical}
    memory = _memory_signals(index, query, lessons)
    for scope in memory:
        rows.setdefault(scope, {"id": scope, "score": 0.0, "reasons": [],
                                "signals": {"exact": False, "lexical": 0.0, "memory": 0.0,
                                            "lesson_ids": [], "matched_terms": {"name": [], "path": [], "body": []},
                                            "field_scores": {"name": 0.0, "path": 0.0, "body": 0.0}}})
    for key, row in rows.items():
        signal = memory.get(key, {"memory": 0.0, "lesson_ids": []})
        row["signals"].update(signal)
        normalized = row["signals"]["lexical"] / maximum if maximum else 0.0
        row["signals"]["lexical_normalized"] = min(normalized, 1.0)
        row["score"] = EXACT_SCORE if row["signals"]["exact"] else normalized + MEMORY_SEARCH_WEIGHT * signal["memory"]
        if signal["lesson_ids"]:
            row["reasons"].append(f"reviewed memory matches lessons: {', '.join(map(str, signal['lesson_ids']))}")
    return sorted(rows.values(), key=lambda row: (not row["signals"]["exact"], -row["score"], row["id"]))[:limit]


def rank_candidates(index: Index, query: str, seeds: list[str], depth: int, lessons: list[dict] | None = None) -> list[dict]:
    """Rank only bounded impact candidates: .60 lexical + .30 graph + .10 memory.

    Seeds always precede nonseeds. Graph signal is 1/(distance+1); lexical and
    memory are normalized to [0,1]. Weights are initial defaults, not eval tuning.
    No unrelated symbol or lesson scope is injected into the graph candidate pool.
    """
    # Context compilation also consumes this ranker; defer the graph import so
    # both modules can expose their public functions without an import cycle.
    from .context import impact
    pool = impact(index, seeds, depth)["candidates"]
    lexical = {row["id"]: row for row in _lexical_rows(index, query)}
    maximum = max((lexical[row["id"]]["score"] for row in pool if row["id"] in lexical), default=0.0)
    memory = _memory_signals(index, query, lessons)
    ranked = []
    for candidate in pool:
        key = candidate["id"]
        source = lexical.get(key)
        raw = source["score"] if source else 0.0
        normalized = raw / maximum if maximum else 0.0
        graph = 1 / (candidate["distance"] + 1)
        signal = memory.get(key, {"memory": 0.0, "lesson_ids": []})
        exact = source["signals"]["exact"] if source else False
        score = LEXICAL_RANK_WEIGHT * normalized + GRAPH_RANK_WEIGHT * graph + MEMORY_RANK_WEIGHT * signal["memory"]
        reasons = list(candidate["reasons"])
        if source:
            reasons.extend(source["reasons"])
        if signal["lesson_ids"]:
            reasons.append(f"reviewed memory matches lessons: {', '.join(map(str, signal['lesson_ids']))}")
        ranked.append({**candidate, "reasons": reasons, "score": score, "lesson_ids": signal["lesson_ids"],
                       "signals": {"exact": exact, "lexical": raw, "lexical_normalized": normalized,
                                   "graph": graph, **signal}})
    # Exact matches stay tied regardless of optional memory; seeds still lead.
    return sorted(ranked, key=lambda row: (row["distance"] != 0, not row["signals"]["exact"],
                                          -EXACT_SCORE if row["signals"]["exact"] else -row["score"], row["id"]))
