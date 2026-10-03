from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .index import build_index
from .memory import Memory
from .service import RepositoryService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local Python code context and correction memory")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="Parse symbols and resolved call relationships")
    changes = commands.add_parser("changes", help="Localize tracked changes against a Git commit")
    changes.add_argument("--ref", default="HEAD")
    finder = commands.add_parser("search", help="Find candidate seeds with lexical search")
    finder.add_argument("query")
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
        service = RepositoryService(args.repo)
        if args.command == "index":
            result = build_index(args.repo).describe()
        elif args.command == "search":
            result = service.search_symbols(args.query)
        elif args.command == "changes":
            result = service.localize_changes(args.ref)
        elif args.command == "impact":
            result = service.analyze_impact(args.symbol, args.ref, args.depth)
        elif args.command == "compile":
            result = service.compile_context(args.symbol, args.ref, args.max_tokens, args.depth)
        else:
            index = build_index(args.repo)
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
