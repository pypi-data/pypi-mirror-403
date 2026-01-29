import inspect
import hashlib

def fingerprint_exception(func, exception):
    """
    Generate a genetic fingerprint for an exception
    based on function bytecode + exception signature.
    """
    code = func.__code__.co_code
    location = f"{func.__code__.co_filename}:{func.__code__.co_firstlineno}"
    signature = f"{type(exception).__name__}:{str(exception)}"

    raw = code + location.encode() + signature.encode()
    return hashlib.sha256(raw).hexdigest()
