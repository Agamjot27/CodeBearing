from billing import refund_total as calculate_refund


def issue_refund(items):
    return {"amount": calculate_refund(items), "status": "preview"}
