"""Presentation must shorten diagnostics without changing repository evidence."""

import copy
import json
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

import test_core
import test_changes
from codebearing.service import RepositoryService

try:
    from mcp import Client, StdioServerParameters
    from codebearing.mcp_server import create_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

if not HAS_MCP and os.environ.get("DIFFCONTEXT_REQUIRE_MCP") == "1":
    raise RuntimeError("MCP integration is required; install the mcp extra")


class PresentationTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_distinct_ranking_diagnostics_are_bounded_without_dropping_rows(self):
        from codebearing.presentation import present_report

        report = RepositoryService(self.root).investigate(task="refund_total")
        rows = [{"id": f"symbol-{n}", "score": n / 100, "distance": n % 3,
                 "lesson_ids": [n, n + 100],
                 "reasons": [f"reason-{n}-{j}:" + "x" * 1000 for j in range(20)],
                 "signals": {"lexical": n, "graph": .5, "lesson_ids": [n],
                             "matched_terms": {"body": [f"term-{n}-{j}:" + "z" * 100 for j in range(30)]}}}
                for n in range(40)]
        report["search_matches"] = copy.deepcopy(rows)
        report["context"]["retrieval"]["candidates"] = copy.deepcopy(rows)
        report["trace"].insert(0, {"stage": "localize", "matches": copy.deepcopy(rows[:-1])})
        before = copy.deepcopy(report)
        compact = present_report(report)
        fields = {field["path"]: field for field in compact["presentation"]["fields"]}
        for path, actual in (("search_matches", compact["search_matches"]),
                             ("context.retrieval.candidates", compact["context"]["retrieval"]["candidates"]),
                             ("trace[0].matches", compact["trace"][0]["matches"])):
            self.assertEqual([row["id"] for row in actual], [row["id"] for row in rows[:len(actual)]])
            for position, row in enumerate(actual):
                original = rows[position]
                for key in ("id", "score", "distance", "lesson_ids"):
                    self.assertEqual(row[key], original[key])
                for key in ("lexical", "graph", "lesson_ids"):
                    self.assertEqual(row["signals"][key], original["signals"][key])
                self.assertEqual(len(row["reasons"]), 8)
                self.assertTrue(all(len(reason) <= 160 for reason in row["reasons"]))
                self.assertEqual(row["signals"]["matched_terms"]["body"],
                                 [term[:80] for term in original["signals"]["matched_terms"]["body"][:8]])
                for suffix, values, shown in (("reasons", original["reasons"], row["reasons"]),
                                             ("signals.matched_terms.body", original["signals"]["matched_terms"]["body"], row["signals"]["matched_terms"]["body"])):
                    counts = fields[f"{path}[{position}].{suffix}"]
                    self.assertEqual(counts["total"], len(values))
                    self.assertEqual(counts["omitted"], len(values) - len(shown))
                    self.assertEqual(counts["omitted_chars"], sum(map(len, values)) - sum(map(len, shown)))
        self.assertEqual(compact["context"]["text"], report["context"]["text"])
        self.assertEqual(compact["verification"], report["verification"])
        self.assertEqual(report, before)
        self.assertIs(present_report(report, "full"), report)
        self.assertLess(len(json.dumps(compact)), len(json.dumps(report)) // 3)

    def test_small_ranking_diagnostics_remain_exact(self):
        from codebearing.presentation import present_report

        report = RepositoryService(self.root).investigate(task="refund_total")
        compact = present_report(report)
        self.assertEqual(compact["search_matches"], report["search_matches"])
        self.assertEqual(compact["context"]["retrieval"], report["context"]["retrieval"])

    def test_null_context_stops_preserve_original_status(self):
        from codebearing.presentation import present_report

        report = RepositoryService(self.root).investigate(task="zzzzunfindable")
        self.assertEqual(report["stop_reason"], "no_matches")
        self.assertIsNone(report["context"])
        compact = present_report(report)
        for key in ("status", "stop_reason", "context", "verification", "search_matches"):
            self.assertEqual(compact[key], report[key])

    def test_search_symbols_matches_receive_same_ranking_policy(self):
        from codebearing.presentation import present_report

        report = RepositoryService(self.root).search_symbols("refund_total")
        row = report["matches"][0]
        row["reasons"] = [f"reason-{n}" + "x" * 300 for n in range(15)]
        row["signals"]["matched_terms"] = {"body": [f"term-{n}" for n in range(20)]}
        before = copy.deepcopy(report)
        compact = present_report(report)
        self.assertEqual(compact["matches"][0]["id"], row["id"])
        self.assertEqual(compact["matches"][0]["score"], row["score"])
        self.assertEqual(len(compact["matches"][0]["reasons"]), 8)
        self.assertEqual(len(compact["matches"][0]["signals"]["matched_terms"]["body"]), 8)
        fields = {field["path"]: field for field in compact["presentation"]["fields"]}
        self.assertEqual(fields["matches[0].reasons"]["omitted"], 7)
        self.assertEqual(fields["matches[0].signals.matched_terms.body"]["omitted"], 12)
        self.assertEqual(report, before)
        self.assertEqual(present_report(report, "full"), before)

    def test_warning_flood_is_bounded_without_mutating_full_report(self):
        from codebearing.presentation import present_report

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
        from codebearing.presentation import present_report

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
        from codebearing.presentation import present_report

        report = RepositoryService(self.root).investigate(symbols=["round_line"])
        verifications = [row for row in report["trace"] if row["stage"] == "verify"]
        self.assertNotEqual(verifications[0]["frontier"], report["verification"]["frontier"])
        compact = present_report(report)
        first = next(row for row in compact["trace"] if row["stage"] == "verify")
        self.assertEqual(first["frontier"], verifications[0]["frontier"])

    def test_serialized_context_and_gaps_precede_long_search_diagnostics(self):
        from codebearing.presentation import present_report

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

    async def test_mcp_no_matches_is_needs_input_not_tool_error(self):
        direct = RepositoryService(self.root).investigate(task="zzzzunfindable")
        async with Client(create_server(self.root)) as client:
            response = await client.call_tool("investigate", {"task": "zzzzunfindable"})
        self.assertFalse(response.is_error)
        report = response.structured_content
        self.assertEqual(report["status"], "needs_input")
        self.assertEqual(report["stop_reason"], "no_matches")
        self.assertIsNone(report["context"])
        self.assertEqual(report["verification"], direct["verification"])

    async def test_mcp_ranking_diagnostics_preserve_both_channels_and_full_detail(self):
        report = RepositoryService(self.root).investigate(task="refund_total")
        row = report["search_matches"][0]
        row["reasons"] = ["unique-reason-" + str(n) + "x" * 400 for n in range(20)]
        row["signals"]["matched_terms"] = {"body": ["term-" + str(n) for n in range(30)]}
        before = copy.deepcopy(report)
        # Exercise the actual SDK dictionary serialization while isolating the
        # presentation input from task ranking changes tested in its own suite.
        with patch.object(RepositoryService, "investigate", return_value=report):
            async with Client(create_server(self.root)) as client:
                compact_result = await client.call_tool("investigate", {"task": "refund_total"})
                full_result = await client.call_tool("investigate", {"task": "refund_total", "detail": "full"})
        self.assertFalse(compact_result.is_error)
        self.assertFalse(full_result.is_error)
        compact = compact_result.structured_content
        text_channel = "\n".join(item.text for item in compact_result.content
                                 if getattr(item, "type", None) == "text")
        self.assertEqual(json.loads(text_channel), compact)
        self.assertEqual(compact["context"]["text"], report["context"]["text"])
        self.assertEqual(compact["search_matches"][0]["id"], row["id"])
        self.assertEqual(len(compact["search_matches"][0]["reasons"]), 8)
        self.assertEqual(full_result.structured_content, before)
        self.assertEqual(report, before)

    async def test_real_stdio_warning_flood_and_explicit_full_response(self):
        for number in range(240):
            self.write(f"unrelated/broken_{number:04d}.py", "def broken(:\n")
        direct = RepositoryService(self.root).investigate(symbols=["refund_total"])
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "codebearing.connect", "--repo", str(self.root)],
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
