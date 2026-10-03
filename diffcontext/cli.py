from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .context import compile_context, impact, search
from .index import build_index
from .memory import Memory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local Python code context and correction memory")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="Parse symbols and resolved call relationships")
    finder = commands.add_parser("search", help="Find candidate seeds with lexical search")
    finder.add_argument("query")
    for command in ["impact", "compile"]:
        sub = commands.add_parser(command)
        sub.add_argument("--symbol", action="append", required=True)
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
        index = build_index(args.repo)
        if args.command == "index":
            result = index.describe()
        elif args.command == "search":
            result = {"matches": search(index, args.query), "warnings": index.warnings}
        elif args.command == "impact":
            result = impact(index, args.symbol, args.depth)
        elif args.command == "compile":
            candidates = impact(index, args.symbol, args.depth)
            lessons = []
            if (index.root / ".diffcontext" / "memory.sqlite3").exists():
                store = Memory(index.root)
                try:
                    lessons = store.list({r["id"] for r in candidates["candidates"]})
                finally:
                    store.close()
            result = compile_context(index, args.symbol, args.max_tokens, args.depth, lessons)
            result["excluded_lessons"] = [{"id": r["id"], "status": r["status"], "stale": r["stale"]} for r in lessons if r["status"] != "confirmed" or r["stale"]]
        else:
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
