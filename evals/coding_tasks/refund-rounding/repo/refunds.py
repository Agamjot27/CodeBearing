from decimal import Decimal
from invoice import round_line


def refund_total(amounts):
    return round_line(sum((Decimal(str(amount)) for amount in amounts), Decimal("0")))
