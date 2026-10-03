"""Trusted local coding fixtures, restricted edits and executable grading.

Subprocesses isolate imports/state, not permissions. Do not use this as a security
sandbox for hostile repositories or candidates.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodingTask:
    id: str
    directory: Path
    task: str
    query: str
    editable: tuple[str, ...]
    scope: str
    evidence: str
    lesson: str


def load_suite(manifest: Path) -> list[CodingTask]:
    manifest = manifest.resolve()
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("tasks"), list) or not data["tasks"]:
        raise ValueError("Expected a nonempty coding suite with schema_version 1.")
    tasks = []
    seen = set()
    for row in data["tasks"]:
        task_id = row["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", task_id) or task_id in seen:
            raise ValueError("Task IDs must be unique lowercase slugs.")
        directory = (manifest.parent / row["directory"]).resolve()
        if not directory.is_relative_to(manifest.parent) or directory == manifest.parent:
            raise ValueError("Task assets must remain below the suite directory.")
        editable = tuple(row["editable"])
        if not editable or len(set(editable)) != len(editable):
            raise ValueError("Tasks need distinct editable source paths.")
        for relative in editable:
            source = directory / "repo" / relative
            if not source.resolve().is_relative_to(directory / "repo") or not source.is_file() or source.is_symlink() or not relative.endswith(".py") or Path(relative).name.startswith("test_"):
                raise ValueError("Editable paths must be existing non-test Python source files.")
        for asset in (directory / "checks.py", directory / "reference.json", directory / "repo" / "test_public.py"):
            if not asset.is_file() or asset.is_symlink():
                raise ValueError(f"Missing or symlinked task asset: {asset.name}")
        tasks.append(CodingTask(task_id, directory, row["task"], row["query"], editable,
                                row["scope"], row["evidence"], row["lesson"]))
        seen.add(task_id)
    return tasks


@contextmanager
def trial_workspace(task: CodingTask, scratch: Path):
    scratch.mkdir(parents=True, exist_ok=True)
    scratch = scratch.resolve()
    workspace = scratch / uuid.uuid4().hex
    workspace.mkdir()
    try:
        # Only repo/ sources enter retrieval. Checks, references and lesson text
        # live outside that root and cannot accidentally become indexed context.
        for source in (task.directory / "repo").rglob("*"):
            if source.is_symlink():
                raise ValueError("Fixture repositories cannot contain symlinks.")
            if source.is_file() and source.suffix == ".py":
                relative = source.relative_to(task.directory / "repo")
                destination = workspace / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        yield workspace
    finally:
        # Verify the exact deletion target at cleanup, including possible changes
        # during candidate execution. Never delete a resolved path outside scratch.
        if workspace.is_symlink() or not workspace.resolve().is_relative_to(scratch) or workspace.resolve() == scratch:
            raise ValueError("Refusing cleanup outside the trial scratch directory.")
        shutil.rmtree(workspace)


def source_hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*.py")) if ".diffcontext" not in path.parts}


def apply_edits(task: CodingTask, root: Path, edits: dict[str, str]) -> dict[str, str]:
    if not isinstance(edits, dict) or any(path not in task.editable for path in edits):
        raise ValueError("Candidate edits must use only the task's editable source allowlist.")
    # Validate the entire batch before writing any file: a rejected second edit
    # must not leave the first edit applied in a partially modified trial.
    validated = []
    total = 0
    for relative, content in edits.items():
        if not isinstance(content, str):
            raise ValueError("Candidate file contents must be strings.")
        size = len(content.encode("utf-8"))
        total += size
        destination = root / relative
        if size > 200_000 or total > 200_000:
            raise ValueError("Candidate edits exceed the 200 KB payload limit.")
        if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents if parent != root and parent.is_relative_to(root)) or not destination.resolve().is_relative_to(root.resolve()):
            raise ValueError("Candidate edit target escapes the trial repository.")
        validated.append((destination, content))
    for destination, content in validated:
        destination.write_text(content, encoding="utf-8")
    return source_hashes(root)


GRADER = r'''
import json, runpy, sys, unittest
sys.path.insert(0, sys.argv[1])
suite = unittest.defaultTestLoader.discover(sys.argv[1], pattern="test_public.py")
namespace = runpy.run_path(sys.argv[2])
for value in namespace.values():
    if isinstance(value, type) and issubclass(value, unittest.TestCase) and value is not unittest.TestCase:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(value))
result = unittest.TextTestRunner(verbosity=0).run(suite)
passed = result.wasSuccessful() and result.testsRun > 0
print("CHECK_RESULT=" + json.dumps({"passed": passed, "tests": result.testsRun,
    "failures": len(result.failures), "errors": len(result.errors),
    "failed_tests": [test.id() for test, _ in result.failures + result.errors]}))
sys.exit(0 if passed else 1)
'''


def grade(task: CodingTask, root: Path, timeout: float = 5) -> dict:
    if not 0.1 <= timeout <= 60:
        raise ValueError("Grader timeout must be between 0.1 and 60 seconds.")
    started = time.monotonic()
    try:
        result = subprocess.run([sys.executable, "-I", "-B", "-c", GRADER, str(root.resolve()),
                                 str(task.directory / "checks.py")], cwd=root,
                                capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"outcome": "timeout", "passed": False, "elapsed_ms": round((time.monotonic() - started) * 1000, 3)}
    except OSError as exc:
        return {"outcome": "grader_error", "passed": None, "error": str(exc)}
    records = [line.removeprefix("CHECK_RESULT=") for line in result.stdout.splitlines() if line.startswith("CHECK_RESULT=")]
    try:
        check = json.loads(records[-1]) if records else {"passed": False, "tests": 0}
        if not isinstance(check, dict) or not isinstance(check.get("tests"), int):
            check = {"passed": False, "tests": 0}
    except json.JSONDecodeError:
        check = {"passed": False, "tests": 0}
    passed = result.returncode == 0 and check.get("passed") is True and check.get("tests", 0) > 0
    return {"outcome": "passed" if passed else "test_failed", "passed": passed,
            "returncode": result.returncode, "checks": check,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:]}


def calibrate(tasks: list[CodingTask], scratch: Path) -> dict:
    """Reference fixes calibrate the grader, never count as model task success."""
    rows = []
    for task in tasks:
        with trial_workspace(task, scratch) as root:
            before = grade(task, root)
            reference = json.loads((task.directory / "reference.json").read_text(encoding="utf-8"))
            apply_edits(task, root, reference)
            after = grade(task, root)
            rows.append({"task": task.id, "buggy": before, "reference": after,
                         "calibrated": before["outcome"] == "test_failed" and before.get("checks", {}).get("tests", 0) > 0 and after["passed"] is True})
    return {"label": "Reference-fix grader calibration, not model outcomes", "passed": all(r["calibrated"] for r in rows), "tasks": rows}
