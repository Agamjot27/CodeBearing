"""Parsed-file reuse must retain full-build evidence and current graph links."""

import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from diffcontext.index import _build_python_index, build_index_from_sources


class PythonUnitTests(unittest.TestCase):
    def test_warm_json_roundtrip_skips_ast_and_matches_full_build(self):
        sources = {
            "billing.py": b"def refund(x):\n    return x\n",
            "checkout.py": b"from billing import refund as calculate\ndef checkout(x):\n    return calculate(x)\n",
        }
        units = {}
        with patch("diffcontext.index.ast.parse", wraps=ast.parse) as parse:
            cold = _build_python_index(Path.cwd(), sources, units=units)
            self.assertEqual(parse.call_count, 2)
        units = json.loads(json.dumps(units))
        with patch("diffcontext.index.ast.parse", side_effect=AssertionError("warm file reparsed")):
            warm = _build_python_index(Path.cwd(), sources, units=units)
        self.assertEqual(cold.describe(), warm.describe())
        self.assertEqual(warm.describe(), build_index_from_sources(Path.cwd(), sources).describe())
        self.assertEqual(units["checkout.py"]["calls"]["checkout.py:checkout"][0]["candidate"], "billing.refund")

    def test_edit_add_and_delete_relink_cached_callers(self):
        sources = {
            "caller.py": b"from target import work\ndef call():\n    return work()\n",
            "target.py": b"def work():\n    return 1\n",
        }
        units = {}
        _build_python_index(Path.cwd(), sources, units=units)
        # The persistence owner removes changed units after comparing byte hashes.
        sources["target.py"] = b"def replacement():\n    return 2\n"
        units.pop("target.py")
        with patch("diffcontext.index.ast.parse", wraps=ast.parse) as parse:
            edited = _build_python_index(Path.cwd(), sources, units=units)
            self.assertEqual(parse.call_count, 1)
        self.assertEqual(edited.edges["caller.py:call"], set())
        self.assertEqual(edited.describe(), build_index_from_sources(Path.cwd(), sources).describe())
        sources["target.py"] = b"def work():\n    return 3\n"
        units.pop("target.py")
        restored = _build_python_index(Path.cwd(), sources, units=units)
        self.assertEqual(restored.edges["caller.py:call"], {"target.py:work"})
        sources.pop("target.py")
        # Even a retained unused unit cannot resurrect a removed source file.
        deleted = _build_python_index(Path.cwd(), sources, units=units)
        self.assertEqual(deleted.edges["caller.py:call"], set())
        sources["new.py"] = b"def added():\n    return 4\n"
        with patch("diffcontext.index.ast.parse", wraps=ast.parse) as parse:
            added = _build_python_index(Path.cwd(), sources, units=units)
            self.assertEqual(parse.call_count, 1)
        self.assertEqual(added.describe(), build_index_from_sources(Path.cwd(), sources).describe())

    def test_cached_failures_keep_bytes_without_success_hash_and_warning_order(self):
        sources = {"bad.py": b"def ?", "invalid.py": b"\xff", "ok.py": b"def ok(): pass\n"}
        units = {}
        cold = _build_python_index(Path.cwd(), sources, ["scan warning"], units)
        with patch("diffcontext.index.ast.parse", side_effect=AssertionError("cached failure reparsed")):
            warm = _build_python_index(Path.cwd(), sources, ["scan warning"], json.loads(json.dumps(units)))
        self.assertEqual(warm.describe(), cold.describe())
        self.assertEqual(warm.sources, sources)
        self.assertEqual(set(warm.hashes), {"ok.py"})
        self.assertEqual(warm.warnings, ["scan warning", "Cannot parse bad.py: SyntaxError", "Cannot parse invalid.py: SyntaxError"])

    def test_alias_edit_and_module_collision_match_full_relinking(self):
        sources = {
            "a.py": b"def run(): pass\n",
            "b.py": b"def run(): pass\n",
            "pkg.py": b"from a import run\ndef outer():\n    return run()\n",
            "pkg/__init__.py": b"from a import run\ndef inner():\n    return run()\n",
        }
        units = {}
        _build_python_index(Path.cwd(), sources, units=units)
        sources["pkg/__init__.py"] = b"from b import run\ndef inner():\n    return run()\n"
        units.pop("pkg/__init__.py")
        with patch("diffcontext.index.ast.parse", wraps=ast.parse) as parse:
            edited = _build_python_index(Path.cwd(), sources, units=units)
            self.assertEqual(parse.call_count, 1)
        self.assertEqual(edited.edges["pkg.py:outer"], {"b.py:run"})
        self.assertEqual(edited.describe(), build_index_from_sources(Path.cwd(), sources).describe())
