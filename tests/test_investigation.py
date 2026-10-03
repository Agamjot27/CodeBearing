import unittest
from unittest.mock import patch

import test_core
import test_changes
from diffcontext import investigation
from diffcontext.context import estimate_tokens
from diffcontext.index import build_index
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService


class InvestigationTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_expands_once_per_depth_on_one_snapshot(self):
        original = build_index(self.root)
        with patch.object(investigation, "build_index", return_value=original) as capture:
            result = RepositoryService(self.root).investigate(symbols=["round_line"])
        capture.assert_called_once_with(self.root)
        self.assertEqual(result["status"], "ready", result["verification"])
        self.assertEqual(result["stop_reason"], "graph_covered")
        depths = [e["depth"] for e in result["trace"] if e["stage"] == "compile"]
        self.assertEqual(depths, [0, 1, 2])
        self.assertEqual(result["verification"]["frontier"], {"current": []})
        self.assertIn("checkout.py:checkout", {r["id"] for r in result["context"]["included"]})
        self.assertFalse((self.root / ".diffcontext").exists())

    def test_task_selection_no_match_and_ambiguity(self):
        service = RepositoryService(self.root)
        result = service.investigate(task="refund_total")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["seeds"]["current"], ["billing.py:refund_total"])
        self.assertEqual(service.investigate(task="zzzzunfindable")["stop_reason"], "no_matches")
        for n in range(4):
            self.write(f"copy{n}.py", "def unique_name():\n    return 1\n")
        result = service.investigate(task="unique_name")
        self.assertEqual(result["stop_reason"], "ambiguous_matches")
        self.assertIsNone(result["context"])

    def test_budget_and_depth_have_visible_gaps(self):
        service = RepositoryService(self.root)
        limited = service.investigate(symbols=["refund_total"], max_tokens=128)
        self.assertEqual(limited["stop_reason"], "token_budget")
        self.assertTrue(limited["verification"]["omitted"]["current"])
        self.assertLessEqual(estimate_tokens(limited["context"]["text"]), 128)
        shallow = service.investigate(symbols=["round_line"], max_depth=0)
        self.assertEqual(shallow["stop_reason"], "depth_limit")
        self.assertIn("billing.py:refund_total", shallow["verification"]["frontier"]["current"])

    def test_step_limit_and_cooperative_deadline(self):
        result = RepositoryService(self.root).investigate(symbols=["round_line"], max_steps=2)
        self.assertEqual(result["stop_reason"], "step_limit")
        self.assertEqual(result["usage"]["operations"], 2)
        self.assertIsNotNone(result["context"])
        now = [0.0]
        def capture(root):
            index = build_index(root)
            now[0] = 1.0
            return index
        with patch.object(investigation, "build_index", side_effect=capture):
            timed = investigation.run(self.root, symbols=["round_line"], max_seconds=0.1, clock=lambda: now[0])
        self.assertEqual(timed["stop_reason"], "time_limit")
        self.assertIsNone(timed["context"])

    def test_snapshot_stays_fixed_and_identity_tracks_content(self):
        index = build_index(self.root)
        with patch.object(investigation, "build_index", return_value=index):
            self.write("billing.py", "def unrelated():\n    return 0\n")
            result = RepositoryService(self.root).investigate(symbols=["round_line"])
        self.assertIn("def round_line", result["context"]["text"])
        fresh = RepositoryService(self.root).investigate(symbols=["unrelated"])
        self.assertNotEqual(result["snapshot"], fresh["snapshot"])

    def test_memory_filtering_and_snapshot_mismatch(self):
        index = build_index(self.root)
        store = Memory(self.root)
        lesson = store.add(index, "billing.py:refund_total", "Round each line", "test_billing.py")
        store.set_status(lesson, "confirmed")
        proposed = store.add(index, "billing.py:refund_total", "Wrong unreviewed advice", "test_billing.py")
        store.close()
        database = self.root / ".diffcontext" / "memory.sqlite3"
        before = database.read_bytes()
        service = RepositoryService(self.root)
        result = service.investigate(symbols=["refund_total"])
        self.assertIn(lesson, result["context"]["included_lessons"])
        self.assertNotIn("Wrong unreviewed advice", result["context"]["text"])
        self.assertEqual(database.read_bytes(), before)
        # Even a reader claiming freshness cannot attach lessons inconsistent
        # with captured code: this protects the memory/code capture race.
        records = service._lessons(set(index.symbols))
        records[0]["scope_hash"] = "different snapshot"
        rejected = investigation.run(self.root, symbols=["refund_total"], lesson_reader=lambda scopes: records)
        self.assertNotIn(lesson, rejected["context"]["included_lessons"])
        self.assertEqual({r["id"] for r in rejected["context"]["excluded_lessons"]}, {lesson, proposed})

    def test_validation_and_parse_gaps(self):
        service = RepositoryService(self.root)
        for kwargs in [{}, {"task": "x", "symbols": ["round_line"]}, {"task": " "},
                       {"symbols": []}, {"symbols": ["round_line"], "max_steps": 1},
                       {"symbols": ["round_line"], "max_seconds": float("nan")}]:
            with self.assertRaises(ValueError):
                service.investigate(**kwargs)
        self.write("broken.py", "def nope(:\n")
        self.assertEqual(service.investigate(symbols=["round_line"])["stop_reason"], "index_warnings")


class RevisionInvestigationTests(unittest.TestCase):
    setUp = test_changes.ChangesTests.setUp
    write = test_changes.ChangesTests.write
    git = test_changes.ChangesTests.git
    cleanup = test_changes.ChangesTests.cleanup

    def test_deleted_function_uses_both_graphs(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        result = RepositoryService(self.root).investigate(ref="HEAD")
        self.assertEqual(result["status"], "partial", result["verification"])
        self.assertEqual(result["stop_reason"], "unresolved_changes")
        self.assertIn("HISTORICAL EVIDENCE", result["context"]["text"])
        self.assertIn("billing.py:refund", result["seeds"]["historical"])
        self.assertEqual(result["verification"]["frontier"], {"current": [], "historical": []})

    def test_no_changes_and_unresolved_configuration(self):
        service = RepositoryService(self.root)
        self.assertEqual(service.investigate(ref="HEAD")["status"], "no_changes")
        self.write("billing.py", "RATE = 3\n\ndef helper(x):\n    return x * RATE\n\ndef refund(x):\n    return helper(x)\n")
        result = service.investigate(ref="HEAD")
        self.assertEqual(result["stop_reason"], "unresolved_changes")
        self.assertTrue(result["verification"]["unresolved_changes"])
        self.assertFalse(result["context"]["complete"])
