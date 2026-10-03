import json
import subprocess
import sys
import unittest
from pathlib import Path

import test_core
import test_changes
from diffcontext.changes import localize_changes
from diffcontext.index import build_index


class CacheCliTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_cli_cache_survives_separate_processes(self):
        command = [sys.executable, "-m", "diffcontext", "--repo", str(self.root), "--cache", "index"]
        counts = []
        for _ in range(2):
            result = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            counts.append(json.loads(result.stdout)["indexing"])
        self.assertEqual(counts[0]["parsed_files"], 3)
        self.assertEqual(counts[1]["reused_files"], 3)
        self.assertEqual(counts[1]["parsed_files"], 0)


class CacheGitTests(unittest.TestCase):
    setUp = test_changes.ChangesTests.setUp
    write = test_changes.ChangesTests.write
    git = test_changes.ChangesTests.git
    cleanup = test_changes.ChangesTests.cleanup

    def test_tracked_snapshot_cache_matches_full_and_excludes_untracked_facts(self):
        self.write("untracked.py", "def unrelated():\n    return 1\n")
        build_index(self.root, cache=True)
        self.write("billing.py", "RATE = 2\n\ndef helper(x):\n    return x * RATE\n")
        cached = localize_changes(self.root, cache=True)
        full = localize_changes(self.root)
        report = dict(cached.report)
        report.pop("indexing")
        self.assertEqual(report, full.report)
        self.assertEqual(cached.current.symbols, full.current.symbols)
        self.assertEqual(cached.current.edges, full.current.edges)
        self.assertEqual(cached.historical.describe(), full.historical.describe())
        self.assertNotIn("untracked.py", cached.current.sources)
        self.assertIn("billing.py:refund", cached.report["removed_symbols"])
        self.assertIn("checkout.py:checkout", cached.report["current_seeds"])
        warm = localize_changes(self.root, cache=True)
        self.assertEqual(warm.report["indexing"]["parsed_files"], 0)
