"""Opt-in cache lifecycle through the installed-launcher protocol boundary."""

import json
import os
import sys
import unittest
from pathlib import Path

import test_core
from diffcontext.connect import configuration

try:
    from mcp import Client, StdioServerParameters
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
if not HAS_MCP and os.environ.get("DIFFCONTEXT_REQUIRE_MCP") == "1":
    raise RuntimeError("Install the required mcp extra")


class CacheConfigurationTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_generated_configuration_preserves_cache_choice_without_writes(self):
        for client in ("claude", "cursor"):
            entry = json.loads(configuration(self.root, client, cache=True))["mcpServers"]["diffcontext_lab"]
            self.assertEqual(entry["args"][-1], "--cache")
            self.assertEqual(entry["args"][-2], str(self.root.resolve()))
        codex = configuration(self.root, "codex", cache=True)
        self.assertIn('"--cache"', codex)
        self.assertFalse((self.root / ".diffcontext").exists())


@unittest.skipUnless(HAS_MCP, "Install the MCP extra")
class CacheProtocolTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    async def test_cache_reuse_and_edit_refresh_over_real_stdio(self):
        parameters = StdioServerParameters(command=sys.executable,
            args=["-m", "diffcontext.connect", "--repo", str(self.root), "--cache"],
            cwd=Path(__file__).resolve().parents[1])
        async with Client(parameters, read_timeout_seconds=30) as client:
            first = await client.call_tool("search_symbols", {"query": "refund_total"})
            self.assertFalse(first.is_error)
            self.assertEqual(first.structured_content["indexing"]["parsed_files"], 3)
            second = await client.call_tool("compile_context", {"symbols": ["billing.py:refund_total"]})
            self.assertFalse(second.is_error)
            self.assertEqual(second.structured_content["indexing"]["reused_files"], 3)
            self.write("billing.py", "def refund_total(amounts):\n    return sum(amounts)\n")
            third = await client.call_tool("compile_context", {"symbols": ["billing.py:refund_total"]})
            self.assertFalse(third.is_error)
            self.assertEqual(third.structured_content["indexing"]["parsed_files"], 1)
            self.assertIn("return sum(amounts)", third.structured_content["text"])
            self.assertNotIn("billing.py:round_line", {row["id"] for row in third.structured_content["included"]})
        self.assertTrue((self.root / ".diffcontext" / "index.sqlite3").exists())
        self.assertFalse((self.root / ".diffcontext" / "memory.sqlite3").exists())
