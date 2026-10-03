import subprocess
import sys
import time
import unittest
from pathlib import Path

import test_core
from diffcontext.processes import run_bounded
from diffcontext.experiments import CommandRunner, RunnerError


class ProcessTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    write = test_core.CoreTests.write

    def test_input_output_exit_and_retention(self):
        result = run_bounded([sys.executable, "-c", "import sys; print(sys.stdin.read()); print('error',file=sys.stderr); sys.exit(3)"],
                             timeout=10, input_text="hello")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout.strip(), "hello")
        self.assertEqual(result.stderr.strip(), "error")
        self.assertFalse(result.stdout_truncated)
        tail = run_bounded([sys.executable, "-c", "print('x'*1000+'end')"], timeout=10, stdout_limit=20)
        self.assertTrue(tail.stdout_truncated)
        self.assertTrue(tail.stdout.endswith("end\n"))
        self.assertLessEqual(len(tail.stdout.encode()), 20)

    def test_timeout_stops_wrapper_and_descendant_without_pipe_wait(self):
        marker = self.root / "descendant-survived"
        ready = self.root / "descendant-started"
        child = "import time; from pathlib import Path; Path(" + repr(str(ready)) + ").write_text('ready'); time.sleep(4); Path(" + repr(str(marker)) + ").write_text('alive')"
        parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(30)"
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            run_bounded([sys.executable, "-c", parent], timeout=2.5)
        self.assertLess(time.monotonic() - started, 12)
        self.assertTrue(ready.exists(), "Child must have started for this test to prove descendant cleanup")
        time.sleep(4.5)
        self.assertFalse(marker.exists(), "Spawned descendant survived owned-tree cleanup")

    def test_oversized_adapter_output_is_not_parsed_from_truncated_tail(self):
        runner = CommandRunner([sys.executable, "-c", "print('x'*250001)"], timeout=10)
        with self.assertRaises(RunnerError) as caught:
            runner({})
        self.assertEqual(caught.exception.outcome, "invalid_response")
