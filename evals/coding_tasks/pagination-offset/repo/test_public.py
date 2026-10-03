import unittest
from service import list_page


class PublicTests(unittest.TestCase):
    def test_empty_collection(self):
        self.assertEqual(list_page([], 1, 5), {"items": [], "total": 0})
