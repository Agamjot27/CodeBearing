import unittest
from pathlib import Path

from codebearing.index import build_index, build_index_from_sources


class SnapshotTests(unittest.TestCase):
    def test_sources_match_disk_index(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "refunds"
        disk = build_index(root)
        snapshot = build_index_from_sources(root, disk.sources)
        self.assertEqual(snapshot.describe(), disk.describe())

    def test_historical_encoding_and_parse_failure_are_preserved(self):
        raw = b"# coding: latin-1\n# caf\xe9\ndef old():\n    return 1\n"
        index = build_index_from_sources(Path.cwd(), {"old.py": raw, "bad.py": b"def ?"})
        self.assertIn("old.py:old", index.symbols)
        self.assertIn("bad.py", index.sources)
        self.assertNotIn("bad.py", index.hashes)
        self.assertTrue(any("bad.py" in warning for warning in index.warnings))

    def test_snapshot_uses_source_bytes_instead_of_current_files(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "refunds"
        snapshot = build_index_from_sources(root, {"billing.py": b"def removed():\n    return 1\n"})
        self.assertEqual(set(snapshot.symbols), {"billing.py:removed"})

    def test_unsafe_and_excluded_source_paths_are_disclosed(self):
        index = build_index_from_sources(Path.cwd(), {"../escape.py": b"def x(): pass", ".venv/x.py": b"def y(): pass"})
        self.assertFalse(index.symbols)
        self.assertEqual(len(index.warnings), 2)
