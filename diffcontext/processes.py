"""Bounded waits for trusted harness commands; this is not a security sandbox."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    stdout_truncated: bool


def _stop_tree(process: subprocess.Popen):
    # Kill descendants before a Windows venv launcher exits and loses the tree
    # relationship. Only the PID returned by our own Popen is targeted.
    try:
        if os.name == "nt":
            stopped = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     timeout=5, check=False)
            if stopped.returncode and process.poll() is None:
                raise OSError("Owned process-tree cleanup failed.")
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        # Release the parent even if tree cleanup fails, but do not report that
        # failure as a clean candidate timeout or conceal it from the harness.
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise OSError("Owned subprocess cleanup did not complete.") from exc


def _tail(stream, limit: int) -> tuple[str, bool]:
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(max(0, size - limit))
    text = stream.read(limit).decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n"), size > limit


def run_bounded(command: list[str], *, timeout: float, cwd: Path | None = None,
                input_text: str = "", stdout_limit: int = 250_000) -> ProcessResult:
    """Run an argv command with bounded waiting and bounded retained output.

    Disk output is not quota-limited. Files prevent descendants holding capture
    pipes from blocking communicate() after timeout. Callers classify the raised
    TimeoutExpired/OSError and must not expose provider stderr as credentials.
    """
    if timeout <= 0 or stdout_limit < 1:
        raise ValueError("Timeout and retained output limit must be positive.")
    with tempfile.TemporaryFile() as stdin, tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        stdin.write(input_text.encode("utf-8"))
        stdin.seek(0)
        process = subprocess.Popen(command, cwd=cwd, stdin=stdin, stdout=stdout,
                                   stderr=stderr, shell=False, start_new_session=os.name != "nt")
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _stop_tree(process)
            raise
        output, truncated = _tail(stdout, stdout_limit)
        errors, _ = _tail(stderr, 4000)
        return ProcessResult(process.returncode, output, errors, truncated)
