"""Retry handler with exponential backoff and jitter."""

import random
from typing import Callable, Any, Awaitable


def calculate_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter.
    
    Formula: base delay 2s, multiply by 2 each attempt, max delay 300s, ±20% jitter
    
    Args:
        attempt: Current attempt number (1-indexed, where attempt=1 is initial attempt)
    
    Returns:
        Delay in seconds
    """
    base_delay = 2.0
    max_delay = 300.0
    
    # Calculate exponential delay: base_delay * (2 ^ (attempt - 1))
    # Attempt 1: 2 * 2^0 = 2s
    # Attempt 2: 2 * 2^1 = 4s
    # Attempt 3: 2 * 2^2 = 8s
    # etc.
    delay = base_delay * (2 ** (attempt - 1))
    
    # Cap at max delay
    delay = min(delay, max_delay)
    
    # Add ±20% jitter
    jitter_range = delay * 0.2
    jitter = random.uniform(-jitter_range, jitter_range)
    
    final_delay = delay + jitter
    
    # Ensure non-negative
    return max(0.0, final_delay)


async def retry_with_backoff(
    func: Callable[..., Awaitable[Any]],
    max_attempts: int,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Retry a function with exponential backoff and jitter.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts (attempt counter starts at 1)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result from func if successful
        
    Raises:
        Exception: Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # If this is the last attempt, raise the exception
            if attempt >= max_attempts:
                raise
            
            # Calculate delay and wait before retrying
            delay = calculate_backoff_delay(attempt)
            import asyncio
            await asyncio.sleep(delay)
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    
    raise RuntimeError("Retry failed without exception")

