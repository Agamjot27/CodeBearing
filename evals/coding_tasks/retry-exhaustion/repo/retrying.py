class TransientError(Exception):
    pass


def run_with_retry(operation, max_attempts):
    for attempt in range(max_attempts):
        try:
            return operation()
        except TransientError:
            if attempt == max_attempts:
                raise
