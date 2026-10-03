"""Packing priorities and task retrieval through the actual user interfaces."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import test_core
import test_typescript
from diffcontext.context import compile_context, estimate_tokens, search
from diffcontext.index import build_index
from diffcontext.memory import Memory
from diffcontext.service import RepositoryService

try:
    from mcp import Client, StdioServerParameters
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


class HybridPackingTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def confirm(self, lesson):
        index = build_index(self.root)
        store = Memory(self.root)
        try:
            identifier = store.add(index, "billing.py:refund_total", lesson, "billing.py")
            store.set_status(identifier, "confirmed")
            return identifier
        finally:
            store.close()

    def test_reserve_preserves_lesson_when_all_code_would_exhaust_budget(self):
        identifier = self.confirm("Refund rounding must remain consistent")
        index = build_index(self.root)
        budget = estimate_tokens(compile_context(index, ["refund_total"], 4000, 1)["text"])
        service = RepositoryService(self.root)
        old = service.investigate(task="refund_total", max_tokens=budget, max_depth=1, retrieval="legacy")["context"]
        new = service.investigate(task="refund_total", max_tokens=budget, max_depth=1)["context"]
        self.assertNotIn(identifier, old["included_lessons"])
        self.assertIn(identifier, new["included_lessons"])
        self.assertFalse(new["missing_seeds"])
        self.assertTrue(new["omitted"])
        self.assertLessEqual(estimate_tokens(new["text"]), budget)

    def test_optional_lesson_never_hides_seed_that_fits_full_budget(self):
        self.write("billing.py", "def refund_total(amounts):\n    return '" + "x" * 420 + "'\n")
        identifier = self.confirm("Refund")
        index = build_index(self.root)
        budget = estimate_tokens(compile_context(index, ["refund_total"], 4000, 0)["text"])
        packet = RepositoryService(self.root).investigate(task="refund_total", max_tokens=budget, max_depth=0)["context"]
        self.assertFalse(packet["missing_seeds"])
        self.assertIn("billing.py:refund_total", {row["id"] for row in packet["included"]})
        self.assertNotIn(identifier, packet["included_lessons"])
        self.assertLessEqual(estimate_tokens(packet["text"]), budget)

    def test_cli_exposes_hybrid_and_legacy_choice(self):
        command = [sys.executable, "-m", "diffcontext", "--repo", str(self.root), "investigate", "--task", "refund total", "--summary"]
        for policy in ("hybrid", "legacy"):
            result = subprocess.run([*command, "--retrieval", policy], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["retrieval"]["policy"], policy)
            self.assertEqual(bool(summary["seeds"]["current"]), policy == "hybrid")


@unittest.skipUnless(HAS_MCP and test_typescript.HAS_PARSERS, "Install MCP and typescript extras")
class HybridStdioTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_typescript.TypeScriptTests.setUp
    cleanup = test_typescript.TypeScriptTests.cleanup
    write = test_typescript.TypeScriptTests.write
    refund_fixture = test_typescript.TypeScriptTests.refund_fixture

    async def test_natural_language_typescript_task_and_policy_over_stdio(self):
        self.refund_fixture()
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "diffcontext.connect", "--repo", str(self.root)],
            cwd=Path(__file__).resolve().parents[1])
        async with Client(parameters, read_timeout_seconds=30) as client:
            listing = await client.list_tools()
            self.assertEqual(len(listing.tools), 6)
            search_tool = next(tool for tool in listing.tools if tool.name == "search_symbols")
            self.assertEqual(search_tool.input_schema["properties"]["retrieval"]["enum"], ["hybrid", "legacy"])
            found = await client.call_tool("search_symbols", {"query": "refund total"})
            self.assertFalse(found.is_error)
            self.assertEqual(found.structured_content["matches"][0]["id"], "billing.ts:refundTotal")
            run = await client.call_tool("investigate", {"task": "refund total", "max_tokens": 2000, "max_depth": 1})
            self.assertFalse(run.is_error)
            packet = run.structured_content["context"]
            self.assertEqual(run.structured_content["retrieval"]["policy"], "hybrid")
            self.assertIn("billing.ts:refundTotal", {row["id"] for row in packet["included"]})
            self.assertLessEqual(packet["estimated_tokens"], 2000)
            baseline = await client.call_tool("investigate", {"task": "refund total", "retrieval": "legacy"})
            self.assertFalse(baseline.is_error)
            self.assertEqual(baseline.structured_content["retrieval"]["policy"], "legacy")
            self.assertEqual(baseline.structured_content["search_matches"], search(build_index(self.root), "refund total", 50))
        self.assertFalse((self.root / ".diffcontext").exists())
