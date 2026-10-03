from refunds import refund_total


def refund_preview(amounts):
    return {"amount": refund_total(amounts), "status": "preview"}
