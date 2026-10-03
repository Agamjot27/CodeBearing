import json
import subprocess
import sys
import shutil
import unittest
import uuid
from pathlib import Path

from diffcontext.context import compile_context, estimate_tokens, impact
from diffcontext.index import build_index, safe_path, select_symbol
from diffcontext.memory import Memory


class CoreTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".test-tmp"
        scratch.mkdir(exist_ok=True)
        self.root = (scratch / uuid.uuid4().hex).resolve()
        if not self.root.is_relative_to(scratch.resolve()):
            raise RuntimeError("Test temporary directory escaped workspace.")
        self.root.mkdir()
        self.addCleanup(shutil.rmtree, self.root)
        self.write("billing.py", "def round_line(amount):\n    return round(amount, 2)\n\ndef refund_total(amounts):\n    return sum(round_line(a) for a in amounts)\n")
        self.write("checkout.py", "from billing import refund_total as calculate\n\ndef checkout(items):\n    return calculate(items)\n")
        self.write("test_billing.py", "from billing import refund_total\n\ndef test_refund():\n    assert refund_total([1]) == 1\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_callers_helpers_and_tests_with_import_alias(self):
        index = build_index(self.root)
        result = impact(index, ["refund_total"], depth=1)
        self.assertEqual({r["id"] for r in result["candidates"]}, {"billing.py:refund_total", "billing.py:round_line", "checkout.py:checkout", "test_billing.py:test_refund"})
        context = compile_context(index, ["refund_total"])
        self.assertIn("from billing import refund_total as calculate", context["text"])
        self.assertEqual(context["missing_seeds"], [])

    def test_budget_discloses_omissions_and_does_not_cut_functions(self):
        index = build_index(self.root)
        result = compile_context(index, ["refund_total"], budget=128)
        self.assertLessEqual(estimate_tokens(result["text"]), 128)
        self.assertTrue(result["omitted"])
        for row in result["included"]:
            self.assertIn(index.symbols[row["id"]].source, result["text"])
        self.write("big.py", "def huge():\n" + "    x = 'a long statement'\n" * 100)
        result = compile_context(build_index(self.root), ["huge"], budget=128)
        self.assertEqual(result["missing_seeds"], ["big.py:huge"])

    def test_ambiguous_names_fail_explicitly(self):
        self.write("other.py", "def refund_total(x):\n    return x\n")
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            select_symbol(build_index(self.root), "refund_total")

    def test_shadowing_and_nested_calls_do_not_invent_edges(self):
        self.write("shadow.py", "from billing import refund_total\n\ndef parameter(refund_total):\n    return refund_total([])\n\ndef outer():\n    def inner():\n        return refund_total([])\n    return 0\n")
        index = build_index(self.root)
        self.assertFalse(index.edges["shadow.py:parameter"])
        self.assertFalse(index.edges["shadow.py:outer"])

    def test_relative_import_and_self_method(self):
        self.write("pkg/__init__.py", "")
        self.write("pkg/helper.py", "def compute():\n    return 1\n")
        self.write("pkg/service.py", "from .helper import compute\n\nclass Service:\n    def run(self):\n        return self.work()\n    def work(self):\n        return compute()\n")
        index = build_index(self.root)
        self.assertEqual(index.edges["pkg/service.py:Service.run"], {"pkg/service.py:Service.work"})
        self.assertEqual(index.edges["pkg/service.py:Service.work"], {"pkg/helper.py:compute"})

    def test_skips_excluded_files_and_reports_syntax_failure(self):
        self.write(".venv/hidden.py", "def ignored():\n    pass\n")
        self.write("broken.py", "def ?")
        index = build_index(self.root)
        self.assertNotIn(".venv/hidden.py", index.hashes)
        self.assertTrue(any("broken.py" in warning for warning in index.warnings))
        with self.assertRaises(ValueError):
            safe_path(self.root, "../outside.py")

    def test_memory_requires_confirmation_then_invalidates_evidence(self):
        index = build_index(self.root)
        memory = Memory(self.root)
        self.addCleanup(memory.close)
        lesson_id = memory.add(index, "billing.py:refund_total", "Round per line", "test_billing.py")
        self.assertEqual(compile_context(index, ["refund_total"], lessons=memory.list())["included_lessons"], [])
        memory.set_status(lesson_id, "confirmed")
        self.assertEqual(compile_context(index, ["refund_total"], lessons=memory.list())["included_lessons"], [lesson_id])
        self.write("test_billing.py", "# Changed evidence\n")
        self.assertTrue(memory.list()[0]["stale"])
        self.assertEqual(compile_context(index, ["refund_total"], lessons=memory.list())["included_lessons"], [])
        with self.assertRaisesRegex(ValueError, "Evidence changed"):
            memory.set_status(lesson_id, "confirmed")

    def test_memory_scope_change_also_invalidates(self):
        index = build_index(self.root)
        memory = Memory(self.root)
        self.addCleanup(memory.close)
        lesson_id = memory.add(index, "billing.py:refund_total", "Round per line", "test_billing.py")
        memory.set_status(lesson_id, "confirmed")
        self.write("billing.py", "def refund_total(x):\n    return 0\n")
        self.assertTrue(memory.list()[0]["stale"])
        self.assertEqual(memory.list({"checkout.py:checkout"}), [])

    def test_cli_roundtrip_and_actionable_error(self):
        result = subprocess.run([sys.executable, "-m", "diffcontext", "--repo", str(self.root), "compile", "--symbol", "refund_total"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("billing.py:refund_total", [r["id"] for r in json.loads(result.stdout)["included"]])
        result = subprocess.run([sys.executable, "-m", "diffcontext", "--repo", str(self.root), "impact", "--symbol", "missing"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown symbol", result.stderr)


if __name__ == "__main__":
    unittest.main()
