from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .index import build_index
from .memory import Memory
from .service import RepositoryService
from .runs import load_summary, summarize


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local code context and correction memory (optional TypeScript/JavaScript)")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cache", action="store_true", help="Persist/reuse local parse facts in .diffcontext/index.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="Parse symbols and resolved call relationships")
    commands.add_parser("serve", help="Run read-only MCP tools over stdio (requires the mcp extra)")
    changes = commands.add_parser("changes", help="Localize tracked changes against a Git commit")
    changes.add_argument("--ref", default="HEAD")
    finder = commands.add_parser("search", help="Find candidate seeds with lexical search")
    finder.add_argument("query")
    finder.add_argument("--retrieval", choices=["hybrid", "legacy"], default="hybrid", help="Task ranking policy; legacy preserves the original overlap baseline")
    investigator = commands.add_parser("investigate", help="Gather context with bounded expansion and a run trace")
    selector = investigator.add_mutually_exclusive_group(required=True)
    selector.add_argument("--task", help="Lexical task description; inspect the selected seeds")
    selector.add_argument("--symbol", action="append")
    selector.add_argument("--ref")
    investigator.add_argument("--max-tokens", type=int, default=4000)
    investigator.add_argument("--max-depth", type=int, default=3)
    investigator.add_argument("--max-steps", type=int, default=7)
    investigator.add_argument("--max-seconds", type=float, default=30)
    investigator.add_argument("--summary", action="store_true", help="Show decisions/citations without source text")
    investigator.add_argument("--retrieval", choices=["hybrid", "legacy"], default="hybrid")
    inspector = commands.add_parser("inspect", help="Summarize a full investigation JSON saved by the caller")
    inspector.add_argument("run_file", type=Path)
    for command in ["impact", "compile"]:
        sub = commands.add_parser(command)
        selector = sub.add_mutually_exclusive_group(required=True)
        selector.add_argument("--symbol", action="append")
        selector.add_argument("--ref", help="Compare this commit with the tracked working tree")
        sub.add_argument("--depth", type=int, default=2)
        if command == "compile":
            sub.add_argument("--max-tokens", type=int, default=4000)
    memory = commands.add_parser("memory")
    actions = memory.add_subparsers(dest="action", required=True)
    add = actions.add_parser("add", help="Record a proposed lesson")
    add.add_argument("--scope", required=True)
    add.add_argument("--lesson", required=True)
    add.add_argument("--evidence", required=True)
    actions.add_parser("list")
    status = actions.add_parser("status", help="Explicit developer review of a lesson")
    status.add_argument("id", type=int)
    status.add_argument("status", choices=["confirmed", "superseded", "disputed"])
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            # Import only at the transport boundary: all ordinary CLI commands
            # must keep working when the optional SDK is not installed.
            try:
                from .mcp_server import create_server
            except ImportError as exc:
                raise ValueError('MCP dependencies are missing; install with: python -m pip install -e ".[mcp]"') from exc
            create_server(args.repo, cache=args.cache).run(transport="stdio")
            return 0
        if args.command == "inspect":
            print(json.dumps(load_summary(args.run_file), indent=2, ensure_ascii=True))
            return 0
        service = RepositoryService(args.repo, cache=args.cache)
        if args.command == "index":
            result = build_index(args.repo, cache=args.cache).describe()
        elif args.command == "search":
            result = service.search_symbols(args.query, retrieval=args.retrieval)
        elif args.command == "changes":
            result = service.localize_changes(args.ref)
        elif args.command == "impact":
            result = service.analyze_impact(args.symbol, args.ref, args.depth)
        elif args.command == "compile":
            result = service.compile_context(args.symbol, args.ref, args.max_tokens, args.depth)
        elif args.command == "investigate":
            result = service.investigate(args.task, args.symbol, args.ref, args.max_tokens,
                                         args.max_depth, args.max_steps, args.max_seconds, args.retrieval)
            # Policy only affects task localization/packing; explicit and Git
            # selectors preserve their original context behavior.
            if args.summary:
                result = summarize(result)
        else:
            index = build_index(args.repo, cache=args.cache)
            store = Memory(index.root)
            try:
                if args.action == "add":
                    result = {"id": store.add(index, args.scope, args.lesson, args.evidence), "status": "proposed"}
                elif args.action == "status":
                    store.set_status(args.id, args.status)
                    result = {"id": args.id, "status": args.status}
                else:
                    result = {"lessons": store.list()}
            finally:
                store.close()
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"diffcontext: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
