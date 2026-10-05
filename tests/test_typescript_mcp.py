"""Exercise TypeScript retrieval through the actual MCP subprocess transport."""

import os
import sys
import unittest
from pathlib import Path

import test_typescript

try:
    from mcp import Client, StdioServerParameters
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

if not HAS_MCP and os.environ.get("DIFFCONTEXT_REQUIRE_MCP") == "1":
    raise RuntimeError("MCP integration is required; install the mcp extra")


@unittest.skipUnless(HAS_MCP and test_typescript.HAS_PARSERS,
                     "Install mcp and typescript extras for the TypeScript stdio test")
class TypeScriptStdioTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_typescript.TypeScriptTests.setUp
    write = test_typescript.TypeScriptTests.write
    cleanup = test_typescript.TypeScriptTests.cleanup
    refund_fixture = test_typescript.TypeScriptTests.refund_fixture

    async def test_real_stdio_typescript_search_compile_and_repository_binding(self):
        self.refund_fixture()
        project = Path(__file__).resolve().parents[1]
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "codebearing", "--repo", str(self.root), "serve"],
            cwd=project,
        )
        async with Client(parameters, read_timeout_seconds=30) as client:
            listing = await client.list_tools()
            self.assertEqual(len(listing.tools), 6)
            # Transport schemas bind requests to the startup repository; callers
            # cannot pass arbitrary filesystem roots through a retrieval tool.
            for tool in listing.tools:
                self.assertNotIn("repo", tool.input_schema["properties"])
            found = await client.call_tool("search_symbols", {"query": "refundTotal"})
            self.assertFalse(found.is_error)
            self.assertIn("billing.ts:refundTotal",
                          {row["id"] for row in found.structured_content["matches"]})
            result = await client.call_tool("compile_context", {
                "symbols": ["billing.ts:refundTotal"], "depth": 1, "max_tokens": 2000,
            })
            self.assertFalse(result.is_error)
            packet = result.structured_content
            self.assertEqual({row["id"] for row in packet["included"]}, {
                "billing.ts:refundTotal", "billing.ts:roundTotal", "checkout.ts:checkout",
            })
            self.assertIn("amounts: number[]", packet["text"])
            self.assertIn("import calculate", packet["text"])
            self.assertLessEqual(packet["estimated_tokens"], 2000)
            invalid = await client.call_tool("compile_context", {
                "symbols": ["outside.ts:notInThisRepository"],
            })
            self.assertTrue(invalid.is_error)
        self.assertFalse((self.root / ".diffcontext").exists())


if __name__ == "__main__":
    unittest.main()
