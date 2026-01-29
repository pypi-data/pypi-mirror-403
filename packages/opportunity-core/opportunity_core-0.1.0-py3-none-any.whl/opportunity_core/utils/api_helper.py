import logging
import time
import random
from typing import Callable, TypeVar, Any

from paapi5_python_sdk.rest import ApiException

logger = logging.getLogger(__name__)

T = TypeVar("T")


def call_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 5,
    initial_delay: float = 2.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    **kwargs: Any,
) -> T:
    """
    Call an API function with exponential backoff for rate limiting.

    Args:
        func: The API function to call.
        *args: Positional arguments for the function.
        max_retries: Maximum number of retries.
        initial_delay: Initial delay in seconds after a failure.
        max_delay: Maximum delay in seconds.
        backoff_factor: Multiplier for the delay after each failure.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the API function call.

    Raises:
        ApiException: If the API call fails after all retries.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            last_exception = e
            # Check for TooManyRequests (HTTP 429) or ThrottlingException
            if e.status == 429 or "TooManyRequests" in str(e) or "Throttling" in str(e):
                if attempt < max_retries:
                    # Add some jitter to prevent thundering herd
                    sleep_time = min(delay, max_delay) * (1 + random.random() * 0.1)
                    logger.warning(
                        f"⚠️  Rate limit hit (429). Retrying in {sleep_time:.2f}s (Attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor
                else:
                    logger.error("❌ Max retries reached for rate limiting.")
            else:
                # For other errors, re-raise immediately or handle differently?
                # For now, we re-raise non-rate-limit errors to avoid masking real issues.
                # Unless it's a 5xx server error which might be transient.
                if 500 <= e.status < 600:
                    if attempt < max_retries:
                        sleep_time = min(delay, max_delay)
                        logger.warning(
                            f"⚠️  Server error ({e.status}). Retrying in {sleep_time:.2f}s (Attempt {attempt + 1}/{max_retries})..."
                        )
                        time.sleep(sleep_time)
                        delay *= backoff_factor
                        continue

                raise e
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in API call: {e}")
            raise e

    if last_exception:
        raise last_exception
