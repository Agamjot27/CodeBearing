"""Presentation must shorten diagnostics without changing repository evidence."""

import copy
import json
import os
import sys
import unittest
from pathlib import Path

import test_core
import test_changes
from diffcontext.service import RepositoryService

try:
    from mcp import Client, StdioServerParameters
    from diffcontext.mcp_server import create_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

if not HAS_MCP and os.environ.get("DIFFCONTEXT_REQUIRE_MCP") == "1":
    raise RuntimeError("MCP integration is required; install the mcp extra")


class PresentationTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_warning_flood_is_bounded_without_mutating_full_report(self):
        from diffcontext.presentation import present_report

        report = RepositoryService(self.root).investigate(symbols=["refund_total"])
        # Repeated warnings across capture/compile/verification caused the actual
        # trial overflow. Long diagnostics verify sampling by example count.
        warnings = [f"broken-{n}.py: " + "unresolved parser diagnostic " * 100
                    for n in range(600)]
        report["context"]["warnings"] = warnings + [
            "Static calls only: dynamic dispatch can be missing."]
        report["verification"]["index_warnings"] = warnings
        report["status"] = "partial"
        report["stop_reason"] = "index_warnings"
        for event in report["trace"]:
            if event["stage"] == "capture":
                event["warnings"] = warnings
            elif event["stage"] == "verify":
                event["index_warnings"] = warnings
        before = copy.deepcopy(report)
        compact = present_report(report)
        self.assertEqual(report, before)
        self.assertEqual(present_report(report, detail="full"), before)
        self.assertEqual(compact["context"]["text"], before["context"]["text"])
        self.assertEqual(compact["status"], "partial")
        self.assertEqual(compact["stop_reason"], "index_warnings")
        self.assertIn("Static calls only: dynamic dispatch can be missing.",
                      compact["context"]["warnings"])
        self.assertLess(len(json.dumps(compact).encode()), 100000)
        disclosure = compact["presentation"]
        self.assertEqual(disclosure["detail"], "compact")
        self.assertIn("full", disclosure["full_detail"])
        fields = {row["path"]: row for row in disclosure["fields"]}
        self.assertEqual(fields["verification.index_warnings"]["total"], 600)
        self.assertGreater(fields["verification.index_warnings"]["omitted"], 0)

    def test_coverage_gaps_and_budget_evidence_survive_compaction(self):
        from diffcontext.presentation import present_report

        service = RepositoryService(self.root)
        for arguments in ({"symbols": ["round_line"], "max_depth": 0},
                          {"symbols": ["refund_total"], "max_tokens": 128}):
            report = service.investigate(**arguments)
            report["verification"]["unresolved_changes"] = [
                {"path": "settings.ts", "reason": "Configuration requires inspection"}]
            report["verification"]["excluded_untracked"] = ["new_test.py"]
            compact = present_report(report)
            self.assertEqual(compact["context"]["text"], report["context"]["text"])
            self.assertEqual(compact["status"], report["status"])
            self.assertEqual(compact["stop_reason"], report["stop_reason"])
            for key in ("frontier", "missing_seeds", "omitted", "unresolved_changes", "excluded_untracked"):
                self.assertEqual(compact["verification"][key], report["verification"][key], key)
            self.assertEqual(compact["context"]["omitted"], report["context"]["omitted"])
            self.assertEqual(compact["trace"][-1]["stage"], "stop")

    def test_distinct_trace_evidence_is_not_replaced_by_a_false_reference(self):
        from diffcontext.presentation import present_report

        report = RepositoryService(self.root).investigate(symbols=["round_line"])
        verifications = [row for row in report["trace"] if row["stage"] == "verify"]
        self.assertNotEqual(verifications[0]["frontier"], report["verification"]["frontier"])
        compact = present_report(report)
        first = next(row for row in compact["trace"] if row["stage"] == "verify")
        self.assertEqual(first["frontier"], verifications[0]["frontier"])

    def test_serialized_context_and_gaps_precede_long_search_diagnostics(self):
        from diffcontext.presentation import present_report

        report = RepositoryService(self.root).investigate(task="refund_total")
        original_order = list(report)
        self.assertLess(original_order.index("search_matches"), original_order.index("context"))
        before = copy.deepcopy(report)
        compact = present_report(report)
        # Hosts may truncate rendered JSON. Put the selected source and coverage
        # caveats before ranking diagnostics, while leaving full export stable.
        serialized_order = list(json.loads(json.dumps(compact)))
        for important in ("context", "verification"):
            for diagnostic in ("search_matches", "trace"):
                self.assertLess(serialized_order.index(important),
                                serialized_order.index(diagnostic))
        self.assertEqual(compact["context"], report["context"])
        self.assertEqual(compact["verification"], report["verification"])
        self.assertEqual(report, before)
        self.assertEqual(list(report), original_order)
        self.assertEqual(list(present_report(report, detail="full")), original_order)


@unittest.skipUnless(HAS_MCP, "optional MCP SDK is not installed")
class PresentationProtocolTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    async def test_real_stdio_warning_flood_and_explicit_full_response(self):
        for number in range(240):
            self.write(f"unrelated/broken_{number:04d}.py", "def broken(:\n")
        direct = RepositoryService(self.root).investigate(symbols=["refund_total"])
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "diffcontext.connect", "--repo", str(self.root)],
            cwd=Path(__file__).resolve().parents[1])
        async with Client(parameters, read_timeout_seconds=30) as client:
            compact_result = await client.call_tool("investigate", {"symbols": ["refund_total"]})
            full_result = await client.call_tool("investigate", {"symbols": ["refund_total"], "detail": "full"})
            self.assertFalse(compact_result.is_error)
            self.assertFalse(full_result.is_error)
            compact = compact_result.structured_content
            full = full_result.structured_content
            self.assertEqual(compact["context"]["text"], direct["context"]["text"])
            self.assertEqual(full["context"], direct["context"])
            self.assertEqual(full["verification"], direct["verification"])
            self.assertEqual(compact["stop_reason"], "index_warnings")
            # Both SDK channels remain useful to clients: shorten metadata in the
            # report rather than remove source from content-only clients.
            text_channel = "\n".join(item.text for item in compact_result.content
                                     if getattr(item, "type", None) == "text")
            self.assertIn("def refund_total", text_channel)
            rendered_order = list(json.loads(text_channel))
            self.assertLess(rendered_order.index("context"), rendered_order.index("search_matches"))
            self.assertLess(rendered_order.index("verification"), rendered_order.index("trace"))
            compact_wire = len(compact_result.model_dump_json().encode())
            full_wire = len(full_result.model_dump_json().encode())
            self.assertLess(compact_wire, full_wire // 3)
            self.assertLess(compact_wire, 60000)
            fields = {row["path"]: row for row in compact["presentation"]["fields"]}
            self.assertEqual(fields["verification.index_warnings"]["total"], 240)
            for name, arguments in (("search_symbols", {"query": "refund_total"}),
                                    ("compile_context", {"symbols": ["refund_total"]}),
                                    ("analyze_impact", {"symbols": ["refund_total"]}),
                                    ("get_lessons", {"symbols": ["refund_total"]})):
                result = await client.call_tool(name, {**arguments, "detail": "full"})
                self.assertFalse(result.is_error, name)
                expected = getattr(RepositoryService(self.root), name)(**arguments)
                self.assertEqual(result.structured_content, expected, name)
        self.assertFalse((self.root / ".diffcontext").exists())


@unittest.skipUnless(HAS_MCP, "optional MCP SDK is not installed")
class PresentationRevisionTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_changes.ChangesTests.setUp
    write = test_changes.ChangesTests.write
    git = test_changes.ChangesTests.git
    cleanup = test_changes.ChangesTests.cleanup

    async def test_revision_labels_gaps_and_full_localization_are_preserved(self):
        self.write("billing.py", "RATE = 3\n\ndef helper(x):\n    return x * RATE\n")
        service = RepositoryService(self.root)
        expected = service.compile_context(ref="HEAD")
        async with Client(create_server(self.root)) as client:
            compact_result = await client.call_tool("compile_context", {"ref": "HEAD"})
            full_result = await client.call_tool("compile_context", {"ref": "HEAD", "detail": "full"})
            self.assertFalse(compact_result.is_error)
            self.assertFalse(full_result.is_error)
            compact = compact_result.structured_content
            self.assertEqual(compact["text"], expected["text"])
            self.assertIn("HISTORICAL EVIDENCE", compact["text"])
            self.assertIn("CURRENT EVIDENCE", compact["text"])
            self.assertEqual(compact["changes"]["unresolved"], expected["changes"]["unresolved"])
            self.assertFalse(compact["complete"])
            for version in ("current", "historical"):
                for key in ("included", "omitted", "missing_seeds"):
                    self.assertEqual(compact[version][key], expected[version][key])
            self.assertEqual(full_result.structured_content, expected)
            localized = await client.call_tool("localize_changes", {"ref": "HEAD", "detail": "full"})
            self.assertFalse(localized.is_error)
            self.assertEqual(localized.structured_content, service.localize_changes("HEAD"))


if __name__ == "__main__":
    unittest.main()
