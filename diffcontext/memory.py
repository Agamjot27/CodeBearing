"""Repository-local lessons with explicit confirmation and evidence freshness."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .index import Index, digest, safe_path


class Memory:
    def __init__(self, root: Path):
        self.root = root.resolve()
        directory = self.root / ".diffcontext"
        if directory.is_symlink():
            raise ValueError("Memory directory must not be a symbolic link.")
        directory.mkdir(exist_ok=True)
        database = directory / "memory.sqlite3"
        if database.is_symlink():
            raise ValueError("Memory database must not be a symbolic link.")
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("""CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY, scope TEXT NOT NULL, lesson TEXT NOT NULL,
            evidence TEXT NOT NULL, evidence_hash TEXT NOT NULL, scope_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'proposed', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        self.connection.commit()

    def close(self):
        self.connection.close()

    def add(self, index: Index, scope: str, lesson: str, evidence: str) -> int:
        if scope not in index.symbols:
            raise ValueError("Lesson scope must be an exact indexed symbol ID.")
        if not lesson.strip():
            raise ValueError("Lesson text cannot be empty.")
        evidence_path = safe_path(self.root, evidence)
        if evidence not in index.hashes:
            raise ValueError("Evidence must be an indexed Python file in this first version.")
        scope_hash = index.hashes[index.symbols[scope].path]
        cursor = self.connection.execute("INSERT INTO lessons(scope,lesson,evidence,evidence_hash,scope_hash) VALUES (?,?,?,?,?)", (scope, lesson, evidence, digest(evidence_path), scope_hash))
        self.connection.commit()
        return cursor.lastrowid

    def set_status(self, lesson_id: int, status: str):
        if status not in {"confirmed", "superseded", "disputed"}:
            raise ValueError("Status must be confirmed, superseded, or disputed.")
        if status == "confirmed":
            row = next((r for r in self.list() if r["id"] == lesson_id), None)
            if row is None:
                raise ValueError("Unknown lesson ID.")
            if row["stale"]:
                raise ValueError("Evidence changed or disappeared; add a new reviewed lesson.")
        cursor = self.connection.execute("UPDATE lessons SET status=? WHERE id=?", (status, lesson_id))
        if not cursor.rowcount:
            raise ValueError("Unknown lesson ID.")
        self.connection.commit()

    def list(self, scopes: set[str] | None = None) -> list[dict]:
        results = []
        for row in self.connection.execute("SELECT * FROM lessons ORDER BY id"):
            record = dict(row)
            if scopes is not None and record["scope"] not in scopes:
                continue
            try:
                scope_file = record["scope"].split(":", 1)[0]
                record["stale"] = (digest(safe_path(self.root, record["evidence"])) != record["evidence_hash"] or digest(safe_path(self.root, scope_file)) != record["scope_hash"])
            except (OSError, ValueError):
                record["stale"] = True
            results.append(record)
        return results
