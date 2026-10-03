import json
import shutil
import stat
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

from diffcontext.changes import changes_impact, compile_changes, localize_changes
from diffcontext.context import estimate_tokens
from diffcontext.index import build_index
from diffcontext.memory import Memory


class ChangesTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".test-tmp"
        scratch.mkdir(exist_ok=True)
        self.root = (scratch / uuid.uuid4().hex).resolve()
        if not self.root.is_relative_to(scratch.resolve()):
            raise RuntimeError("Unsafe fixture cleanup path")
        self.root.mkdir()
        self.addCleanup(self.cleanup)
        self.git("init", "-q")
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n\ndef refund(x):\n    return helper(x)\n")
        self.write("checkout.py", "from billing import refund\n\ndef checkout(x):\n    return refund(x)\n")
        self.write("test_billing.py", "from billing import refund\n\ndef test_refund():\n    assert refund(1) == 2\n")
        self.write(".gitignore", ".diffcontext/\n")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture baseline")

    def cleanup(self):
        # Git object files are read-only on Windows. Retry only fixture-contained
        # paths after clearing that flag; never apply this to the project checkout.
        def retry(function, path, error):
            if not Path(path).resolve().is_relative_to(self.root):
                raise RuntimeError("Cleanup target escaped Git fixture")
            Path(path).chmod(stat.S_IWRITE | stat.S_IREAD)
            function(path)
        shutil.rmtree(self.root, onerror=retry)

    def git(self, *args):
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, name, source):
        (self.root / name).write_text(source, encoding="utf-8")

    def test_modified_function_maps_coordinates_and_expands_callers(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n\ndef refund(x):\n    return helper(x) + 1\n")
        change = localize_changes(self.root)
        self.assertIn("billing.py:refund", change.report["current_seeds"])
        self.assertIn("billing.py:refund", change.report["historical_seeds"])
        self.assertEqual(change.report["files"][0]["hunks"][0]["new"], {"start": 7, "count": 1})
        self.assertIn("checkout.py:checkout", {r["id"] for r in changes_impact(change)["current"]["candidates"]})

    def test_deleted_function_retains_prior_source_and_current_callers(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        change = localize_changes(self.root)
        self.assertIn("billing.py:refund", change.report["removed_symbols"])
        self.assertIn("checkout.py:checkout", change.report["current_seeds"])
        context = compile_changes(change)
        self.assertIn("HISTORICAL EVIDENCE", context["text"])
        self.assertIn("def refund(x)", context["text"])
        self.assertIn("def checkout(x)", context["text"])

    def test_deleted_file_can_compile_with_historical_seeds_only(self):
        for path in self.root.glob("*.py"):
            path.unlink()
        change = localize_changes(self.root)
        self.assertFalse(change.report["current_seeds"])
        self.assertTrue(change.report["historical_seeds"])
        self.assertIn("def refund(x)", compile_changes(change)["text"])

    def test_stage_new_file_and_disclose_untracked(self):
        self.write("new file.py", "def added():\n    return 1\n")
        before = localize_changes(self.root)
        self.assertEqual(before.report["excluded_untracked"], ["new file.py"])
        self.assertFalse(before.report["current_seeds"])
        self.git("add", "new file.py")
        after = localize_changes(self.root)
        self.assertIn("new file.py:added", after.report["current_seeds"])
        self.assertEqual(after.report["files"][0]["status"], "added")

    def test_constant_change_falls_back_and_reports_missing_module_context(self):
        self.write("billing.py", "RATE = 3\n\ndef helper(x):\n    return x * RATE\n\ndef refund(x):\n    return helper(x)\n")
        change = localize_changes(self.root)
        self.assertTrue(change.report["files"][0]["fallback"])
        self.assertIn("billing.py:helper", change.report["current_seeds"])
        self.assertIn("billing.py:refund", change.report["current_seeds"])
        self.assertTrue(change.report["unresolved"])
        self.assertFalse(compile_changes(change)["complete"])

    def test_deleted_statement_does_not_mark_next_function_removed(self):
        self.write("billing.py", "\ndef helper(x):\n    return x * 2\n\ndef refund(x):\n    return helper(x)\n")
        change = localize_changes(self.root)
        self.assertEqual(change.report["removed_symbols"], [])
        self.assertTrue(change.report["files"][0]["fallback"])

    def test_staged_and_unstaged_changes_compared_to_selected_commit(self):
        self.write("checkout.py", "from billing import refund\n\ndef checkout(x):\n    return refund(x) + 1\n")
        self.git("add", "checkout.py")
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n\ndef refund(x):\n    return helper(x) + 2\n")
        change = localize_changes(self.root, "HEAD")
        self.assertEqual({r["path"] for r in change.report["files"]}, {"checkout.py", "billing.py"})

    def test_staged_deletion_with_leftover_disk_file_is_not_resurrected(self):
        self.git("rm", "--cached", "billing.py")
        change = localize_changes(self.root)
        self.assertNotIn("billing.py:refund", change.current.symbols)
        self.assertIn("billing.py:refund", change.report["removed_symbols"])
        self.assertIn("billing.py", change.report["excluded_untracked"])

    def test_syntax_errors_and_non_python_changes_are_unresolved(self):
        self.write("settings.json", '{"rate": 2}')
        self.git("add", "settings.json")
        self.write("billing.py", "def ?")
        change = localize_changes(self.root)
        self.assertEqual({r["path"] for r in change.report["unresolved"]}, {"settings.json", "billing.py"})
        self.assertFalse(compile_changes(change)["complete"])

    def test_shared_budget_discloses_missing_historical_seeds(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        change = localize_changes(self.root)
        for budget in [128, 256, 600, 4000]:
            result = compile_changes(change, budget)
            self.assertLessEqual(estimate_tokens(result["text"]), budget)
        self.assertTrue(compile_changes(change, 128)["historical"]["missing_seeds"])

    def test_no_changes_invalid_revision_and_subdirectory(self):
        change = localize_changes(self.root)
        self.assertEqual(change.report["files"], [])
        self.assertTrue(compile_changes(change)["complete"])
        for revision in ["missing-ref", "--output=unexpected"]:
            with self.assertRaises(ValueError):
                localize_changes(self.root, revision)
        sub = self.root / "sub"
        sub.mkdir()
        with self.assertRaisesRegex(ValueError, "repository root"):
            localize_changes(sub)

    def test_cli_changes_impact_and_compile(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        for command in ["changes", "impact", "compile"]:
            result = subprocess.run([sys.executable, "-m", "diffcontext", "--repo", str(self.root), command, "--ref", "HEAD"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            report = payload if command == "changes" else payload["changes"]
            self.assertIn("billing.py:refund", report["removed_symbols"])

    def test_rename_is_explicit_delete_plus_add(self):
        self.git("mv", "billing.py", "renamed.py")
        change = localize_changes(self.root)
        self.assertEqual({r["status"] for r in change.report["files"]}, {"added", "deleted"})
        self.assertIn("billing.py:refund", change.report["removed_symbols"])
        self.assertIn("renamed.py:refund", change.report["current_seeds"])

    def test_import_change_seeds_file_and_warns(self):
        self.write("checkout.py", "from billing import helper as refund\n\ndef checkout(x):\n    return refund(x)\n")
        change = localize_changes(self.root)
        self.assertIn("checkout.py:checkout", change.report["current_seeds"])
        self.assertTrue(change.report["unresolved"])

    def test_memory_is_used_only_for_current_evidence(self):
        memory = Memory(self.root)
        index = build_index(self.root)
        lesson_id = memory.add(index, "billing.py:refund", "Review the invoice rounding", "test_billing.py")
        memory.set_status(lesson_id, "confirmed")
        self.write("checkout.py", "from billing import refund\n\ndef checkout(x):\n    return refund(x) + 1\n")
        change = localize_changes(self.root)
        context = compile_changes(change, lessons=memory.list())
        memory.close()
        self.assertIn(lesson_id, context["current"]["included_lessons"])
        self.assertEqual(context["historical"]["included_lessons"], [])

    def test_non_git_root_and_invalid_depth_fail(self):
        sub = self.root / "elsewhere"
        sub.mkdir()
        with self.assertRaises(ValueError):
            localize_changes(sub)
        change = localize_changes(self.root)
        with self.assertRaisesRegex(ValueError, "Depth"):
            compile_changes(change, depth=-1)


if __name__ == "__main__":
    unittest.main()
