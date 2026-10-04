from transactions import run_transaction


def submit_order(pool, reserve):
    """Return the reservation result after its transaction commits."""
    return run_transaction(pool, reserve)
