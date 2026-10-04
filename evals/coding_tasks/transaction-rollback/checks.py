"""Independent checks stay outside the indexed fixture repo; no live database."""

import unittest
from orders import submit_order
from transactions import run_transaction


class SyntheticClient:
    def __init__(self, begin_error=None, commit_error=None, rollback_error=None):
        self.events = []
        self.begin_error = begin_error
        self.commit_error = commit_error
        self.rollback_error = rollback_error

    def begin(self):
        self.events.append("begin")
        if self.begin_error is not None:
            raise self.begin_error

    def commit(self):
        self.events.append("commit")
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self):
        self.events.append("rollback")
        if self.rollback_error is not None:
            raise self.rollback_error

    def release(self, discard=False):
        self.events.append(("release", discard))


class SyntheticPool:
    def __init__(self, client=None, error=None):
        self.client = client
        self.error = error

    def acquire(self):
        if self.error is not None:
            raise self.error
        return self.client


class AcceptanceTests(unittest.TestCase):
    def test_original_error_survives_failed_rollback(self):
        original = ValueError("reservation rejected")
        client = SyntheticClient(rollback_error=ConnectionError("rollback disconnected"))

        def fail(active):
            self.assertIs(active, client)
            client.events.append("operation")
            raise original

        with self.assertRaises(ValueError) as caught:
            submit_order(SyntheticPool(client), fail)
        self.assertIs(caught.exception, original)
        self.assertEqual(client.events, ["begin", "operation", "rollback", ("release", True)])

    def test_failed_rollback_discards_exactly_once(self):
        client = SyntheticClient(rollback_error=RuntimeError("rollback failure"))

        def fail(active):
            raise ValueError("operation failure")

        # Disposal is checked independently of exception identity so fixing only
        # error preservation still fails the poisoned-client regression.
        try:
            run_transaction(SyntheticPool(client), fail)
        except Exception:
            pass
        self.assertEqual([event for event in client.events if isinstance(event, tuple)],
                         [("release", True)])

    def test_successful_rollback_preserves_error_and_reuses_client(self):
        original = LookupError("missing stock")
        client = SyntheticClient()

        def fail(active):
            raise original

        with self.assertRaises(LookupError) as caught:
            run_transaction(SyntheticPool(client), fail)
        self.assertIs(caught.exception, original)
        self.assertEqual(client.events, ["begin", "rollback", ("release", False)])

    def test_commit_error_is_preserved_when_rollback_fails(self):
        original = RuntimeError("commit rejected")
        client = SyntheticClient(commit_error=original, rollback_error=ConnectionError("offline"))
        with self.assertRaises(RuntimeError) as caught:
            run_transaction(SyntheticPool(client), lambda active: "result")
        self.assertIs(caught.exception, original)
        self.assertEqual(client.events, ["begin", "commit", "rollback", ("release", True)])

    def test_begin_error_rolls_back_and_releases(self):
        original = RuntimeError("begin rejected")
        client = SyntheticClient(begin_error=original)
        with self.assertRaises(RuntimeError) as caught:
            run_transaction(SyntheticPool(client), lambda active: self.fail("must not run"))
        self.assertIs(caught.exception, original)
        self.assertEqual(client.events, ["begin", "rollback", ("release", False)])

    def test_acquire_error_does_not_invent_client_cleanup(self):
        original = ConnectionError("pool offline")
        with self.assertRaises(ConnectionError) as caught:
            run_transaction(SyntheticPool(error=original), lambda active: self.fail("must not run"))
        self.assertIs(caught.exception, original)
