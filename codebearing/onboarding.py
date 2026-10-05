"""CodeBearing's user entry point; advanced commands delegate to the core CLI."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from .connect import check_connection, configuration


def prepare_config(root: Path, client: str, *, cache: bool = False) -> tuple[Path, bytes, bytes | None]:
    """Validate a project-only merge before connecting or writing anything."""
    relative = {"claude": ".mcp.json", "cursor": ".cursor/mcp.json", "codex": ".codex/config.toml"}[client]
    target = root / relative
    for path in [target, *target.parents]:
        if path == root.parent:
            break
        if path.is_symlink():
            raise ValueError("Assistant configuration path must not be a symlink.")
    before = target.read_bytes() if target.exists() else None
    old = before.decode("utf-8-sig") if before is not None else ""
    generated = configuration(root, client, cache=cache)
    if client == "codex":
        try:
            import tomllib
        except ImportError as exc:
            raise ValueError("Automatic Codex setup needs Python 3.11+. Use codebearing-mcp --config codex on Python 3.10.") from exc
        parsed = tomllib.loads(old)
        desired = tomllib.loads(generated)["mcp_servers"]["codebearing"]
        servers = parsed.get("mcp_servers", {})
        if not isinstance(servers, dict):
            raise ValueError("Existing mcp_servers must be a table.")
        existing = servers.get("codebearing")
        if existing is not None:
            if existing != desired:
                raise ValueError("An existing CodeBearing entry differs. Update it manually with codebearing-mcp --config codex.")
            return target, before, before
        # Append a new table to preserve user comments and unrelated formatting.
        # Parse the result too: inline-table configurations can forbid extension.
        merged = old.rstrip() + ("\n\n" if old.strip() else "") + generated
        after = tomllib.loads(merged)
        if after["mcp_servers"]["codebearing"] != desired:
            raise ValueError("Could not safely add CodeBearing to the existing TOML.")
        return target, merged.encode("utf-8"), before
    parsed = json.loads(old) if old.strip() else {}
    if not isinstance(parsed, dict):
        raise ValueError("Assistant configuration must be a JSON object.")
    servers = parsed.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("Existing mcpServers must be an object.")
    desired = json.loads(generated)["mcpServers"]["codebearing"]
    if "codebearing" in servers:
        if servers["codebearing"] != desired:
            raise ValueError("An existing CodeBearing entry differs. Update it manually with codebearing-mcp --config " + client + ".")
        return target, before, before
    servers["codebearing"] = desired
    return target, (json.dumps(parsed, indent=2, ensure_ascii=False) + "\n").encode("utf-8"), before


def save_config(root: Path, target: Path, contents: bytes, before: bytes | None):
    # Revalidate after the connection check: user/editor changes must not be
    # overwritten by a previously prepared merge. Only known project paths pass.
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Assistant configuration escaped the selected project.")
    if (target.read_bytes() if target.exists() else None) != before:
        raise ValueError("Assistant settings changed during setup. Rerun setup.")
    if contents == before:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(contents)
        # Keep all unrelated settings; publication is atomic, never a partial JSON.
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"setup", "--help", "-h"}:
        from .cli import main as core_main
        return core_main(args)
    parser = argparse.ArgumentParser(prog="codebearing", description="Relevant code and correction memory for your coding assistant.")
    commands = parser.add_subparsers(dest="command")
    setup = commands.add_parser("setup", help="Connect this project to Claude Code, Cursor or Codex")
    setup.add_argument("--client", choices=["claude", "cursor", "codex"], required=True)
    setup.add_argument("--repo", type=Path, default=Path.cwd())
    setup.add_argument("--cache", action="store_true", help="Opt into persistent parse reuse")
    parsed = parser.parse_args(args)
    if parsed.command is None:
        parser.print_help()
        return 0
    try:
        root = parsed.repo.expanduser().resolve()
        if not root.is_dir():
            raise ValueError("Select an existing project directory with --repo.")
        target, contents, before = prepare_config(root, parsed.client, cache=parsed.cache)
        # Do not write a setup entry if the installed server cannot actually
        # launch/respond. This is a protocol check, not an assistant-host claim.
        result = asyncio.run(asyncio.wait_for(check_connection(root, cache=parsed.cache), timeout=45))
        save_config(root, target, contents, before)
        print("CodeBearing is connected to your project.")
        print("Settings: " + str(target))
        print(f"Verified {len(result['tools'])} MCP tools. Open/restart {parsed.client} in this project and enable/approve CodeBearing.")
        print('Try: "Use CodeBearing to investigate my task before editing code. Explain relevant functions, dependencies and lessons."')
        return 0
    except Exception as exc:
        print(f"CodeBearing setup: {exc}", file=sys.stderr)
        return 2
