"""Optional, snapshot-only TypeScript/JavaScript call-graph adapter.

Only direct local/relative-ESM calls and same-class ``this.method`` calls are
resolved. This is syntax evidence, not type checking or runtime dispatch analysis.
"""

from __future__ import annotations

import hashlib
import posixpath
from dataclasses import dataclass, field

from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_typescript

from .index import Index, Symbol

FUNCTIONS = {"function_declaration", "generator_function_declaration", "function_expression", "generator_function", "arrow_function", "method_definition"}
BOUNDARIES = FUNCTIONS | {"class_declaration", "class", "class_expression"}
SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mts", ".mjs")


@dataclass
class _File:
    raw: bytes
    root: object
    language: str
    preamble: str
    definitions: dict = field(default_factory=dict)
    exports: dict = field(default_factory=dict)
    imports: dict = field(default_factory=dict)
    duplicate_names: set = field(default_factory=set)
    duplicate_exports: set = field(default_factory=set)
    unsafe_bindings: set = field(default_factory=set)

    def text(self, node):
        return self.raw[node.start_byte:node.end_byte].decode("utf-8") if node else ""


def _walk(node):
    yield node
    for child in node.named_children:
        yield from _walk(child)


def _body_walk(node):
    """Skip nested executable scopes and type syntax, including callback bodies."""
    if node.type in BOUNDARIES or node.type.startswith("jsx_"):
        return
    if node.type in {"type_annotation", "type_arguments", "type_parameters", "interface_declaration", "type_alias_declaration"}:
        return
    yield node
    for child in node.named_children:
        yield from _body_walk(child)


def _bindings(file, node):
    """Extract binding names, never object property keys or annotation names."""
    if node is None:
        return set()
    if node.type in {"identifier", "shorthand_property_identifier_pattern"}:
        return {file.text(node)}
    if node.type in {"required_parameter", "optional_parameter"}:
        return _bindings(file, node.child_by_field_name("pattern"))
    if node.type in {"pair_pattern", "assignment_pattern", "object_assignment_pattern"}:
        return _bindings(file, node.child_by_field_name("value") or node.child_by_field_name("left"))
    if node.type in {"formal_parameters", "object_pattern", "array_pattern", "rest_pattern"}:
        result = set()
        for child in node.named_children:
            result.update(_bindings(file, child))
        return result
    return set()


def _shadowed(file, node):
    names = _bindings(file, node.child_by_field_name("parameters"))
    names.update(_bindings(file, node.child_by_field_name("parameter")))
    if node.type in {"function_expression", "generator_function"}:
        # The expression's private recursive name belongs to this scope, not
        # to a same-named declaration elsewhere in the module.
        names.update(_bindings(file, node.child_by_field_name("name")))
    # Block-scoped bindings are intentionally treated as function-wide. This
    # sacrifices some valid edges rather than guessing scope and inventing calls.
    def visit(current):
        if current.type in BOUNDARIES:
            declaration_name = current.child_by_field_name("name")
            if declaration_name and declaration_name.type in {"identifier", "type_identifier"}:
                names.add(file.text(declaration_name))
            return
        if current.type == "variable_declarator":
            names.update(_bindings(file, current.child_by_field_name("name")))
        elif current.type in {"assignment_expression", "augmented_assignment_expression"}:
            # Reassigned callable bindings no longer have a dependable target.
            names.update(_bindings(file, current.child_by_field_name("left")))
        elif current.type == "catch_clause":
            names.update(_bindings(file, current.child_by_field_name("parameter")))
        for child in current.named_children:
            visit(child)
    body = node.child_by_field_name("body")
    if body:
        visit(body)
    return names


def _put_export(file, exported, local, path, warnings):
    if exported in file.duplicate_exports:
        return
    if exported in file.exports and file.exports[exported] != local:
        warnings.append(f"Ambiguous ESM export {exported!r}: {path}")
        file.exports.pop(exported, None)
        file.duplicate_exports.add(exported)
    else:
        file.exports[exported] = local


def _definitions(file, declaration):
    """Yield (name, owner, executable node, complete excerpt node)."""
    name = declaration.child_by_field_name("name")
    if declaration.type in {"function_declaration", "generator_function_declaration"} and name:
        yield file.text(name), None, declaration, declaration
    elif declaration.type in {"lexical_declaration", "variable_declaration"}:
        for variable in declaration.named_children:
            if variable.type != "variable_declarator":
                continue
            name = variable.child_by_field_name("name")
            value = variable.child_by_field_name("value")
            if name and name.type == "identifier" and value and value.type in FUNCTIONS:
                yield file.text(name), None, value, declaration
    elif declaration.type == "class_declaration" and name:
        owner = file.text(name)
        body = declaration.child_by_field_name("body")
        for method in body.named_children if body else []:
            method_name = method.child_by_field_name("name")
            if (method.type == "method_definition" and method.child_by_field_name("body")
                    and method_name and method_name.type in {"property_identifier", "identifier"}):
                yield f"{owner}.{file.text(method_name)}", owner, method, method


def _imports(file, statement, path, warnings):
    source = statement.child_by_field_name("source")
    if not source:
        warnings.append(f"Unsupported import syntax: {path}")
        return
    # Grammar exposes type-only keywords as anonymous tokens, not named nodes.
    if any(child.type == "type" for child in statement.children):
        return
    module = file.text(source)[1:-1]
    clause = next((child for child in statement.named_children if child.type == "import_clause"), None)
    if not clause:
        return
    if not module.startswith("."):
        warnings.append(f"Unresolved package/alias import {module!r}: {path}")
    for child in clause.named_children:
        entries = []
        if child.type == "identifier":
            entries.append((file.text(child), "default"))
        elif child.type == "namespace_import":
            entries.append((file.text(child.named_children[0]), "*"))
        elif child.type == "named_imports":
            for specifier in child.named_children:
                if specifier.type != "import_specifier" or any(token.type == "type" for token in specifier.children):
                    continue
                original = specifier.child_by_field_name("name")
                local = specifier.child_by_field_name("alias") or original
                entries.append((file.text(local), file.text(original)))
        for local, exported in entries:
            if local in file.imports:
                file.imports[local] = None
                warnings.append(f"Ambiguous import binding {local!r}: {path}")
            else:
                file.imports[local] = (module, exported)


def _resolve_module(path, module, files):
    if not module.startswith(".") or "\\" in module:
        return None
    base = posixpath.normpath(posixpath.join(posixpath.dirname(path), module))
    if base.startswith("../") or base in {"..", "/"} or base.startswith("/"):
        return None
    # TypeScript commonly imports './file.js' while the captured source is .ts.
    candidates = [base]
    if base.endswith((".js", ".jsx", ".mjs")):
        stem = base.rsplit(".", 1)[0]
        candidates += [stem + suffix for suffix in (".ts", ".tsx", ".mts")]
    elif not base.endswith(SUFFIXES):
        candidates += [base + suffix for suffix in SUFFIXES]
        candidates += [base + "/index" + suffix for suffix in SUFFIXES]
    matches = [candidate for candidate in candidates if candidate in files]
    # Exact paths win; ambiguous extensionless matches are never guessed.
    if base in files:
        return base
    return matches[0] if len(matches) == 1 else None


def extend_index(index: Index, sources: dict[str, bytes]) -> Index:
    """Extend a validated captured Index; never read files or execute target code."""
    parsers = {
        "typescript": Parser(Language(tree_sitter_typescript.language_typescript())),
        "tsx": Parser(Language(tree_sitter_typescript.language_tsx())),
        "javascript": Parser(Language(tree_sitter_javascript.language())),
    }
    files = {}
    for path, raw in sorted(sources.items()):
        index.sources[path] = raw
        language = "typescript" if path.endswith((".ts", ".tsx", ".mts")) else "javascript"
        try:
            raw.decode("utf-8")
        except UnicodeError:
            index.warnings.append(f"Cannot parse {path}: invalid UTF-8")
            continue
        root = parsers["tsx" if path.endswith(".tsx") else language].parse(raw).root_node
        if root.has_error:
            index.warnings.append(f"Cannot parse {path}: tree-sitter syntax errors")
            continue
        imports = [raw[n.start_byte:n.end_byte].decode("utf-8") for n in root.named_children if n.type == "import_statement"]
        file = _File(raw, root, language, "\n".join(imports))
        files[path] = file
        index.hashes[path] = hashlib.sha256(raw).hexdigest()
        for statement in root.named_children:
            if statement.type == "import_statement":
                _imports(file, statement, path, index.warnings)
                continue
            exported = statement.type == "export_statement"
            if exported and any(child.type == "type" for child in statement.children):
                continue
            declaration = statement.child_by_field_name("declaration") if exported else statement
            if exported and statement.child_by_field_name("source"):
                index.warnings.append(f"Unsupported ESM re-export: {path}")
                continue
            if declaration:
                definitions = list(_definitions(file, declaration))
                for name, owner, node, excerpt in definitions:
                    if name in file.definitions or name in file.duplicate_names:
                        file.definitions.pop(name, None)
                        file.duplicate_names.add(name)
                        index.warnings.append(f"Ambiguous duplicate definition {name!r}: {path}")
                        continue
                    file.definitions[name] = (owner, node, statement if exported and owner is None else excerpt)
                if exported:
                    is_default = any(child.type == "default" for child in statement.children)
                    for name, owner, _, _ in definitions:
                        if owner is None:
                            _put_export(file, "default" if is_default else name, name, path, index.warnings)
                    if not definitions and is_default:
                        index.warnings.append(f"Unsupported anonymous/default export: {path}")
            if exported:
                clause = next((n for n in statement.named_children if n.type == "export_clause"), None)
                if clause:
                    for specifier in clause.named_children:
                        if any(token.type == "type" for token in specifier.children):
                            continue
                        name = specifier.child_by_field_name("name")
                        alias = specifier.child_by_field_name("alias") or name
                        if name:
                            _put_export(file, file.text(alias), file.text(name), path, index.warnings)
                value = statement.child_by_field_name("value")
                if value and value.type == "identifier":
                    _put_export(file, "default", file.text(value), path, index.warnings)
                elif value:
                    index.warnings.append(f"Unsupported anonymous/default export: {path}")
        if any(n.type == "call_expression" and file.text(n.child_by_field_name("function")) == "require" for n in _walk(root)):
            index.warnings.append(f"Unsupported CommonJS require: {path}")
        if any(n.type in {"jsx_element", "jsx_self_closing_element"} for n in _walk(root)):
            index.warnings.append(f"Unsupported JSX component/reference resolution: {path}")
        # A module-level reassignment can replace a captured callable before a
        # later invocation. Keep its source searchable, but never resolve calls
        # against that binding as if its initial value remained authoritative.
        for item in _body_walk(root):
            if item.type in {"assignment_expression", "augmented_assignment_expression"}:
                file.unsafe_bindings.update(_bindings(file, item.child_by_field_name("left")))
        if file.unsafe_bindings:
            index.warnings.append(f"Reassigned module bindings are not resolved ({', '.join(sorted(file.unsafe_bindings))}): {path}")

    for path, file in files.items():
        for name, (owner, node, excerpt) in file.definitions.items():
            key = f"{path}:{name}"
            index.symbols[key] = Symbol(key, path, name, path.rsplit(".", 1)[0].replace("/", "."), owner,
                                        excerpt.start_point.row + 1, excerpt.end_point.row + 1,
                                        file.text(excerpt), file.preamble, language=file.language)
            index.edges[key] = set()
    for path, file in files.items():
        for name, (owner, node, _) in file.definitions.items():
            key = f"{path}:{name}"
            shadowed = _shadowed(file, node)
            unresolved = 0
            body = node.child_by_field_name("body")
            for call in _body_walk(body) if body else []:
                if call.type != "call_expression":
                    continue
                target = call.child_by_field_name("function")
                target_path, target_name = path, None
                if target and target.type == "identifier":
                    local = file.text(target)
                    if local not in shadowed and local not in file.unsafe_bindings:
                        if local in file.imports and file.imports[local]:
                            module, exported = file.imports[local]
                            target_path = _resolve_module(path, module, files)
                            target_name = files[target_path].exports.get(exported) if target_path else None
                        elif local not in file.imports:
                            target_name = local
                elif target and target.type == "member_expression":
                    receiver = target.child_by_field_name("object")
                    property_node = target.child_by_field_name("property")
                    member = file.text(property_node)
                    if receiver and receiver.type == "this" and owner and property_node and property_node.type == "property_identifier":
                        # Static methods and instance methods are distinct runtime
                        # receivers; do not claim a cross-kind 'this' dispatch.
                        target_name = f"{owner}.{member}"
                        other = file.definitions.get(target_name)
                        static = lambda n: any(c.type == "static" for c in n.children)
                        if other and static(node) != static(other[1]):
                            target_name = None
                    elif receiver and receiver.type == "identifier" and file.text(receiver) not in shadowed and file.text(receiver) not in file.unsafe_bindings:
                        binding = file.imports.get(file.text(receiver))
                        if binding and binding[1] == "*" and property_node and property_node.type == "property_identifier":
                            target_path = _resolve_module(path, binding[0], files)
                            target_name = files[target_path].exports.get(member) if target_path else None
                candidate = f"{target_path}:{target_name}"
                if target_path in files and target_name in files[target_path].unsafe_bindings:
                    target_name = None
                if target_name and candidate in index.symbols:
                    index.edges[key].add(candidate)
                else:
                    unresolved += 1
            if unresolved:
                index.warnings.append(f"Unresolved calls ({unresolved}) in {key}; dynamic/type/JSX dispatch is not modeled")
    return index
