"""Optional parser failures remain visible without breaking the Python core."""

import unittest
from pathlib import Path
from unittest.mock import patch

from codebearing.index import build_index_from_sources, is_source_path


class LanguageBoundaryTests(unittest.TestCase):
    def test_missing_extra_retains_bytes_and_python_evidence(self):
        sources = {"main.py": b"def run(): return 1\n",
                   "main.ts": b"export function run() { return 1; }\n"}
        with patch.dict("sys.modules", {"codebearing.typescript": None}):
            index = build_index_from_sources(Path.cwd(), sources)
        self.assertEqual(set(index.sources), set(sources))
        self.assertEqual(set(index.symbols), {"main.py:run"})
        self.assertNotIn("main.ts", index.hashes)
        self.assertTrue(any("[typescript]" in w and "main.ts" in w for w in index.warnings))

    def test_only_implementation_paths_are_eligible(self):
        for path in ("main.py", "main.ts", "main.tsx", "main.js", "main.jsx", "main.mts", "main.mjs"):
            self.assertTrue(is_source_path(path))
        for path in ("types.d.ts", "types.d.mts", "bundle.min.js", "app.go", "package.json"):
            self.assertFalse(is_source_path(path))
