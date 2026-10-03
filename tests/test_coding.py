import json
import unittest
from pathlib import Path

import test_core
from diffcontext.coding import apply_edits, calibrate, grade, load_suite, source_hashes, trial_workspace


SUITE = Path(__file__).resolve().parents[1] / "evals" / "coding_tasks" / "suite.json"


class CodingTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_all_fixture_bugs_fail_and_references_pass(self):
        report = calibrate(load_suite(SUITE), self.root / "trials")
        self.assertTrue(report["passed"], report)
        self.assertEqual(len(report["tasks"]), 3)
        self.assertEqual(list((self.root / "trials").iterdir()), [])

    def test_copy_excludes_grading_material_and_edits_are_atomic(self):
        task = load_suite(SUITE)[0]
        with trial_workspace(task, self.root / "trials") as root:
            self.assertFalse((root / "checks.py").exists())
            self.assertFalse((root / "reference.json").exists())
            before = source_hashes(root)
            for edits in [{"../escape.py": ""}, {"test_public.py": ""},
                          {"refunds.py": "changed", "invoice.py": "changed"}, {"refunds.py": 1}]:
                with self.assertRaises(ValueError):
                    apply_edits(task, root, edits)
                self.assertEqual(source_hashes(root), before)
            apply_edits(task, root, {"refunds.py": "def refund_total(:\n"})
            self.assertEqual(grade(task, root)["outcome"], "test_failed")

    def test_candidate_loop_times_out_and_fresh_copy_remains_buggy(self):
        task = load_suite(SUITE)[0]
        with trial_workspace(task, self.root / "trials") as root:
            apply_edits(task, root, {"refunds.py": "while True:\n    pass\n"})
            self.assertEqual(grade(task, root, timeout=0.2)["outcome"], "timeout")
        with trial_workspace(task, self.root / "trials") as root:
            self.assertEqual(grade(task, root)["outcome"], "test_failed")

    def test_task_directory_and_test_edit_validation(self):
        manifest = self.root / "suite.json"
        data = json.loads(SUITE.read_text(encoding="utf-8"))
        data["tasks"][0]["directory"] = "../outside"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "below"):
            load_suite(manifest)
