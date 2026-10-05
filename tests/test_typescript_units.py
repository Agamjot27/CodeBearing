"""Portable parse facts must skip parsing without preserving obsolete edges."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from codebearing.index import Index

try:
    from tree_sitter import Parser as RealParser
    from codebearing.typescript import extend_index
except ImportError:
    extend_index = None


@unittest.skipIf(extend_index is None, "optional TypeScript parser extra unavailable")
class TypeScriptUnitTests(unittest.TestCase):
    def build(self, sources, units=None):
        return extend_index(Index(Path.cwd(), {}, {}, [], {}), sources, units)

    def parser_spy(self):
        calls = []

        class CountingParser:
            def __init__(self, language):
                self.parser = RealParser(language)

            def parse(self, raw):
                calls.append(raw)
                return self.parser.parse(raw)

        return calls, patch("codebearing.typescript.Parser", CountingParser)

    def test_json_roundtrip_warm_units_skip_parser_and_preserve_output(self):
        sources = {
            "a.ts": b"export function target(){return 1;} export default target;",
            "b.ts": b'import first, {target as alias} from "./a"; import * as ns from "./a"; export const run=()=>{first();alias();ns.target(); missing();};',
            "view.tsx": b'export const view=()=> <div title="caf\xc3\xa9"/>;',
            "invalid.ts": b"export function broken( {",
            "encoding.js": b"\xff",
        }
        units = {}
        calls, spy = self.parser_spy()
        with spy:
            cold = self.build(sources, units)
        self.assertEqual(len(calls), 4)
        portable = json.loads(json.dumps(units))
        calls, spy = self.parser_spy()
        with spy:
            warm = self.build(sources, portable)
        self.assertEqual(calls, [])
        self.assertEqual(cold.describe(), warm.describe())
        self.assertEqual(cold.sources, warm.sources)
        self.assertNotIn("invalid.ts", warm.hashes)
        self.assertNotIn("encoding.js", warm.hashes)
        self.assertEqual(warm.edges["b.ts:run"], {"a.ts:target"})

    def test_changed_exporter_rebuilds_cached_importer_edges_and_warnings(self):
        sources = {
            "a.ts": b"export function target(){return 1;}",
            "b.ts": b'import {target} from "./a"; export function run(){return target();}',
        }
        units = {}
        original = self.build(sources, units)
        self.assertEqual(original.edges["b.ts:run"], {"a.ts:target"})
        changed = dict(sources, **{"a.ts": b"export function replacement(){return 2;}"})
        units.pop("a.ts")  # The cache owner invalidates the changed byte digest.
        calls, spy = self.parser_spy()
        with spy:
            incremental = self.build(changed, units)
        self.assertEqual(calls, [changed["a.ts"]])
        self.assertEqual(incremental.describe(), self.build(changed).describe())
        self.assertEqual(incremental.edges["b.ts:run"], set())
        self.assertTrue(any("Unresolved calls (1) in b.ts:run" in w for w in incremental.warnings))
        # Removing a source must not resurrect it from retained cache rows.
        deleted = {"b.ts": changed["b.ts"]}
        calls, spy = self.parser_spy()
        with spy:
            after_delete = self.build(deleted, units)
        self.assertEqual(calls, [])
        self.assertEqual(after_delete.describe(), self.build(deleted).describe())
        self.assertNotIn("a.ts:replacement", after_delete.symbols)

    def test_static_method_and_shadowing_facts_match_after_reload(self):
        sources = {
            "methods.ts": b"function target(){} export const expression=function target(){target();}; class C { static run(){this.instance();} instance(){this.other();} other(){} }",
        }
        units = {}
        cold = self.build(sources, units)
        warm = self.build(sources, json.loads(json.dumps(units)))
        self.assertEqual(cold.describe(), warm.describe())
        self.assertEqual(warm.edges["methods.ts:expression"], set())
        self.assertEqual(warm.edges["methods.ts:C.run"], set())
        self.assertEqual(warm.edges["methods.ts:C.instance"], {"methods.ts:C.other"})


if __name__ == "__main__":
    unittest.main()
