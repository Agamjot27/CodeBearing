from decimal import Decimal
import unittest
from invoice import invoice_total
from service import refund_preview


class PublicTests(unittest.TestCase):
    def test_invoice_rounds_per_line(self):
        self.assertEqual(invoice_total(["0.005", "0.005"]), Decimal("0.02"))

    def test_whole_cent_refund(self):
        self.assertEqual(refund_preview(["2.50"]), {"amount": Decimal("2.50"), "status": "preview"})
