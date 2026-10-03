import unittest
from retrying import run_with_retry, TransientError
from client import fetch


class AcceptanceTests(unittest.TestCase):
    def test_exhaustion_preserves_exception_and_count(self):
        calls = []
        error = TransientError("last failure")
        def fail():
            calls.append(1)
            raise error
        with self.assertRaises(TransientError) as caught:
            run_with_retry(fail, 3)
        self.assertIs(caught.exception, error)
        self.assertEqual(len(calls), 3)

    def test_success_after_failure(self):
        calls = []
        def sometimes():
            calls.append(1)
            if len(calls) < 2:
                raise TransientError("retry")
            return "done"
        self.assertEqual(fetch(sometimes), "done")
        self.assertEqual(len(calls), 2)

    def test_nontransient_and_invalid(self):
        def fail():
            raise RuntimeError("do not retry")
        with self.assertRaises(RuntimeError):
            run_with_retry(fail, 2)
        for attempts in [0, -1]:
            with self.assertRaises(ValueError):
                run_with_retry(lambda: 1, attempts)
