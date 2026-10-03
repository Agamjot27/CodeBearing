"""Model-free stdio demonstration: discover, search, then compile one seed."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters


async def demonstrate(repo: Path, query: str):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "diffcontext", "--repo", str(repo.resolve()), "serve"],
    )
    async with Client(parameters, read_timeout_seconds=30) as client:
        listing = await client.list_tools()
        found = await client.call_tool("search_symbols", {"query": query})
        if found.is_error:
            raise RuntimeError(str(found.content))
        matches = found.structured_content["matches"]
        if not matches:
            raise ValueError("No matches; try another query.")
        # Selecting the first lexical match is only a transport demo. An assistant
        # should inspect candidates and warnings before choosing task evidence.
        seed = matches[0]["id"]
        compiled = await client.call_tool("compile_context", {"symbols": [seed], "max_tokens": 2000})
        if compiled.is_error:
            raise RuntimeError(str(compiled.content))
        print(json.dumps({"tools": [tool.name for tool in listing.tools], "seed": seed,
                          "context": compiled.structured_content}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--query", default="refund_total")
    arguments = parser.parse_args()
    asyncio.run(demonstrate(arguments.repo, arguments.query))
