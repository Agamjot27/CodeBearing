"""Wholly authored development fixture; clients expose begin/commit/rollback/release."""


def run_transaction(pool, operation):
    client = pool.acquire()
    try:
        client.begin()
        result = operation(client)
        client.commit()
        return result
    except BaseException:
        client.rollback()
        raise
    finally:
        client.release(discard=False)
