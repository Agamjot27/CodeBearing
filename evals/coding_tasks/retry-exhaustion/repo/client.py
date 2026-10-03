from retrying import run_with_retry


def fetch(operation):
    return run_with_retry(operation, max_attempts=3)
