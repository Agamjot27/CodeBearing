"""Verify real persistence/review/freshness boundaries in the public demo."""

import json
from pathlib import Path
import shutil
import unittest
import uuid

from scripts.demo_memory import run_demo


class MemoryDemoTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1] / ".test-tmp" / ("memory-demo-" + uuid.uuid4().hex)
        self.root.parent.mkdir(exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))

    def test_default_never_confirms_a_lesson(self):
        result = run_demo(self.root)
        self.assertFalse(result["review"]["performed"])
        self.assertFalse(result["review"]["human_approval_claimed"])
        self.assertEqual(result["proposal"]["retrieval"]["lessons"], [])
        self.assertEqual(result["proposal"]["retrieval"]["excluded_lessons"][0]["status"], "proposed")
        self.assertEqual(json.loads((self.root / "MEMORY_DEMO_RESULT.json").read_text()), result)

    def test_explicit_operator_review_survives_new_process_then_goes_stale(self):
        result = run_demo(self.root, "test-operator")
        self.assertEqual(result["review"]["actor"], "test-operator")
        self.assertFalse(result["review"]["human_approval_claimed"])
        self.assertTrue(result["compiled_lesson_included"])
        self.assertEqual(len(result["fresh_process_retrieval"]["lessons"]), 1)
        self.assertEqual(result["after_source_change"]["lessons"], [])
        self.assertTrue(result["after_source_change"]["excluded_lessons"][0]["stale"])
        self.assertFalse(result["stale_lesson_compiled"])
        self.assertFalse(result["regression"]["before_fix_passed"])
        self.assertTrue(result["regression"]["after_fix_passed"])

    def test_nonempty_directory_is_preserved(self):
        self.root.mkdir()
        marker = self.root / "keep.txt"
        marker.write_text("untouched")
        with self.assertRaisesRegex(ValueError, "existing files"):
            run_demo(self.root, "operator")
        self.assertEqual(marker.read_text(), "untouched")


if __name__ == "__main__":
    unittest.main()
