"""Retry decorator for fault-tolerant operations.

Usage:
    from cgc_common.utils import retry_on_failure

    @retry_on_failure(max_attempts=3, delay_seconds=0.5, logger=logger)
    def query_gpu():
        return run_nvidia_smi()
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry_on_failure(
    max_attempts: int = 3,
    delay_seconds: float = 0.0,
    logger: Any | None = None,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry decorator with optional delay and logging.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay_seconds: Delay between retries in seconds (default: 0)
        logger: Optional logger for retry messages (uses logger.warning)
        exceptions: Tuple of exception types to catch (default: Exception)

    Returns:
        Decorated function that retries on failure

    Example:
        @retry_on_failure(max_attempts=3, delay_seconds=0.5)
        def flaky_operation():
            return external_api_call()
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: BaseException | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        if logger:
                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}"
                            )
                        if delay_seconds > 0:
                            time.sleep(delay_seconds)
                    else:
                        if logger:
                            logger.warning(
                                f"{func.__name__} failed after {max_attempts} attempts: {e}"
                            )

            # Re-raise the last exception if all attempts failed
            if last_exception is not None:
                raise last_exception

        return wrapper  # type: ignore[return-value]

    return decorator
