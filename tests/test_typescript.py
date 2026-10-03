"""Conservative JS/TS graph regressions; no target Node code is executed."""

import importlib.util
import os
import shutil
import stat
import subprocess
import unittest
import uuid
from pathlib import Path

from diffcontext.changes import compile_changes, localize_changes
from diffcontext.context import compile_context, estimate_tokens
from diffcontext.index import build_index, build_index_from_sources
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService


HAS_PARSERS = all(importlib.util.find_spec(name) is not None for name in (
    "tree_sitter", "tree_sitter_javascript", "tree_sitter_typescript"))
if os.environ.get("DIFFCONTEXT_REQUIRE_TYPESCRIPT") == "1" and not HAS_PARSERS:
    raise RuntimeError("Required TypeScript parser dependencies are missing")


@unittest.skipUnless(HAS_PARSERS, "Install the typescript extra to exercise language adapters")
class TypeScriptTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / ".test-tmp"
        scratch.mkdir(exist_ok=True)
        self.root = (scratch / uuid.uuid4().hex).resolve()
        if not self.root.is_relative_to(scratch.resolve()):
            raise RuntimeError("Fixture path escaped workspace")
        self.root.mkdir()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        # Git makes object files read-only on Windows; only clear fixture flags.
        def retry(function, path, error):
            if not Path(path).resolve().is_relative_to(self.root):
                raise RuntimeError("Cleanup escaped fixture")
            Path(path).chmod(stat.S_IWRITE | stat.S_IREAD)
            function(path)
        shutil.rmtree(self.root, onerror=retry)

    def write(self, name, source):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def git(self, *args):
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def refund_fixture(self):
        self.write("billing.ts", "export function roundTotal(amount: number): number {\n  return Math.round(amount * 100) / 100;\n}\n\nexport default function refundTotal(amounts: number[]): number {\n  return roundTotal(amounts.reduce((total, amount) => total + amount, 0));\n}\n")
        self.write("checkout.ts", "import calculate, { roundTotal as round } from './billing.js';\nimport * as billing from './billing';\nexport const checkout = (items: number[]) => calculate(items);\nexport function named(amount: number) { return round(amount); }\nexport function namespace(amount: number) { return billing.roundTotal(amount); }\n")

    def test_named_default_namespace_imports_and_arrow_symbols(self):
        self.refund_fixture()
        index = build_index(self.root)
        self.assertEqual(index.edges["billing.ts:refundTotal"], {"billing.ts:roundTotal"})
        self.assertEqual(index.edges["checkout.ts:checkout"], {"billing.ts:refundTotal"})
        self.assertEqual(index.edges["checkout.ts:named"], {"billing.ts:roundTotal"})
        self.assertEqual(index.edges["checkout.ts:namespace"], {"billing.ts:roundTotal"})
        self.assertEqual(index.symbols["checkout.ts:checkout"].language, "typescript")
        packet = compile_context(index, ["billing.ts:refundTotal"], budget=2000, depth=1)
        self.assertEqual({row["id"] for row in packet["included"]}, {
            "billing.ts:refundTotal", "billing.ts:roundTotal", "checkout.ts:checkout"})
        self.assertIn("from './billing.js'", packet["text"])
        self.assertLessEqual(estimate_tokens(packet["text"]), 2000)

    def test_same_class_this_methods(self):
        self.write("service.ts", "class Service {\n  run(amount: number) { return this.work(amount); }\n  work(amount: number) { return amount; }\n}\n")
        index = build_index(self.root)
        self.assertEqual(index.edges["service.ts:Service.run"], {"service.ts:Service.work"})
        self.assertFalse(index.edges["service.ts:Service.work"])

    def test_named_expression_and_reassigned_bindings_never_target_original(self):
        self.write("helper.ts", "export function target() { return 1; }\n")
        self.write("bindings.ts", "import { target } from './helper';\nexport const expression = function target() { return target(); };\nexport function localClass() { class target {} return target(); }\n")
        self.write("mutated.ts", "function original() { return 1; }\nlet alias = () => original();\nalias = () => 2;\nexport function caller() { return alias(); }\n")
        index = build_index(self.root)
        self.assertFalse(index.edges["bindings.ts:expression"])
        self.assertFalse(index.edges["bindings.ts:localClass"])
        self.assertFalse(index.edges["mutated.ts:caller"])

    def test_shadowing_and_nested_calls_never_invent_edges(self):
        self.write("helper.ts", "export function target() { return 1; }\n")
        self.write("shadow.ts", "import { target } from './helper';\nexport function parameter(target: () => number) { return target(); }\nexport function local() { const target = () => 2; return target(); }\nexport function destructured(input: any) { const { target } = input; return target(); }\nexport function outer() { function inner() { return target(); } return 0; }\nexport function callback() { return [1].map(() => target()); }\nexport function direct() { return target(); }\n")
        index = build_index(self.root)
        for name in ("parameter", "local", "destructured", "outer", "callback"):
            self.assertFalse(index.edges[f"shadow.ts:{name}"], name)
        self.assertEqual(index.edges["shadow.ts:direct"], {"helper.ts:target"})
        self.assertNotIn("shadow.ts:inner", index.symbols)

    def test_jsx_and_utf8_preserve_lines_without_component_edges(self):
        self.write("view.tsx", "// café 💡\nexport function Child() { return <span>été</span>; }\n\nexport const View = () => <Child />;\n")
        self.write("plain.jsx", "export function Widget() { return <div>hello</div>; }\n")
        index = build_index(self.root)
        child = index.symbols["view.tsx:Child"]
        self.assertEqual((child.start, child.end), (2, 2))
        self.assertIn("été", child.source)
        self.assertNotIn("café", child.source)
        self.assertFalse(index.edges["view.tsx:View"])
        self.assertEqual(index.symbols["plain.jsx:Widget"].language, "javascript")

    def test_all_supported_extensions_and_ignored_artifacts(self):
        for extension in ("ts", "tsx", "js", "jsx", "mts", "mjs"):
            self.write(f"source.{extension}", "export function example() { return 1; }\n")
        self.write("node_modules/pkg/hidden.ts", "export function hidden() {}\n")
        self.write("types.d.ts", "export declare function declaration(): number;\n")
        index = build_index(self.root)
        self.assertEqual(len(index.symbols), 6)
        self.assertNotIn("types.d.ts", index.sources)
        self.assertNotIn("node_modules/pkg/hidden.ts", index.sources)

    def test_parse_failure_keeps_bytes_but_no_hash_or_partial_symbols(self):
        raw = b"export function valid() { return 1; }\nexport function broken( {\n"
        (self.root / "broken.ts").write_bytes(raw)
        index = build_index(self.root)
        self.assertEqual(index.sources["broken.ts"], raw)
        self.assertNotIn("broken.ts", index.hashes)
        self.assertFalse(index.symbols)
        self.assertTrue(any("broken.ts" in warning for warning in index.warnings))

    def test_external_imports_are_disclosed_without_fabricated_edges(self):
        self.write("external.ts", "import { missing } from 'not-installed';\nexport function run() { return missing(); }\n")
        index = build_index(self.root)
        self.assertFalse(index.edges["external.ts:run"])
        self.assertTrue(any("external.ts" in warning for warning in index.warnings))

    def test_ambiguous_relative_modules_and_reexports_are_not_guessed(self):
        self.write("helper.ts", "export function target() { return 1; }\n")
        self.write("helper.js", "export function target() { return 2; }\n")
        self.write("barrel.ts", "export { target } from './helper.ts';\n")
        self.write("consumer.ts", "import { target } from './helper';\nimport { target as indirect } from './barrel';\nexport function ambiguous() { return target(); }\nexport function reexported() { return indirect(); }\n")
        index = build_index(self.root)
        self.assertFalse(index.edges["consumer.ts:ambiguous"])
        self.assertFalse(index.edges["consumer.ts:reexported"])
        self.assertTrue(any("re-export" in warning for warning in index.warnings))

    def test_invalid_utf8_and_anonymous_default_exports_are_disclosed(self):
        (self.root / "invalid.js").write_bytes(b"// \xff\nexport function valid() {}\n")
        self.write("anonymous.ts", "export default () => 1;\n")
        index = build_index(self.root)
        self.assertNotIn("invalid.js", index.hashes)
        self.assertIn("invalid.js", index.sources)
        self.assertFalse(index.symbols)
        self.assertTrue(any("UTF-8" in warning for warning in index.warnings))
        self.assertTrue(any("default export" in warning for warning in index.warnings))

    def test_disk_snapshot_parity_and_python_language_default(self):
        self.refund_fixture()
        self.write("worker.py", "def work():\n    return 1\n")
        disk = build_index(self.root)
        snapshot = build_index_from_sources(self.root, disk.sources)
        self.assertEqual(snapshot.describe(), disk.describe())
        self.assertEqual(disk.symbols["worker.py:work"].language, "python")

    def test_shared_service_and_memory_freshness(self):
        self.refund_fixture()
        self.write("evidence.ts", "export function checkRefund() { return true; }\n")
        memory = Memory(self.root)
        self.addCleanup(memory.close)
        lesson = memory.add(build_index(self.root), "billing.ts:refundTotal", "Round the final total", "evidence.ts")
        memory.set_status(lesson, "confirmed")
        service = RepositoryService(self.root)
        packet = service.compile_context(symbols=["billing.ts:refundTotal"])
        self.assertIn(lesson, packet["included_lessons"])
        investigation = service.investigate(symbols=["billing.ts:refundTotal"])
        self.assertIn(investigation["status"], {"ready", "partial"})
        self.write("evidence.ts", "export function checkRefund() { return false; }\n")
        packet = service.compile_context(symbols=["billing.ts:refundTotal"])
        self.assertNotIn(lesson, packet["included_lessons"])
        self.assertTrue(packet["excluded_lessons"][0]["stale"])

    def test_git_deleted_function_recovers_historical_source_and_surviving_caller(self):
        self.refund_fixture()
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture baseline")
        self.write("billing.ts", "export function roundTotal(amount: number): number {\n  return Math.round(amount * 100) / 100;\n}\n")
        changed = localize_changes(self.root)
        self.assertIn("billing.ts:refundTotal", changed.report["removed_symbols"])
        self.assertIn("checkout.ts:checkout", changed.report["current_seeds"])
        packet = compile_changes(changed)
        self.assertIn("HISTORICAL EVIDENCE", packet["text"])
        self.assertIn("function refundTotal", packet["text"])
        self.assertIn("const checkout", packet["text"])


if __name__ == "__main__":
    unittest.main()
