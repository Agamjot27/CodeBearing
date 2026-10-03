import asyncio
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import AsyncMock, patch

import test_core
from diffcontext.onboarding import main, prepare_config, save_config


class SetupTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_json_merge_preserves_settings_and_repeat_bytes(self):
        for client, path in [("claude", ".mcp.json"), ("cursor", ".cursor/mcp.json")]:
            old = {"custom": True, "mcpServers": {"existing": {"command": "other"}}}
            self.write(path, json.dumps(old))
            target, contents, before = prepare_config(self.root, client)
            save_config(self.root, target, contents, before)
            merged = json.loads(target.read_text())
            self.assertTrue(merged["custom"])
            self.assertEqual(merged["mcpServers"]["existing"], old["mcpServers"]["existing"])
            self.assertIn("codebearing", merged["mcpServers"])
            again = prepare_config(self.root, client)
            self.assertEqual(again[1], target.read_bytes())

    @unittest.skipIf(sys.version_info < (3, 11), "Automatic TOML merge needs Python 3.11")
    def test_codex_preserves_comments_and_unrelated_tables(self):
        import tomllib
        old = '# personal settings\nmodel = "existing-model"\n[mcp_servers.other]\ncommand = "other"\n'
        self.write(".codex/config.toml", old)
        target, contents, before = prepare_config(self.root, "codex")
        save_config(self.root, target, contents, before)
        self.assertTrue(target.read_text().startswith(old.rstrip()))
        parsed = tomllib.loads(target.read_text())
        self.assertEqual(parsed["model"], "existing-model")
        self.assertEqual(parsed["mcp_servers"]["other"]["command"], "other")
        self.assertIn("codebearing", parsed["mcp_servers"])
        self.assertEqual(prepare_config(self.root, "codex")[1], target.read_bytes())

    def test_invalid_conflicting_or_concurrently_changed_settings_are_not_overwritten(self):
        for data in ['invalid', '[]', '{"mcpServers":[]}', '{"mcpServers":{"codebearing":{"command":"existing"}}}']:
            self.write(".mcp.json", data)
            with self.assertRaises(ValueError):
                prepare_config(self.root, "claude")
            self.assertEqual((self.root / ".mcp.json").read_text(), data)
        self.write(".mcp.json", '{}')
        target, contents, before = prepare_config(self.root, "claude")
        target.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, "changed"):
            save_config(self.root, target, contents, before)
        self.assertEqual(target.read_text(), '{"changed":true}')

    def test_connection_failure_writes_no_settings(self):
        with patch("diffcontext.onboarding.check_connection", new=AsyncMock(side_effect=RuntimeError("offline"))), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["setup", "--client", "cursor", "--repo", str(self.root)]), 2)
        self.assertFalse((self.root / ".cursor").exists())

    def test_setup_reports_plain_next_step_after_verified_connection(self):
        output = io.StringIO()
        checked = AsyncMock(return_value={"tools": ["one", "two"]})
        with patch("diffcontext.onboarding.check_connection", new=checked), contextlib.redirect_stdout(output):
            self.assertEqual(main(["setup", "--client", "cursor", "--repo", str(self.root)]), 0)
        self.assertIn("CodeBearing", output.getvalue())
        self.assertIn("Open/restart cursor", output.getvalue())
        self.assertTrue((self.root / ".cursor/mcp.json").exists())

    def test_symlinked_configuration_is_refused(self):
        other = self.root / "other.json"
        other.write_text('{}')
        try:
            (self.root / ".mcp.json").symlink_to(other)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            prepare_config(self.root, "claude")
        self.assertEqual(other.read_text(), '{}')
