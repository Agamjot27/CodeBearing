"""Task retrieval regressions; fixture outcomes are not model-quality evidence."""

import unittest
from unittest.mock import patch

import test_core

from codebearing.context import compile_context, estimate_tokens, search
from codebearing.index import build_index
from codebearing.memory import Memory
from codebearing.service import RepositoryService


class HybridTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def lesson(self, text="Chargeback settlement requires final rounding", confirmed=True):
        store = Memory(self.root)
        try:
            lesson_id = store.add(build_index(self.root), "billing.py:refund_total", text, "test_billing.py")
            if confirmed:
                store.set_status(lesson_id, "confirmed")
            return lesson_id, store.list()[0]
        finally:
            store.close()

    def test_identifier_splitting_localizes_natural_language_camel_and_snake(self):
        self.write("camel.py", "def reconcileBalance(amount):\n    return amount\n")
        service = RepositoryService(self.root)
        for query, expected in (("refund total", "billing.py:refund_total"),
                                ("reconcile balance", "camel.py:reconcileBalance")):
            self.assertFalse(search(build_index(self.root), query))
            matches = service.search_symbols(query)["matches"]
            self.assertTrue(matches)
            self.assertEqual(matches[0]["id"], expected)
            run = service.investigate(task=query, max_depth=1)
            self.assertIn(expected, run["seeds"]["current"])

    def test_explicit_selection_preserves_legacy_context(self):
        service = RepositoryService(self.root)
        reference = compile_context(build_index(self.root), ["billing.py:refund_total"], budget=1000, depth=1)
        for policy in ("hybrid", "legacy"):
            run = service.investigate(symbols=["billing.py:refund_total"], max_depth=1,
                                      max_tokens=1000, retrieval=policy)
            self.assertEqual(run["context"]["text"], reference["text"])
            self.assertEqual(run["context"]["included"], reference["included"])

    def test_legacy_task_policy_is_available(self):
        service = RepositoryService(self.root)
        legacy = service.search_symbols("refund_total", retrieval="legacy")["matches"]
        self.assertEqual(legacy, search(build_index(self.root), "refund_total"))
        run = service.investigate(task="refund total", retrieval="legacy")
        self.assertEqual((run["status"], run["stop_reason"]), ("needs_input", "no_matches"))

    def test_no_match_and_validation_do_not_manufacture_seeds(self):
        service = RepositoryService(self.root)
        self.assertEqual(service.search_symbols("xyzzynonexistent") ["matches"], [])
        run = service.investigate(task="xyzzynonexistent")
        self.assertEqual(run["seeds"]["current"], [])
        self.assertEqual(run["stop_reason"], "no_matches")
        for query in ("", " ", "a" * 2001):
            with self.assertRaises(ValueError):
                service.search_symbols(query)
        with self.assertRaises(ValueError):
            service.search_symbols("refund", retrieval="unknown")
        with self.assertRaises(ValueError):
            service.investigate(task="refund", retrieval="unknown")

    def test_four_equal_matches_remain_ambiguous(self):
        for name in ("a", "b", "c", "d"):
            self.write(f"{name}.py", "def identicalSignal():\n    return 1\n")
        run = RepositoryService(self.root).investigate(task="identical signal")
        self.assertEqual((run["status"], run["stop_reason"]), ("needs_input", "ambiguous_matches"))

    def test_confirmed_memory_can_localize_opaque_code_and_is_packed_with_scope(self):
        lesson_id, _ = self.lesson()
        service = RepositoryService(self.root)
        matches = service.search_symbols("chargeback settlement")["matches"]
        self.assertEqual(matches[0]["id"], "billing.py:refund_total")
        run = service.investigate(task="chargeback settlement", max_tokens=1000, max_depth=1)
        packet = run["context"]
        self.assertIn(lesson_id, packet["included_lessons"])
        self.assertIn("billing.py:refund_total", {row["id"] for row in packet["included"]})
        self.assertIn("Chargeback settlement", packet["text"])
        self.assertLessEqual(estimate_tokens(packet["text"]), 1000)

    def test_proposed_and_stale_memory_never_boost_search(self):
        lesson_id, _ = self.lesson(confirmed=False)
        service = RepositoryService(self.root)
        self.assertEqual(service.search_symbols("chargeback settlement")["matches"], [])
        store = Memory(self.root)
        try:
            store.set_status(lesson_id, "confirmed")
        finally:
            store.close()
        self.write("test_billing.py", "# Evidence changed after confirmation\n")
        self.assertEqual(service.search_symbols("chargeback settlement")["matches"], [])
        run = service.investigate(task="chargeback settlement")
        self.assertEqual(run["stop_reason"], "no_matches")

    def test_current_snapshot_hash_validation_blocks_forged_fresh_memory(self):
        _, record = self.lesson()
        for field in ("scope_hash", "evidence_hash"):
            corrupted = {**record, field: "not-the-captured-hash", "stale": False}
            with patch.object(RepositoryService, "_lessons", return_value=[corrupted]):
                service = RepositoryService(self.root)
                self.assertEqual(service.search_symbols("chargeback settlement")["matches"], [])
                self.assertEqual(service.investigate(task="chargeback settlement")["stop_reason"], "no_matches")

    def test_whole_code_citations_and_budget_omissions_remain_visible(self):
        index = build_index(self.root)
        service = RepositoryService(self.root)
        packet = service.investigate(task="refund total", max_tokens=1000, max_depth=1)["context"]
        self.assertLessEqual(estimate_tokens(packet["text"]), 1000)
        self.assertEqual(packet["included"][0]["id"], "billing.py:refund_total")
        for row in packet["included"]:
            self.assertIn(index.symbols[row["id"]].source, packet["text"])
            self.assertEqual(row["file_hash"], index.hashes[row["path"]])
            self.assertIn(f"{row['path']}:{row['start']}-{row['end']}", packet["text"])
        self.write("huge.py", "def giganticTarget():\n" + "    x = 'long statement for budget exhaustion'\n" * 100)
        packet = service.investigate(task="gigantic target", max_tokens=128, max_depth=0)["context"]
        self.assertEqual(packet["missing_seeds"], ["huge.py:giganticTarget"])
        self.assertEqual(packet["included"], [])
        self.assertTrue(packet["omitted"])
        self.assertLessEqual(estimate_tokens(packet["text"]), 128)

    def test_memory_is_not_packed_when_its_scope_code_cannot_fit(self):
        self.write("billing.py", "def refund_total(amounts):\n" + "    value = 'source must not be silently truncated'\n" * 100)
        lesson_id, _ = self.lesson()
        packet = RepositoryService(self.root).investigate(task="chargeback settlement", max_tokens=128, max_depth=0)["context"]
        self.assertNotIn(lesson_id, packet["included_lessons"])
        self.assertNotIn("Chargeback settlement", packet["text"])
        self.assertIn("billing.py:refund_total", packet["missing_seeds"])
        self.assertLessEqual(estimate_tokens(packet["text"]), 128)

    def test_cache_and_fresh_task_rankings_match_and_queries_are_not_cached(self):
        self.lesson()
        plain = RepositoryService(self.root)
        cached = RepositoryService(self.root, cache=True)
        for query in ("refund total", "chargeback settlement", "noSuchQuery", "round line"):
            self.assertEqual(plain.search_symbols(query)["matches"], cached.search_symbols(query)["matches"])
        self.write("billing.py", "def refund_total(amounts):\n    return 0\n")
        self.assertEqual(cached.search_symbols("chargeback settlement")["matches"], [])
        self.assertEqual(plain.search_symbols("refund total")["matches"], cached.search_symbols("refund total")["matches"])


if __name__ == "__main__":
    unittest.main()
