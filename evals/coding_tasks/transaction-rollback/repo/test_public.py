import unittest
from orders import submit_order


class PublicTests(unittest.TestCase):
    def test_success_commits_and_releases_once(self):
        events = []

        class Client:
            def begin(self): events.append("begin")
            def commit(self): events.append("commit")
            def rollback(self): events.append("rollback")
            def release(self, discard=False): events.append(("release", discard))

        client = Client()

        class Pool:
            def acquire(self): return client

        def reserve(active):
            self.assertIs(active, client)
            events.append("reserve")
            return {"reservation": 42}

        self.assertEqual(submit_order(Pool(), reserve), {"reservation": 42})
        self.assertEqual(events, ["begin", "reserve", "commit", ("release", False)])
