from decimal import Decimal
import unittest
from invoice import invoice_total
from refunds import refund_total
from service import refund_preview


class AcceptanceTests(unittest.TestCase):
    def test_fractional_lines(self):
        for amounts in [["0.005", "0.005"], ["1.005", "2.005"], ["-0.005", "0.005"]]:
            self.assertEqual(refund_total(amounts), invoice_total(amounts))

    def test_empty_and_decimal(self):
        self.assertIsInstance(refund_total([]), Decimal)
        self.assertEqual(refund_total([]), Decimal("0"))
        self.assertEqual(refund_total([Decimal("0.005")] * 3), Decimal("0.03"))

    def test_preview_shape(self):
        self.assertEqual(refund_preview(["0.005", "0.005"]), {"amount": Decimal("0.02"), "status": "preview"})
