import os
import sys
import unittest
from pathlib import Path

import test_changes
import test_core

try:
    from mcp import Client, StdioServerParameters
    from diffcontext.mcp_server import create_server
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

if not HAS_MCP and os.environ.get("DIFFCONTEXT_REQUIRE_MCP") == "1":
    raise RuntimeError("MCP integration is required for this run; install the mcp extra.")


@unittest.skipUnless(HAS_MCP, "optional MCP SDK is not installed")
class MCPTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    async def test_discovery_contract_and_core_tools(self):
        async with Client(create_server(self.root)) as client:
            listing = await client.list_tools()
            names = {tool.name for tool in listing.tools}
            self.assertEqual(names, {"search_symbols", "localize_changes", "analyze_impact", "compile_context", "get_lessons", "investigate"})
            for tool in listing.tools:
                self.assertTrue(tool.annotations.read_only_hint)
                self.assertNotIn("repo", tool.input_schema["properties"])
            found = await client.call_tool("search_symbols", {"query": "refund_total"})
            self.assertFalse(found.is_error)
            self.assertTrue(found.structured_content["matches"])
            result = await client.call_tool("compile_context", {"symbols": ["refund_total"]})
            self.assertFalse(result.is_error)
            self.assertIn("def refund_total", result.structured_content["text"])
            impact = await client.call_tool("analyze_impact", {"symbols": ["refund_total"]})
            self.assertIn("checkout.py:checkout", {r["id"] for r in impact.structured_content["candidates"]})
            lessons = await client.call_tool("get_lessons", {"symbols": ["refund_total"]})
            self.assertEqual(lessons.structured_content["lessons"], [])
        self.assertFalse((self.root / ".diffcontext").exists())

    async def test_errors_and_recovery(self):
        async with Client(create_server(self.root)) as client:
            for arguments in [{}, {"symbols": ["refund_total"], "ref": "HEAD"}, {"symbols": ["missing"]}, {"symbols": ["refund_total"], "max_tokens": 127}, {"symbols": ["refund_total"], "depth": 6}]:
                result = await client.call_tool("compile_context", arguments)
                self.assertTrue(result.is_error, arguments)
            result = await client.call_tool("search_symbols", {"query": "refund", "limit": 51})
            self.assertTrue(result.is_error)
            result = await client.call_tool("compile_context", {})
            self.assertIn("Supply exactly one", str(result.content))
            result = await client.call_tool("compile_context", {"symbols": ["refund_total"]})
            self.assertFalse(result.is_error)

    async def test_memory_filtering_over_protocol(self):
        from diffcontext.index import build_index
        from diffcontext.memory import Memory
        store = Memory(self.root)
        index = build_index(self.root)
        confirmed = store.add(index, "billing.py:refund_total", "Round per item", "test_billing.py")
        store.set_status(confirmed, "confirmed")
        store.add(index, "billing.py:refund_total", "Not reviewed", "test_billing.py")
        store.close()
        db = self.root / ".diffcontext" / "memory.sqlite3"
        before = db.read_bytes()
        async with Client(create_server(self.root)) as client:
            result = await client.call_tool("get_lessons", {"symbols": ["refund_total"]})
            self.assertEqual([r["id"] for r in result.structured_content["lessons"]], [confirmed])
            self.write("test_billing.py", "# changed evidence\n")
            result = await client.call_tool("get_lessons", {"symbols": ["refund_total"]})
            self.assertEqual(result.structured_content["lessons"], [])
        self.assertEqual(db.read_bytes(), before)

    async def test_investigation_contract_and_limits(self):
        async with Client(create_server(self.root)) as client:
            result = await client.call_tool("investigate", {"task": "refund_total"})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["status"], "ready")
            self.assertEqual(result.structured_content["trace"][-1]["stage"], "stop")
            for args in [{}, {"task": "refund", "ref": "HEAD"},
                         {"symbols": ["round_line"], "max_steps": 1}]:
                invalid = await client.call_tool("investigate", args)
                self.assertTrue(invalid.is_error)
            limited = await client.call_tool("investigate", {"symbols": ["round_line"], "max_depth": 0})
            self.assertFalse(limited.is_error)
            self.assertEqual(limited.structured_content["stop_reason"], "depth_limit")
        self.assertFalse((self.root / ".diffcontext").exists())


@unittest.skipUnless(HAS_MCP, "optional MCP SDK is not installed")
class StdioTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_changes.ChangesTests.setUp
    write = test_changes.ChangesTests.write
    git = test_changes.ChangesTests.git
    cleanup = test_changes.ChangesTests.cleanup

    async def test_real_stdio_revision_context_and_error_recovery(self):
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        project = Path(__file__).resolve().parents[1]
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "diffcontext", "--repo", str(self.root), "serve"],
            cwd=project,
        )
        async with Client(parameters, read_timeout_seconds=30) as client:
            listing = await client.list_tools()
            self.assertEqual(len(listing.tools), 6)
            located = await client.call_tool("localize_changes", {"ref": "HEAD"})
            self.assertIn("billing.py:refund", located.structured_content["removed_symbols"])
            result = await client.call_tool("compile_context", {"ref": "HEAD", "max_tokens": 4000})
            self.assertFalse(result.is_error)
            self.assertIn("HISTORICAL EVIDENCE", result.structured_content["text"])
            self.assertIn("checkout.py:checkout", result.structured_content["changes"]["current_seeds"])
            failed = await client.call_tool("localize_changes", {"ref": "unknown-ref"})
            self.assertTrue(failed.is_error)
            recovered = await client.call_tool("search_symbols", {"query": "checkout"})
            self.assertFalse(recovered.is_error)
            investigation = await client.call_tool("investigate", {"ref": "HEAD"})
            self.assertFalse(investigation.is_error)
            self.assertEqual(investigation.structured_content["status"], "partial")
            self.assertIn("HISTORICAL EVIDENCE", investigation.structured_content["context"]["text"])
        self.assertFalse((self.root / ".diffcontext").exists())
