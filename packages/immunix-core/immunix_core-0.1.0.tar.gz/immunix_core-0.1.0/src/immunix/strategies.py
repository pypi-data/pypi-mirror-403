import time

def retry_strategy(func, *args, **kwargs):
    return func(*args, **kwargs)

def backoff_strategy(func, *args, **kwargs):
    time.sleep(2)
    return func(*args, **kwargs)

def degraded_strategy(func, *args, **kwargs):
    return {"status": "DEGRADED", "data": None}

STRATEGIES = {
    "retry": retry_strategy,
    "backoff": backoff_strategy,
    "degraded": degraded_strategy,
}
