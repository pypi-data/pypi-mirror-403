"""Retry utilities for handling transient failures."""

from functools import wraps
import time
from typing import Any, Callable, Optional, Type, Union

from owlab.core.logger import get_logger

logger = get_logger("owlab.utils.retry")


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""

    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """Decorator for retrying function calls with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Backoff multiplier (default: 2.0)
        exceptions: Exception type(s) to catch and retry on (default: Exception)
        on_retry: Optional callback function called on each retry attempt.
            Receives (exception, attempt_number) as arguments.

    Returns:
        Decorated function

    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError, TimeoutError))
        def fetch_data():
            # Function that may fail
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
                        raise RetryError(
                            f"Function {func.__name__} failed after {max_attempts} attempts"
                        ) from e

            # Should never reach here, but just in case
            if last_exception:
                raise RetryError(
                    f"Function {func.__name__} failed after {max_attempts} attempts"
                ) from last_exception

        return wrapper

    return decorator


def retry_on_http_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    status_codes: Optional[tuple[int, ...]] = None,
):
    """Decorator for retrying HTTP requests on specific status codes.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Backoff multiplier (default: 2.0)
        status_codes: HTTP status codes to retry on.
            Default: (429, 500, 502, 503, 504) - rate limit and server errors

    Returns:
        Decorated function
    """
    if status_codes is None:
        status_codes = (429, 500, 502, 503, 504)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import requests

            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    response = func(*args, **kwargs)
                    # Check if response is a requests.Response object
                    if hasattr(response, "status_code"):
                        if response.status_code in status_codes:
                            if attempt < max_attempts:
                                logger.warning(
                                    f"HTTP {response.status_code} on attempt {attempt}/{max_attempts} "
                                    f"for {func.__name__}. Retrying in {current_delay:.2f}s..."
                                )
                                time.sleep(current_delay)
                                current_delay *= backoff
                                continue
                            else:
                                logger.error(
                                    f"HTTP {response.status_code} after {max_attempts} attempts "
                                    f"for {func.__name__}"
                                )
                                response.raise_for_status()
                    return response
                except requests.HTTPError as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"HTTP error on attempt {attempt}/{max_attempts} for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"HTTP error after {max_attempts} attempts for {func.__name__}: {e}"
                        )
                        raise
                except requests.RequestException as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Request error on attempt {attempt}/{max_attempts} for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Request error after {max_attempts} attempts for {func.__name__}: {e}"
                        )
                        raise

            if last_exception:
                raise RetryError(
                    f"Function {func.__name__} failed after {max_attempts} attempts"
                ) from last_exception

        return wrapper

    return decorator
