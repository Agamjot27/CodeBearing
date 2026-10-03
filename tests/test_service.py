import sqlite3
import unittest

import test_core
from diffcontext.context import compile_context
from diffcontext.index import build_index
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService


class ServiceTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write
    def test_service_preserves_core_result_and_does_not_create_memory(self):
        service = RepositoryService(self.root)
        expected = compile_context(build_index(self.root), ["refund_total"])
        actual = service.compile_context(["refund_total"])
        self.assertEqual(actual["text"], expected["text"])
        self.assertEqual(service.get_lessons(["refund_total"])["lessons"], [])
        self.assertFalse((self.root / ".diffcontext").exists())

    def test_readonly_database_rejects_sql_and_mutations(self):
        store = Memory(self.root)
        store.close()
        readonly = Memory(self.root, read_only=True)
        self.addCleanup(readonly.close)
        with self.assertRaises(sqlite3.OperationalError):
            readonly.connection.execute("INSERT INTO lessons(scope,lesson,evidence,evidence_hash,scope_hash) VALUES ('x','x','x','x','x')")
        with self.assertRaisesRegex(ValueError, "Read-only"):
            readonly.set_status(1, "confirmed")
        with self.assertRaisesRegex(ValueError, "Read-only"):
            readonly.add(build_index(self.root), "billing.py:refund_total", "x", "test_billing.py")

    def test_service_filters_lessons_and_leaves_db_bytes_unchanged(self):
        store = Memory(self.root)
        index = build_index(self.root)
        confirmed = store.add(index, "billing.py:refund_total", "Round per line", "test_billing.py")
        store.set_status(confirmed, "confirmed")
        proposed = store.add(index, "billing.py:refund_total", "Unreviewed", "test_billing.py")
        store.close()
        path = self.root / ".diffcontext" / "memory.sqlite3"
        before = path.read_bytes()
        service = RepositoryService(self.root)
        result = service.get_lessons(["refund_total"])
        self.assertEqual([r["id"] for r in result["lessons"]], [confirmed])
        self.assertEqual(result["excluded_lessons"][0]["id"], proposed)
        self.assertEqual(service.compile_context(["refund_total"])["included_lessons"], [confirmed])
        self.assertEqual(path.read_bytes(), before)
        self.write("test_billing.py", "# changed\n")
        self.assertEqual(service.get_lessons(["refund_total"])["lessons"], [])

    def test_service_bounds_and_fixed_repository(self):
        service = RepositoryService(self.root)
        for symbols, ref in [(None, None), (["refund_total"], "HEAD"), ([], None), (["../outside.py:x"], None)]:
            with self.assertRaises(ValueError):
                service.analyze_impact(symbols, ref)
        with self.assertRaises(ValueError):
            service.search_symbols("refund", 51)
        with self.assertRaises(ValueError):
            service.compile_context(["refund_total"], max_tokens=32001)
        with self.assertRaises(sqlite3.OperationalError):
            Memory(self.root / "missing", read_only=True)
