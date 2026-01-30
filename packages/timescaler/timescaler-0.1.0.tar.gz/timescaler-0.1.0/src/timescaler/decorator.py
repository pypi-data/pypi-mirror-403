from functools import wraps
from typing import List, Optional
from timescaler.main import Timescaler, Hypertable

def snap_stats(hypertables: Optional[List[Hypertable]] = None):
    """
    Decorator to snapshot chunk statistics after the decorated function completes.
    
    Usage:
        @snap_stats
        def my_func():
            ...
            
        @snap_stats(hypertables=[Hypertable('public', 'my_table')])
        def my_func():
            ...
    """
    # This handles the case where it's called as @snap_stats without parens?
    # Actually @snap_stats without parens means 'hypertables' receives the function.
    # We need to detect that.
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Snap after execution
            # If used as @snap_stats without parens, 'hypertables' is the function, so we default to None for snap list.
            # But wait, the standard pattern for optional-arg decorator is complex.
            # Let's check below.
            
            target_list = hypertables if isinstance(hypertables, list) else None
            Timescaler.snap(target_hypertables=target_list)
            return result
        return wrapper

    if callable(hypertables):
        # Case: @snap_stats (no parentheses)
        func = hypertables
        hypertables = None # reset arg
        return decorator(func)
    else:
        # Case: @snap_stats(hypertables=...)
        return decorator
