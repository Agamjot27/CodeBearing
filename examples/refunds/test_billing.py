from decimal import Decimal
from billing import refund_total
from checkout import issue_refund


def test_rounding_is_per_line():
    assert refund_total(["0.005", "0.005"]) == Decimal("0.02")


def test_checkout_refund():
    assert issue_refund(["2.50"])["amount"] == Decimal("2.50")
