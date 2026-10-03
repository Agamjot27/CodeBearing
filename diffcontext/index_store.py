"""Disposable per-file parse facts and current graph; never executable objects."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sqlite3
import sys
import time
from pathlib import Path

from . import __version__

SCHEMA_VERSION = "1"
FACTS_VERSION = "1"


def parser_fingerprint(path: str) -> str:
    """An unchanged file must be reparsed after parser/runtime/adapter upgrades."""
    versions = [FACTS_VERSION, __version__, sys.implementation.name,
                f"{sys.version_info.major}.{sys.version_info.minor}"]
    if not path.endswith(".py"):
        for package in ("tree-sitter", "tree-sitter-typescript", "tree-sitter-javascript"):
            try:
                versions.append(importlib.metadata.version(package))
            except importlib.metadata.PackageNotFoundError:
                versions.append("unavailable")
    return ":".join(versions)


def _encoded(value: dict) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()


class IndexStore:
    def __init__(self, root: Path):
        root = root.resolve()
        directory = root / ".diffcontext"
        path = directory / "index.sqlite3"
        # Cache writes must never follow a repository-created link elsewhere.
        if directory.is_symlink() or path.is_symlink():
            raise ValueError("Index cache cannot use symbolic links.")
        directory.mkdir(exist_ok=True)
        if not path.resolve().is_relative_to(root):
            raise ValueError("Index cache path escapes repository.")
        self.connection = sqlite3.connect(path, timeout=2)
        self._fingerprints = {}
        try:
            with self.connection:
                self.connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                metadata = dict(self.connection.execute("SELECT key,value FROM metadata"))
                if metadata != {"schema": SCHEMA_VERSION, "root": str(root)}:
                    # This DB is derived state, separate from engineering memory.
                    # A schema/root mismatch is reset rather than migrated as truth.
                    for table in ("files", "symbols", "edges"):
                        self.connection.execute(f"DROP TABLE IF EXISTS {table}")
                    self.connection.execute("DELETE FROM metadata")
                    self.connection.executemany("INSERT INTO metadata VALUES (?,?)",
                                                [("schema", SCHEMA_VERSION), ("root", str(root))])
                self.connection.execute("CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, digest TEXT NOT NULL, parser TEXT NOT NULL, payload TEXT NOT NULL, checksum TEXT NOT NULL)")
                self.connection.execute("CREATE TABLE IF NOT EXISTS symbols (id TEXT PRIMARY KEY, path TEXT NOT NULL, payload TEXT NOT NULL)")
                self.connection.execute("CREATE TABLE IF NOT EXISTS edges (caller TEXT NOT NULL, target TEXT NOT NULL, PRIMARY KEY(caller,target))")
        except Exception:
            self.connection.close()
            raise

    def load(self, sources: dict[str, bytes]) -> tuple[dict, int]:
        units = {}
        rows = list(self.connection.execute("SELECT path,digest,parser,payload,checksum FROM files"))
        for path, digest, parser, payload, checksum in rows:
            if path not in sources or digest != hashlib.sha256(sources[path]).hexdigest() or parser != self.fingerprint(path):
                continue
            if _checksum(payload) != checksum:
                continue
            try:
                unit = json.loads(payload)
            except (ValueError, TypeError):
                continue
            if isinstance(unit, dict):
                units[path] = unit
        return units, len({row[0] for row in rows} - sources.keys())

    def fingerprint(self, path):
        language = "python" if path.endswith(".py") else "web"
        if language not in self._fingerprints:
            self._fingerprints[language] = parser_fingerprint(path)
        return self._fingerprints[language]

    def publish(self, sources: dict[str, bytes], units: dict, index):
        # One transaction publishes units, deletes and the graph together. Readers
        # see the previous complete generation or this one, never half an edit.
        with self.connection:
            self.connection.execute("DELETE FROM files")
            for path, unit in units.items():
                if path not in sources:
                    continue
                payload = _encoded(unit)
                self.connection.execute("INSERT INTO files VALUES (?,?,?,?,?)",
                    (path, hashlib.sha256(sources[path]).hexdigest(), self.fingerprint(path), payload, _checksum(payload)))
            self.connection.execute("DELETE FROM symbols")
            from dataclasses import asdict
            self.connection.executemany("INSERT INTO symbols VALUES (?,?,?)",
                [(symbol.id, symbol.path, _encoded(asdict(symbol))) for symbol in index.symbols.values()])
            self.connection.execute("DELETE FROM edges")
            self.connection.executemany("INSERT INTO edges VALUES (?,?)",
                [(caller, target) for caller, targets in index.edges.items() for target in targets])

    def close(self):
        self.connection.close()


def build_cached_sources(root: Path, sources: dict[str, bytes], warnings: list[str] | None = None):
    """Hash captured bytes, reuse parse facts, then relink the complete graph."""
    from .index import build_index_from_sources

    started = time.perf_counter()
    store = None
    units = {}
    removed = 0
    cache_error = None
    try:
        store = IndexStore(root)
        units, removed = store.load(sources)
    except (OSError, sqlite3.Error, ValueError) as exc:
        if store:
            store.close()
            store = None
        cache_error = f"Index cache unavailable ({type(exc).__name__}); fresh parsing used."
    reused = len(units)
    # JSON is data, not pickle. Malformed facts must not break context retrieval.
    # Reparse all captured evidence if an otherwise checksummed payload is invalid.
    try:
        try:
            index = build_index_from_sources(root, sources, warnings, units=units)
        except (KeyError, TypeError, ValueError, AttributeError):
            if not reused:
                raise
            units = {}
            reused = 0
            index = build_index_from_sources(root, sources, warnings, units=units)
    except Exception:
        if store:
            store.close()
        raise
    persisted = False
    if store:
        try:
            if reused != len(sources) or removed:
                store.publish(sources, units, index)
            persisted = True
        except (OSError, sqlite3.Error) as exc:
            cache_error = f"Index cache write failed ({type(exc).__name__}); current evidence is fresh."
        finally:
            store.close()
    if cache_error:
        index.warnings.append(cache_error)
    index.indexing = {"cache": "persistent" if persisted else "fallback", "captured_files": len(sources),
                      "reused_files": reused, "parsed_files": len(units) - reused,
                      "uncached_files": len(sources) - len(units), "removed_files": removed,
                      "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                      "scope": "capture is measured separately; all dependency facts are relinked"}
    return index
