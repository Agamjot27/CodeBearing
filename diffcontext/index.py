"""Captured-source indexing with a stdlib Python core and optional language adapters."""

from __future__ import annotations

import ast
import hashlib
import io
import tokenize
from dataclasses import asdict, dataclass, field
from pathlib import Path

EXCLUDED = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "build", "dist", ".diffcontext", "site-packages"}
MAX_FILE_BYTES = 1_000_000
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs"}


def is_source_path(relative: str) -> bool:
    """Recognize implementation files, excluding declarations and minified bundles."""
    return (Path(relative).suffix in SOURCE_SUFFIXES
            and not relative.endswith((".d.ts", ".d.mts", ".min.js", ".min.mjs")))


@dataclass
class Symbol:
    id: str
    path: str
    name: str
    module: str
    owner: str | None
    start: int
    end: int
    source: str
    preamble: str
    language: str = "python"


@dataclass
class Index:
    root: Path
    symbols: dict[str, Symbol]
    edges: dict[str, set[str]]
    warnings: list[str]
    hashes: dict[str, str]
    sources: dict[str, bytes] = field(default_factory=dict)

    def describe(self) -> dict:
        return {
            "root": str(self.root),
            "files": len(self.hashes),
            "symbols": [asdict(s) for s in self.symbols.values()],
            "edges": [{"from": a, "to": b, "kind": "calls"} for a in sorted(self.edges) for b in sorted(self.edges[a])],
            "warnings": self.warnings,
            "file_hashes": self.hashes,
        }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Use a repository-relative path without '..'.")
    if any(part in EXCLUDED for part in Path(relative).parts):
        raise ValueError("Path is inside an excluded directory.")
    if any(parent.is_symlink() for parent in [path, *path.parents] if parent != root and root in [parent, *parent.parents]):
        raise ValueError("Symbolic links are not allowed.")
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Path escapes repository root.")
    return resolved


def _body_walk(node: ast.AST):
    """Do not attribute nested definitions' calls to their enclosing function."""
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield from _body_walk(child)


def build_index(root: Path) -> Index:
    """Read current files once, then use the same parser as historical snapshots."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")
    import os
    sources = {}
    warnings = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not (Path(directory) / d).is_symlink() and not d.startswith("."))
        for filename in sorted(files):
            if not is_source_path(filename) or filename.startswith("."):
                continue
            path = Path(directory) / filename
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                warnings.append(f"Skipped symbolic link: {relative}")
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    warnings.append(f"Skipped file larger than {MAX_FILE_BYTES} bytes: {relative}")
                    continue
                sources[relative] = path.read_bytes()
            except OSError as exc:
                warnings.append(f"Cannot read {relative}: {type(exc).__name__}")
    return build_index_from_sources(root, sources, warnings)


def build_index_from_sources(root: Path, sources: dict[str, bytes], warnings: list[str] | None = None) -> Index:
    """Use one byte capture for both language adapters and historical snapshots."""
    valid = {}
    warnings = list(warnings or [])
    for relative, raw in sorted(sources.items()):
        parts = relative.split("/")
        if (not is_source_path(relative) or any(p in EXCLUDED or p.startswith(".") for p in parts)
                or Path(relative).is_absolute() or ".." in parts or "\\" in relative):
            warnings.append(f"Skipped unsupported source path: {relative}")
        elif len(raw) > MAX_FILE_BYTES:
            warnings.append(f"Skipped file larger than {MAX_FILE_BYTES} bytes: {relative}")
        else:
            valid[relative] = raw
    index = _build_python_index(root, {p: raw for p, raw in valid.items() if p.endswith(".py")}, warnings)
    web_sources = {p: raw for p, raw in valid.items() if not p.endswith(".py")}
    # Retain unparsed bytes so missing optional parsers cannot make Git changes
    # disappear. Successful parsing alone adds hashes usable as memory evidence.
    index.sources.update(web_sources)
    if web_sources:
        try:
            from .typescript import extend_index
            extend_index(index, web_sources)
        except ImportError:
            index.warnings.append("TypeScript/JavaScript parsing unavailable; install the [typescript] extra. "
                                  "Unindexed files: " + ", ".join(sorted(web_sources)))
    return index


def _build_python_index(root: Path, sources: dict[str, bytes], warnings: list[str] | None = None) -> Index:
    """Index byte snapshots without checking out or executing historical code.

    Retain source bytes even on parse failure so diff localization can disclose
    changes in invalid files. Source and hash share one read, avoiding mismatches.
    """
    root = root.resolve()
    symbols: dict[str, Symbol] = {}
    nodes = {}
    imports = {}
    qualified = {}
    warnings = list(warnings or [])
    hashes = {}
    captured = {}
    for relative, raw in sorted(sources.items()):
        parts = relative.split("/")
        if (not relative.endswith(".py") or any(p in EXCLUDED or p.startswith(".") for p in parts)
                or Path(relative).is_absolute() or ".." in parts or "\\" in relative):
            warnings.append(f"Skipped unsupported source path: {relative}")
            continue
        if len(raw) > MAX_FILE_BYTES:
            warnings.append(f"Skipped file larger than {MAX_FILE_BYTES} bytes: {relative}")
            continue
        captured[relative] = raw
        filename = parts[-1]
        try:
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
            source = raw.decode(encoding)
            tree = ast.parse(source, filename=relative)
            hashes[relative] = hashlib.sha256(raw).hexdigest()
        except (SyntaxError, UnicodeError, LookupError, ValueError) as exc:
            warnings.append(f"Cannot parse {relative}: {type(exc).__name__}")
            continue
        module = relative[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        package = module if filename == "__init__.py" else module.rpartition(".")[0]
        aliases = {}
        lines = source.splitlines()
        preamble = []
        for statement in tree.body:
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                preamble.append("\n".join(lines[statement.lineno - 1:statement.end_lineno]))
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
            elif isinstance(statement, ast.ImportFrom):
                base = statement.module or ""
                if statement.level:
                    parents = package.split(".") if package else []
                    keep = len(parents) - statement.level + 1
                    base = ".".join(parents[:max(0, keep)] + ([base] if base else []))
                for alias in statement.names:
                    if alias.name != "*":
                        aliases[alias.asname or alias.name] = ".".join(filter(None, [base, alias.name]))
        imports[module] = aliases
        definitions = []
        for statement in tree.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.append((statement, None))
            elif isinstance(statement, ast.ClassDef):
                definitions.extend((method, statement.name) for method in statement.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)))
        for node, owner in definitions:
            name = f"{owner}.{node.name}" if owner else node.name
            symbol_id = f"{relative}:{name}"
            start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            symbols[symbol_id] = Symbol(symbol_id, relative, name, module, owner, start, node.end_lineno, "\n".join(lines[start - 1:node.end_lineno]), "\n".join(preamble))
            nodes[symbol_id] = node
            qualified[f"{module}.{name}"] = symbol_id
    edges = {key: set() for key in symbols}
    for key, node in nodes.items():
        symbol = symbols[key]
        arguments = {arg.arg for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]}
        arguments.update(arg.arg for arg in [node.args.vararg, node.args.kwarg] if arg)
        # A local name shadows module imports and definitions; avoid invented edges.
        local = arguments | {n.id for n in _body_walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        local.update(n.name for n in ast.walk(node) if n is not node and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
        for call in _body_walk(node):
            if not isinstance(call, ast.Call):
                continue
            parts = []
            target = call.func
            while isinstance(target, ast.Attribute):
                parts.insert(0, target.attr)
                target = target.value
            if not isinstance(target, ast.Name):
                continue
            parts.insert(0, target.id)
            if parts[0] in {"self", "cls"} and symbol.owner and len(parts) == 2:
                candidate = f"{symbol.module}.{symbol.owner}.{parts[1]}"
            elif parts[0] in local:
                continue
            elif parts[0] in imports[symbol.module]:
                candidate = ".".join([imports[symbol.module][parts[0]], *parts[1:]])
            else:
                candidate = ".".join([symbol.module, *parts])
            if candidate in qualified:
                edges[key].add(qualified[candidate])
    return Index(root, symbols, edges, warnings, hashes, captured)


def select_symbol(index: Index, value: str) -> str:
    if value in index.symbols:
        return value
    matches = [key for key, s in index.symbols.items() if s.name == value]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError(f"Ambiguous symbol {value!r}; use one of: {', '.join(matches)}")
    raise ValueError(f"Unknown symbol: {value}")
