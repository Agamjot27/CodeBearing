"""Incremental parse reuse must preserve the graph and fresh source evidence."""

import hashlib
import json
import os
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

import test_core
import test_typescript

from diffcontext.index import build_index
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService


class IndexStoreTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    @property
    def database(self):
        return self.root / ".diffcontext" / "index.sqlite3"

    def cached(self):
        return build_index(self.root, cache=True)

    def assert_parity(self, cached):
        described = cached.describe()
        described.pop("indexing", None)
        self.assertEqual(described, build_index(self.root).describe())

    def mutate_db(self, sql, parameters=()):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(sql, parameters)
            connection.commit()

    def test_default_build_is_pure_and_cold_warm_reuse_skips_parser(self):
        full = build_index(self.root)
        self.assertNotIn("indexing", full.describe())
        self.assertFalse((self.root / ".diffcontext").exists())
        cold = self.cached()
        self.assert_parity(cold)
        self.assertEqual(cold.indexing["parsed_files"], 3)
        self.assertEqual(cold.indexing["reused_files"], 0)
        with patch("diffcontext.index._python_unit", side_effect=AssertionError("Warm build parsed unchanged bytes")):
            warm = self.cached()
        self.assert_parity(warm)
        self.assertEqual(warm.indexing["parsed_files"], 0)
        self.assertEqual(warm.indexing["reused_files"], 3)
        self.assertEqual(warm.indexing["captured_files"], 3)
        self.assertEqual(warm.indexing["uncached_files"], 0)
        with closing(sqlite3.connect(self.database)) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"metadata", "files", "symbols", "edges"} <= tables)
            self.assertEqual({row[0] for row in connection.execute("SELECT id FROM symbols")}, set(warm.symbols))
            self.assertEqual(set(connection.execute("SELECT caller,target FROM edges")),
                             {(caller, target) for caller, targets in warm.edges.items() for target in targets})

    def test_edit_add_delete_rename_relink_unchanged_callers(self):
        self.cached()
        self.write("billing.py", "def refund_total(amounts):\n    return sum(amounts)\n")
        edited = self.cached()
        self.assert_parity(edited)
        self.assertEqual((edited.indexing["parsed_files"], edited.indexing["reused_files"]), (1, 2))
        self.assertEqual(edited.edges["checkout.py:checkout"], {"billing.py:refund_total"})
        self.write("extra.py", "from billing import refund_total\n\ndef extra(items):\n    return refund_total(items)\n")
        added = self.cached()
        self.assert_parity(added)
        self.assertEqual(added.indexing["parsed_files"], 1)
        (self.root / "billing.py").rename(self.root / "renamed.py")
        renamed = self.cached()
        self.assert_parity(renamed)
        self.assertEqual(renamed.indexing["removed_files"], 1)
        self.assertEqual(renamed.indexing["parsed_files"], 1)
        self.assertFalse(renamed.edges["checkout.py:checkout"])
        (self.root / "renamed.py").unlink()
        deleted = self.cached()
        self.assert_parity(deleted)
        self.assertEqual(deleted.indexing["removed_files"], 1)
        self.assertEqual(deleted.indexing["parsed_files"], 0)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertFalse(list(connection.execute("SELECT id FROM symbols WHERE path IN ('billing.py','renamed.py')")))
            self.assertFalse(list(connection.execute("SELECT target FROM edges WHERE target LIKE 'billing.py:%'")))

    def test_exporter_rename_relinks_importer_without_reparsing_it(self):
        self.cached()
        self.write("billing.py", "def renamed_total(amounts):\n    return sum(amounts)\n")
        index = self.cached()
        self.assert_parity(index)
        self.assertEqual(index.indexing["reused_files"], 2)
        self.assertFalse(index.edges["checkout.py:checkout"])

    def test_same_size_and_mtime_edit_is_not_missed(self):
        self.cached()
        target = self.root / "checkout.py"
        before = target.stat()
        target.write_text(target.read_text().replace("calculate(items)", "calculate([123])"), encoding="utf-8")
        self.assertEqual(target.stat().st_size, before.st_size)
        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
        index = self.cached()
        self.assert_parity(index)
        self.assertEqual(index.indexing["parsed_files"], 1)
        self.assertIn("[123]", index.symbols["checkout.py:checkout"].source)

    def test_syntax_failure_is_reusable_and_recovers_on_edit(self):
        self.write("broken.py", "def ?")
        cold = self.cached()
        self.assert_parity(cold)
        self.assertIn("broken.py", cold.sources)
        self.assertNotIn("broken.py", cold.hashes)
        with patch("diffcontext.index._python_unit", side_effect=AssertionError("Failed parse reparsed unchanged")):
            warm = self.cached()
        self.assert_parity(warm)
        self.assertEqual(warm.indexing["reused_files"], 4)
        self.write("broken.py", "def recovered():\n    return 1\n")
        fixed = self.cached()
        self.assert_parity(fixed)
        self.assertIn("broken.py:recovered", fixed.symbols)
        self.assertEqual(fixed.indexing["parsed_files"], 1)

    def test_bad_checksum_and_parser_fingerprint_force_reparse(self):
        self.cached()
        self.mutate_db("UPDATE files SET checksum='invalid' WHERE path='billing.py'")
        recovered = self.cached()
        self.assert_parity(recovered)
        self.assertEqual(recovered.indexing["parsed_files"], 1)
        self.mutate_db("UPDATE files SET parser='obsolete-parser'")
        reparsed = self.cached()
        self.assert_parity(reparsed)
        self.assertEqual(reparsed.indexing["parsed_files"], 3)

    def test_checksummed_invalid_facts_fall_back_to_fresh_parsing(self):
        self.cached()
        payload = json.dumps({"wrong_contract": True})
        checksum = hashlib.sha256(payload.encode()).hexdigest()
        self.mutate_db("UPDATE files SET payload=?,checksum=? WHERE path='billing.py'", (payload, checksum))
        recovered = self.cached()
        self.assert_parity(recovered)
        self.assertEqual(recovered.indexing["reused_files"], 0)
        self.assertEqual(recovered.indexing["parsed_files"], 3)

    def test_schema_and_repository_fingerprint_mismatch_reset_cache(self):
        self.cached()
        for key in ("schema", "root"):
            self.mutate_db("UPDATE metadata SET value='mismatched' WHERE key=?", (key,))
            rebuilt = self.cached()
            self.assert_parity(rebuilt)
            self.assertEqual(rebuilt.indexing["reused_files"], 0)
            self.assertEqual(rebuilt.indexing["parsed_files"], 3)

    def test_corrupt_database_falls_back_without_losing_current_evidence(self):
        self.cached()
        self.database.write_bytes(b"not a SQLite database")
        recovered = self.cached()
        fresh = build_index(self.root)
        self.assertEqual(recovered.symbols, fresh.symbols)
        self.assertEqual(recovered.edges, fresh.edges)
        self.assertEqual(recovered.hashes, fresh.hashes)
        self.assertEqual(recovered.sources, fresh.sources)
        self.assertEqual(recovered.indexing["cache"], "fallback")
        self.assertTrue(any("cache" in warning.lower() for warning in recovered.warnings))

    def test_cache_publish_failure_returns_fresh_graph_and_warning(self):
        with patch("diffcontext.index_store.IndexStore.publish", side_effect=sqlite3.OperationalError("fixture write failure")):
            index = self.cached()
        fresh = build_index(self.root)
        self.assertEqual(index.symbols, fresh.symbols)
        self.assertEqual(index.edges, fresh.edges)
        self.assertEqual(index.hashes, fresh.hashes)
        self.assertEqual(index.indexing["cache"], "fallback")
        self.assertTrue(any("write failed" in warning.lower() for warning in index.warnings))

    def test_symlink_cache_is_refused_without_writing_target(self):
        target = self.root / "target.sqlite3"
        target.write_bytes(b"must stay untouched")
        self.database.parent.mkdir()
        try:
            self.database.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"Creating symbolic links is unavailable: {type(exc).__name__}")
        index = self.cached()
        self.assertEqual(index.indexing["cache"], "fallback")
        self.assertEqual(index.symbols, build_index(self.root).symbols)
        self.assertEqual(target.read_bytes(), b"must stay untouched")

    def test_service_cache_reports_reuse_without_modifying_engineering_memory(self):
        memory = Memory(self.root)
        memory.add(build_index(self.root), "billing.py:refund_total", "Keep rounding consistent", "test_billing.py")
        memory.close()
        memory_path = self.root / ".diffcontext" / "memory.sqlite3"
        original_memory = memory_path.read_bytes()
        service = RepositoryService(self.root, cache=True)
        found = service.search_symbols("refund_total")
        self.assertEqual(found["indexing"]["parsed_files"], 3)
        packet = service.compile_context(symbols=["billing.py:refund_total"])
        self.assertEqual(packet["indexing"]["reused_files"], 3)
        run = service.investigate(symbols=["billing.py:refund_total"])
        self.assertEqual(run["indexing"]["reused_files"], 3)
        self.assertEqual(memory_path.read_bytes(), original_memory)

    @unittest.skipUnless(test_typescript.HAS_PARSERS, "Install the typescript extra")
    def test_typescript_export_edits_and_deletions_relink_reused_importers(self):
        self.write("helper.ts", "export function target() { return 1; }\n")
        self.write("caller.ts", "import { target } from './helper';\nexport function caller() { return target(); }\n")
        self.cached()
        warm = self.cached()
        self.assert_parity(warm)
        self.assertEqual(warm.indexing["reused_files"], 5)
        self.write("helper.ts", "export function renamed() { return 2; }\n")
        edited = self.cached()
        self.assert_parity(edited)
        self.assertEqual(edited.indexing["reused_files"], 4)
        self.assertEqual(edited.indexing["parsed_files"], 1)
        self.assertFalse(edited.edges["caller.ts:caller"])
        (self.root / "helper.ts").unlink()
        deleted = self.cached()
        self.assert_parity(deleted)
        self.assertEqual(deleted.indexing["removed_files"], 1)
        self.assertFalse(deleted.edges["caller.ts:caller"])


if __name__ == "__main__":
    unittest.main()
