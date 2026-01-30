"""Retry policy with exponential backoff for telemetry export.

This module provides retry logic to handle transient failures when
exporting telemetry to the collector.
"""

import logging
import random
import time
from typing import Callable, TypeVar, Any, Optional

from ..utils.exceptions import BufferingError, ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryPolicy:
    """Retry policy with exponential backoff and jitter.

    Provides configurable retry logic for handling transient failures
    when exporting telemetry to the collector.

    Features:
        - Exponential backoff with configurable base and max delays
        - Jitter to prevent thundering herd problem
        - Maximum attempt limits
        - Detailed logging of retry attempts

    Examples:
        >>> retry_policy = RetryPolicy(max_attempts=3, base_delay=1.0)
        >>> result = retry_policy.execute(export_function, data)

        With custom configuration:
        >>> retry_policy = RetryPolicy(
        ...     max_attempts=5,
        ...     base_delay=2.0,
        ...     max_delay=120.0,
        ...     jitter=True
        ... )
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        backoff_multiplier: float = 2.0,
    ):
        """Initialize retry policy.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            jitter: Whether to add random jitter (default: True)
            backoff_multiplier: Multiplier for exponential backoff (default: 2.0)

        Raises:
            ConfigurationError: If parameters are invalid
        """
        if max_attempts <= 0:
            raise ConfigurationError(f"max_attempts must be positive, got {max_attempts}")

        if base_delay <= 0:
            raise ConfigurationError(f"base_delay must be positive, got {base_delay}")

        if max_delay < base_delay:
            raise ConfigurationError(f"max_delay ({max_delay}) must be >= base_delay ({base_delay})")

        if backoff_multiplier <= 1.0:
            raise ConfigurationError(f"backoff_multiplier must be > 1.0, got {backoff_multiplier}")

        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.backoff_multiplier = backoff_multiplier

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds for this attempt

        Example:
            >>> policy = RetryPolicy(base_delay=1.0, max_delay=60.0)
            >>> policy.calculate_delay(0)  # First retry
            1.0
            >>> policy.calculate_delay(2)  # Third retry
            4.0
        """
        # Exponential backoff: delay = base_delay * (multiplier ^ attempt)
        delay = self.base_delay * (self.backoff_multiplier**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled (random value between 0 and delay)
        if self.jitter:
            delay = delay * random.uniform(0.5, 1.5)

        return delay

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with retry logic.

        Attempts to execute the function, retrying on failure with
        exponential backoff. Raises the last exception if all attempts fail.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful function execution

        Raises:
            Exception: The last exception if all retry attempts fail

        Example:
            >>> def export_data(data):
            ...     # Might fail transiently
            ...     send_to_collector(data)
            >>>
            >>> retry_policy = RetryPolicy(max_attempts=3)
            >>> retry_policy.execute(export_data, my_data)
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_attempts):
            try:
                # Try to execute function
                result = func(*args, **kwargs)

                # Log success if this wasn't the first attempt
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded after {attempt + 1} attempts",
                        extra={"attempt": attempt + 1, "max_attempts": self.max_attempts},
                    )

                return result

            except Exception as e:
                last_exception = e

                # Check if we have more attempts
                if attempt + 1 >= self.max_attempts:
                    logger.error(
                        f"Operation failed after {self.max_attempts} attempts: {e}",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": self.max_attempts,
                            "error": str(e),
                        },
                    )
                    break  # No more attempts, will raise below

                # Calculate delay and wait
                delay = self.calculate_delay(attempt)

                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{self.max_attempts}), "
                    f"retrying in {delay:.2f}s: {e}",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": self.max_attempts,
                        "delay_seconds": delay,
                        "error": str(e),
                    },
                )

                time.sleep(delay)

        # All attempts failed, raise the last exception
        if last_exception:
            raise last_exception
        else:
            # Should never happen, but handle defensively
            raise BufferingError(
                "Retry policy exhausted all attempts but no exception was captured. "
                "This indicates an internal error in the retry mechanism."
            )

    def execute_with_fallback(
        self, func: Callable[..., T], fallback: Callable[[], T], *args: Any, **kwargs: Any
    ) -> T:
        """Execute function with retry logic and fallback.

        Attempts to execute the function with retries. If all attempts fail,
        executes the fallback function instead of raising an exception.

        Args:
            func: Primary function to execute
            fallback: Fallback function to call if all attempts fail
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of successful execution (either func or fallback)

        Example:
            >>> def export_data(data):
            ...     send_to_collector(data)
            >>>
            >>> def queue_data():
            ...     queue.enqueue(data)
            ...     return None
            >>>
            >>> retry_policy = RetryPolicy(max_attempts=3)
            >>> retry_policy.execute_with_fallback(export_data, queue_data, my_data)
        """
        try:
            return self.execute(func, *args, **kwargs)
        except Exception as e:
            logger.warning(
                f"All retry attempts failed, executing fallback: {e}", extra={"error": str(e)}
            )
            return fallback()
