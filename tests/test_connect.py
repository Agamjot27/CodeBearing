import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

import test_core
from codebearing.connect import configuration, main


class ConnectionTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_configs_preserve_spaces_and_pin_interpreter(self):
        root = self.root / "project with spaces"
        root.mkdir()
        for client in ("claude", "cursor"):
            entry = json.loads(configuration(root, client))["mcpServers"]["codebearing"]
            self.assertEqual(entry["command"], str(Path(sys.executable).absolute()))
            self.assertEqual(entry["args"], ["-m", "codebearing.connect", "--repo", str(root)])
            self.assertEqual(entry.get("type"), "stdio")
        # Parse TOML in the distribution check on Python 3.11+. Core still supports 3.10.
        if sys.version_info >= (3, 11):
            import tomllib
            entry = tomllib.loads(configuration(root, "codex"))["mcp_servers"]["codebearing"]
            self.assertEqual(entry["args"][-1], str(root))
            self.assertEqual(entry["command"], str(Path(sys.executable).absolute()))

    def test_configuration_preserves_virtualenv_symlink_path(self):
        interpreter = self.root / "venv-python"
        try:
            interpreter.symlink_to(sys.executable)
        except OSError:
            self.skipTest("Creating symlinks is not permitted on this host")
        entry = json.loads(configuration(self.root, "cursor", str(interpreter)))["mcpServers"]["codebearing"]
        self.assertEqual(entry["command"], str(interpreter.absolute()))

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib requires Python 3.11+")
    def test_codex_configuration_accepts_non_bmp_paths(self):
        import tomllib
        root = self.root / ("project-" + chr(0x1F600))
        entry = tomllib.loads(configuration(root, "codex"))["mcp_servers"]["codebearing"]
        self.assertEqual(entry["args"][-1], str(root.resolve()))

    def test_config_mode_does_not_create_host_settings_or_database(self):
        before = sorted(p.relative_to(self.root) for p in self.root.rglob("*"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["--repo", str(self.root), "--config", "claude"]), 0)
        self.assertIn("codebearing", json.loads(output.getvalue())["mcpServers"])
        self.assertEqual(before, sorted(p.relative_to(self.root) for p in self.root.rglob("*")))

    def test_missing_repository_has_no_success_output(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["--repo", str(self.root / "missing"), "--check"]), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("does not exist", stderr.getvalue())

    def test_missing_sdk_explains_optional_install(self):
        from unittest.mock import patch
        stderr = io.StringIO()
        with patch.dict(sys.modules, {"codebearing.mcp_server": None}), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["--repo", str(self.root)]), 2)
        self.assertIn('codebearing[mcp]', stderr.getvalue())


try:
    import mcp
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


@unittest.skipUnless(HAS_MCP, "optional MCP SDK is not installed")
class ConnectionProtocolTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    async def test_check_uses_real_subprocess_and_leaves_repo_unchanged(self):
        from codebearing.connect import TOOLS, check_connection
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = await check_connection(self.root)
        self.assertEqual(result["status"], "connected")
        self.assertEqual(set(result["tools"]), TOOLS)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
