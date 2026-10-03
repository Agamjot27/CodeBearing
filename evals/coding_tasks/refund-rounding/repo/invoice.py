from decimal import Decimal, ROUND_HALF_UP


def round_line(amount):
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def invoice_total(amounts):
    return sum((round_line(amount) for amount in amounts), Decimal("0"))
