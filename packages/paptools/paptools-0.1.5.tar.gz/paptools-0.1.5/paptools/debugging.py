from .settings import settings
import time
from functools import wraps
from contextlib import contextmanager

_warned = set()

def warn_once(msg):
    """Print a warning only once."""
    if msg not in _warned:
        _warned.add(msg)
        print(f"[WARNING] {msg}")

@contextmanager
def debug(state=True, level="debug"):
    """Example usage:
    with debug(True, level="trace"):
        result = complicated_calculation()
        """
    old_verbose = settings.verbose
    old_level = settings.debug_level
    settings.verbose = state
    settings.debug_level = level
    try:
        yield
    finally:
        settings.verbose = old_verbose
        settings.debug_level = old_level

def debug_print(msg, level="info"):
    if not settings.verbose:
        return
    
    levels = ["info", "debug", "trace"]
    
    if levels.index(level) <= levels.index(settings.debug_level):
        print(f"[{level.upper()}] {msg}")

def dump_object(obj):
    """Print internal fields of an object for debugging."""
    if settings.verbose:
        print("[OBJECT DUMP]")
        for key, val in vars(obj).items():
            print(f"  {key}: {val}")

def timed(func):
    """
    Decorator that measures execution time of a function, but only
    prints the timing result when settings.verbose is True.

    Example:
        @timed
        def compute():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # If debugging is off → run normally
        if not settings.verbose:
            return func(*args, **kwargs)

        # Debugging on → measure time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        print(f"[TIMED] {func.__name__}: {end - start:.6f} s")
        return result

    return wrapper