"""Repository-bound orchestration shared by CLI and agent interfaces."""

from pathlib import Path

from . import changes
from . import investigation
from .context import compile_context, impact, search
from .index import build_index, select_symbol
from .memory import Memory


class RepositoryService:
    """Read fresh code per request; transport adapters never implement retrieval."""

    def __init__(self, root: Path, *, cache: bool = False):
        self.root = root.resolve()
        self.cache = cache
        if not self.root.is_dir():
            raise ValueError(f"Repository directory does not exist: {self.root}")

    def _index(self):
        return build_index(self.root, cache=True) if self.cache else build_index(self.root)

    def _changes(self, ref):
        return changes.localize_changes(self.root, ref, cache=True) if self.cache else changes.localize_changes(self.root, ref)

    @staticmethod
    def _validate(symbols, ref, depth):
        if not 0 <= depth <= 5:
            raise ValueError("Depth must be between 0 and 5.")
        if (symbols is None) == (ref is None):
            raise ValueError("Supply exactly one of symbols or ref.")
        if symbols is not None and (not 1 <= len(symbols) <= 20 or any(not s.strip() or len(s) > 2000 for s in symbols)):
            raise ValueError("Supply 1–20 nonempty symbols, each at most 2000 characters.")
        if ref is not None and (not ref.strip() or len(ref) > 2000):
            raise ValueError("Ref must be nonempty and at most 2000 characters.")

    def _lessons(self, scopes: set[str]) -> list[dict]:
        if not scopes or not (self.root / ".diffcontext" / "memory.sqlite3").exists():
            return []
        store = Memory(self.root, read_only=True)
        try:
            return store.list(scopes)
        finally:
            store.close()

    def search_symbols(self, query: str, limit: int = 10) -> dict:
        if not query.strip() or len(query) > 2000:
            raise ValueError("Query must be nonempty and at most 2000 characters.")
        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50.")
        index = self._index()
        return {"matches": search(index, query, limit), "warnings": index.warnings,
                **({"indexing": index.indexing} if index.indexing else {})}

    def localize_changes(self, ref: str = "HEAD") -> dict:
        self._validate(None, ref, 2)
        return self._changes(ref).report

    def analyze_impact(self, symbols: list[str] | None = None, ref: str | None = None, depth: int = 2) -> dict:
        self._validate(symbols, ref, depth)
        if ref is not None:
            return changes.changes_impact(self._changes(ref), depth)
        index = self._index()
        result = impact(index, symbols, depth)
        if index.indexing:
            result["indexing"] = index.indexing
        return result

    def compile_context(self, symbols: list[str] | None = None, ref: str | None = None, max_tokens: int = 4000, depth: int = 2) -> dict:
        self._validate(symbols, ref, depth)
        if not 128 <= max_tokens <= 32000:
            raise ValueError("Token budget must be between 128 and 32000.")
        changed = self._changes(ref) if ref is not None else None
        index = changed.current if changed is not None else self._index()
        seeds = changed.report["current_seeds"] if changed is not None else symbols
        candidates = impact(index, seeds, depth)["candidates"] if seeds else []
        lessons = self._lessons({row["id"] for row in candidates})
        result = changes.compile_changes(changed, max_tokens, depth, lessons) if changed is not None else compile_context(index, seeds, max_tokens, depth, lessons)
        result["excluded_lessons"] = [{"id": r["id"], "status": r["status"], "stale": r["stale"]} for r in lessons if r["status"] != "confirmed" or r["stale"]]
        if index.indexing:
            result["indexing"] = index.indexing
        return result

    def get_lessons(self, symbols: list[str]) -> dict:
        self._validate(symbols, None, 0)
        index = self._index()
        scopes = {select_symbol(index, s) for s in symbols}
        records = self._lessons(scopes)
        # Agent-facing retrieval includes only eligible text; excluded records
        # reveal status/reason, not advice the developer has not confirmed.
        return {
            "lessons": [r for r in records if r["status"] == "confirmed" and not r["stale"]],
            "excluded_lessons": [{"id": r["id"], "status": r["status"], "stale": r["stale"]} for r in records if r["status"] != "confirmed" or r["stale"]],
            "warnings": index.warnings,
            **({"indexing": index.indexing} if index.indexing else {}),
        }

    def investigate(self, task: str | None = None, symbols: list[str] | None = None,
                    ref: str | None = None, max_tokens: int = 4000, max_depth: int = 3,
                    max_steps: int = 7, max_seconds: float = 30) -> dict:
        return investigation.run(self.root, task=task, symbols=symbols, ref=ref,
                                 max_tokens=max_tokens, max_depth=max_depth,
                                 max_steps=max_steps, max_seconds=max_seconds,
                                 cache=self.cache,
                                 lesson_reader=self._lessons)
