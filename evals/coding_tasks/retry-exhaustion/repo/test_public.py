import unittest
from client import fetch


class PublicTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(fetch(lambda: "ok"), "ok")
