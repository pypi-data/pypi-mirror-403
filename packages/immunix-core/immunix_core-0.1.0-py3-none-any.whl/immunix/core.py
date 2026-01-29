from functools import wraps
from .genome import fingerprint_exception
from .vault import GeneVault
from .strategies import STRATEGIES
from .exceptions import ImmunixExtinctionError


class Immunix:
    """
    Autonomous Self-Healing Infrastructure Engine.
    """

    def __init__(self, memory_file="immunix_memory.json"):
        self.vault = GeneVault(memory_file)

    def protect(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                fingerprint = fingerprint_exception(func, e)

                learned = self.vault.get(fingerprint)
                strategies = list(STRATEGIES.keys())

                if learned:
                    strategies.insert(0, learned["strategy"])

                for strategy_name in strategies:
                    try:
                        result = STRATEGIES[strategy_name](func, *args, **kwargs)
                        self.vault.store(fingerprint, strategy_name)
                        return result
                    except Exception:
                        continue

                raise ImmunixExtinctionError(
                    f"All recovery strategies failed for {func.__name__}"
                ) from e

        return wrapper
