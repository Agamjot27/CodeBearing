"""Installed MCP launcher, configuration output, and model-free connection check."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

TOOLS = {"search_symbols", "localize_changes", "analyze_impact", "compile_context",
         "get_lessons", "investigate"}


def configuration(root: Path, client: str, python: str | None = None) -> str:
    """Print configuration only; never rewrite a host's existing settings."""
    # POSIX virtualenv executables are symlinks: resolving them selects the base
    # interpreter and loses this installation. Preserve the absolute venv path.
    command = str(Path(python or sys.executable).absolute())
    args = ["-m", "diffcontext.connect", "--repo", str(root.resolve())]
    # Pin the interpreter that owns this installation. GUI hosts need not inherit
    # the shell's PATH or virtual-environment activation to find our package.
    if client == "codex":
        # TOML rejects JSON's surrogate-pair escapes for non-BMP characters.
        # Emit Unicode scalars directly and escape DEL, forbidden in TOML strings.
        encode = lambda value: json.dumps(value, ensure_ascii=False).replace(chr(127), "\\u007f")
        return ("[mcp_servers.diffcontext_lab]\ncommand = " + encode(command)
                + "\nargs = " + encode(args) + "\n")
    entry = {"command": command, "args": args}
    if client == "claude":
        entry["type"] = "stdio"
    return json.dumps({"mcpServers": {"diffcontext_lab": entry}}, indent=2) + "\n"


async def check_connection(root: Path) -> dict:
    """Discover tools and run a read-only request through a separate stdio process."""
    from mcp import Client, StdioServerParameters

    parameters = StdioServerParameters(command=sys.executable,
        args=["-m", "diffcontext.connect", "--repo", str(root)])
    async with Client(parameters, read_timeout_seconds=30) as client:
        listing = await client.list_tools()
        names = {tool.name for tool in listing.tools}
        if names != TOOLS:
            raise RuntimeError(f"Unexpected tool set: {sorted(names)}")
        result = await client.call_tool("search_symbols", {"query": "__diffcontext_connection_check__"})
        if result.is_error or not isinstance(result.structured_content, dict):
            raise RuntimeError("The search tool did not return a successful structured response.")
        if "matches" not in result.structured_content:
            raise RuntimeError("The search response is missing matches.")
        return {"status": "connected", "repo": str(root), "tools": sorted(names),
                "warnings": result.structured_content.get("warnings", []),
                "scope": "MCP transport and search response; not coding-task correctness."}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="Local Python repository (Git root for revision tools)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--config", choices=["claude", "cursor", "codex"], help="Print host configuration without changing settings")
    mode.add_argument("--check", action="store_true", help="Test discovery and a search request; no model/API key needed")
    args = parser.parse_args(argv)
    try:
        root = args.repo.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"Repository directory does not exist: {root}")
        if args.config:
            if args.config == "codex" and hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            print(configuration(root, args.config), end="")
            return 0
        # Configuration and --help stay available without the optional SDK.
        try:
            from .mcp_server import create_server
        except ImportError as exc:
            raise RuntimeError('MCP dependencies unavailable. Install "diffcontext-lab[mcp]" '
                               'from your release wheel or Git source; see docs/MCP.md.') from exc
        if args.check:
            result = asyncio.run(asyncio.wait_for(check_connection(root), timeout=45))
            print(json.dumps(result, indent=2))
        else:
            create_server(root).run(transport="stdio")
        return 0
    except (ValueError, OSError, RuntimeError, TimeoutError) as exc:
        print(f"diffcontext-lab-mcp: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if not args.check:
            raise
        # SDK subprocess failures may use exception groups. Keep doctor failures
        # off stdout and return a failing exit status instead of a success banner.
        print(f"diffcontext-lab-mcp: Connection check failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
