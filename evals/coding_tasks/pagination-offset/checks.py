import unittest
from paging import slice_page
from service import list_page


class AcceptanceTests(unittest.TestCase):
    def test_page_boundaries(self):
        self.assertEqual(slice_page(list(range(5)), 1, 2), [0, 1])
        self.assertEqual(slice_page(list(range(5)), 2, 2), [2, 3])
        self.assertEqual(slice_page(list(range(5)), 3, 2), [4])
        self.assertEqual(slice_page(list(range(5)), 4, 2), [])

    def test_invalid_arguments(self):
        for page, size in [(0, 2), (-1, 2), (1, 0), (1, -1)]:
            with self.assertRaises(ValueError):
                slice_page([1, 2], page, size)

    def test_consumer_shape(self):
        self.assertEqual(list_page([1, 2, 3], 1, 2), {"items": [1, 2], "total": 3})
