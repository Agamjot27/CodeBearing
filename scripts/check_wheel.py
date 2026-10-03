"""Install a wheel in a fresh environment and verify entry points outside the checkout.

Requires pip >=22.3 in the invoking interpreter; dependency installation may use
the network. No model calls, assistant settings writes, or package publication.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
import venv
import zipfile
from pathlib import Path


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=240)
    if result.returncode:
        raise RuntimeError(f"Command failed: {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def verify(wheel: Path):
    wheel = wheel.resolve()
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if any(name.startswith(("tests/", "evals/", "examples/", "scripts/", ".")) for name in names):
            raise ValueError("Wheel contains development artifacts.")
        if "diffcontext/connect.py" not in names:
            raise ValueError("Wheel is missing the installed MCP launcher.")
    checkout = Path(__file__).resolve().parents[1]
    scratch = checkout / ".test-tmp" / ("wheel-" + uuid.uuid4().hex)
    scratch.mkdir(parents=True)
    # Keep cleanup constrained to our verified disposable workspace directory.
    if not scratch.resolve().is_relative_to((checkout / ".test-tmp").resolve()):
        raise ValueError("Distribution scratch directory escaped workspace.")
    try:
        environment = scratch / "environment"
        venv.EnvBuilder(with_pip=False).create(environment)
        bin_dir = environment / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        run([sys.executable, "-m", "pip", "--python", str(python), "install", str(wheel) + "[mcp]"], scratch)
        repo = scratch / "project with spaces"
        shutil.copytree(checkout / "examples" / "refunds", repo,
                        ignore=shutil.ignore_patterns("__pycache__", ".diffcontext"))
        launcher = bin_dir / ("diffcontext-lab-mcp.exe" if os.name == "nt" else "diffcontext-lab-mcp")
        core = bin_dir / ("diffcontext-lab.exe" if os.name == "nt" else "diffcontext-lab")
        run([str(launcher), "--help"], scratch)
        indexed = json.loads(run([str(core), "--repo", str(repo), "index"], scratch))
        if not indexed:
            raise ValueError("Installed core entry point returned no index.")
        for client in ("claude", "cursor", "codex"):
            output = run([str(launcher), "--repo", str(repo), "--config", client], scratch)
            if client == "codex":
                if sys.version_info >= (3, 11):
                    import tomllib
                    entry = tomllib.loads(output)["mcp_servers"]["diffcontext_lab"]
                else:
                    continue
            else:
                entry = json.loads(output)["mcpServers"]["diffcontext_lab"]
            if Path(entry["command"]).absolute() != python.absolute() or entry["args"][-1] != str(repo.resolve()):
                raise ValueError("Configuration does not point to the clean installation/repository.")
            run([entry["command"], "-I", "-c", "import diffcontext.connect, mcp"], scratch)
        checked = json.loads(run([str(launcher), "--repo", str(repo), "--check"], scratch))
        if checked["status"] != "connected" or len(checked["tools"]) != 6:
            raise ValueError("Installed MCP server failed discovery/search.")
        if (repo / ".diffcontext").exists():
            raise ValueError("Read-only check created repository state.")
        print(json.dumps({"wheel": wheel.name, "status": "passed", "tools": checked["tools"],
                          "checks": ["clean install", "outside-checkout CLI", "client configs", "stdio discovery and search"]}, indent=2))
    finally:
        shutil.rmtree(scratch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    verify(parser.parse_args().wheel)
