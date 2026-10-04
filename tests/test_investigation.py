import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_core
import test_changes
from diffcontext import investigation
from diffcontext.context import estimate_tokens
from diffcontext.index import build_index
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService
from diffcontext.runs import load_summary, summarize


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

    def test_hybrid_task_context_covers_disconnected_aspects_and_legacy_stays_pinned(self):
        self.write("totals.py", "def bookingTotal():\n    return 1\n")
        self.write("booking.py", "def confirm():\n    confirmation = 'booking payment'\n    return confirmation\n")
        self.write("transaction.py", "def transaction():\n    return 'rollback'\n")
        service = RepositoryService(self.root)
        query = "booking confirmation payment rollback"
        result = service.investigate(task=query, max_tokens=4000)
        self.assertTrue({"booking.py:confirm", "transaction.py:transaction"}
                        <= set(result["seeds"]["current"]))
        self.assertLessEqual(len(result["seeds"]["current"]), 3)
        self.assertIn("def confirm", result["context"]["text"])
        self.assertIn("def transaction", result["context"]["text"])
        self.assertEqual(result["retrieval"]["seed_selection"]["max_seeds"], 3)
        old = service.investigate(task=query, retrieval="legacy")
        top = old["search_matches"][0]["score"]
        self.assertEqual(old["seeds"]["current"],
                         [r["id"] for r in old["search_matches"] if r["score"] == top])

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

    def test_cli_saved_run_and_inspection(self):
        command = [sys.executable, "-m", "diffcontext", "--repo", str(self.root)]
        result = subprocess.run([*command, "investigate", "--task", "refund_total"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "ready")
        path = self.root / "run.json"
        path.write_text(result.stdout, encoding="utf-8-sig")
        # Inspection works on saved evidence even after the target disappears.
        inspected = subprocess.run([sys.executable, "-m", "diffcontext", "--repo", str(self.root / "missing"),
                                    "inspect", str(path)], capture_output=True, text=True)
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        view = json.loads(inspected.stdout)
        self.assertEqual(view["run_id"], report["run_id"])
        self.assertNotIn("text", view)
        self.assertEqual(view["trace"][-1]["stage"], "stop")
        self.assertTrue(view["evidence"]["current"])
        compact = subprocess.run([*command, "investigate", "--symbol", "round_line", "--summary"], capture_output=True, text=True)
        self.assertEqual(compact.returncode, 0, compact.stderr)
        self.assertEqual(json.loads(compact.stdout)["status"], "ready")

    def test_inspection_rejects_malformed_saved_reports(self):
        path = self.root / "run.json"
        for data in ['not json', '{"schema_version": 2}', '{"schema_version": 1, "status": "ready"}']:
            path.write_text(data, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_summary(path)
        path.write_bytes(b"\xff\xfe")
        with self.assertRaises(ValueError):
            load_summary(path)
        with self.assertRaises(ValueError):
            summarize({"schema_version": 1, "status": "invented"})
        with patch("diffcontext.runs.MAX_RUN_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "limit"):
                load_summary(path)
        failed = subprocess.run([sys.executable, "-m", "diffcontext", "inspect", str(path)], capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("UTF-8", failed.stderr)

    def test_time_limit_after_compile_preserves_partial_evidence(self):
        now = [0.0]
        original = investigation.compile_context
        def slow_compile(*args):
            package = original(*args)
            now[0] = 1.0
            return package
        with patch.object(investigation, "compile_context", side_effect=slow_compile):
            result = investigation.run(self.root, symbols=["round_line"], max_seconds=0.1, clock=lambda: now[0])
        self.assertEqual(result["stop_reason"], "time_limit")
        self.assertIsNotNone(result["context"])


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
