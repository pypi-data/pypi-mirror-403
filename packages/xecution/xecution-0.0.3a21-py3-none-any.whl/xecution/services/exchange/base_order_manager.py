import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, List, Union
from enum import Enum
from dataclasses import dataclass


class ExchangeErrorType(Enum):
    """Standard error types across exchanges"""
    NETWORK_ERROR = "network_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_CREDENTIALS = "invalid_credentials"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    INVALID_SYMBOL = "invalid_symbol"
    INVALID_ORDER = "invalid_order"
    SERVER_ERROR = "server_error"
    MAINTENANCE = "maintenance"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry mechanism"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retryable_errors: List[ExchangeErrorType] = None

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ExchangeErrorType.NETWORK_ERROR,
                ExchangeErrorType.RATE_LIMIT_EXCEEDED,
                ExchangeErrorType.SERVER_ERROR
            ]


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 1200
    requests_per_second: int = 10
    weight_per_minute: int = 6000  # For exchanges like Binance
    burst_allowance: int = 5


class StandardizedError(Exception):
    """Standardized error across all exchanges"""
    def __init__(self, error_type: ExchangeErrorType, message: str, original_error: Exception = None, retry_after: float = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error
        self.retry_after = retry_after
        self.timestamp = time.time()


class BaseOrderManager(ABC):
    """Base class for all exchange order managers with comprehensive functionality"""

    def __init__(self, api_key: str, api_secret: str, retry_config: RetryConfig = None, rate_limit_config: RateLimitConfig = None):
        self.api_key = api_key
        self.api_secret = api_secret

        # Time synchronization
        self._cached_server_time_offset: Optional[int] = None
        self._last_sync_time: Optional[float] = None

        # Retry configuration
        self.retry_config = retry_config or RetryConfig()

        # Rate limiting
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self._request_times: List[float] = []
        self._request_weights: List[tuple] = []  # [(timestamp, weight), ...]

        # Error tracking
        self._error_counts: Dict[ExchangeErrorType, int] = {}
        self._last_error_time: Optional[float] = None

    @abstractmethod
    async def get_server_time(self) -> int:
        """Get server timestamp in milliseconds. Each exchange must implement this."""
        pass

    async def get_synchronized_timestamp(self, safety_margin_ms: int = 2000) -> int:
        """
        Get a synchronized timestamp with optional caching to reduce API calls.
        Returns server time + safety margin in milliseconds.
        """
        try:
            # Try to use cached offset if it's fresh (less than 30 seconds old)
            current_time = time.time()
            if (self._cached_server_time_offset is not None and
                self._last_sync_time is not None and
                current_time - self._last_sync_time < 30):

                local_time_ms = int(current_time * 1000)
                synchronized_time = local_time_ms + self._cached_server_time_offset + safety_margin_ms
                logging.debug(f"[{self.__class__.__name__}] Using cached time offset: {self._cached_server_time_offset}ms")
                return synchronized_time

            # Get fresh server time
            server_time = await self.get_server_time()
            local_time_ms = int(current_time * 1000)

            # Calculate and cache offset
            self._cached_server_time_offset = server_time - local_time_ms
            self._last_sync_time = current_time

            synchronized_time = server_time + safety_margin_ms
            logging.debug(f"[{self.__class__.__name__}] Fresh sync - server: {server_time}, local: {local_time_ms}, offset: {self._cached_server_time_offset}ms")
            return synchronized_time

        except Exception as e:
            logging.error(f"[{self.__class__.__name__}] get_synchronized_timestamp error: {e}")
            # Fallback to local time
            return int(time.time() * 1000) + safety_margin_ms

    def clear_time_cache(self):
        """Clear cached time offset. Call this if you suspect time sync issues."""
        self._cached_server_time_offset = None
        self._last_sync_time = None
        logging.debug(f"[{self.__class__.__name__}] Time cache cleared")

    # ===== ERROR HANDLING & RETRY MECHANISMS =====

    @abstractmethod
    def standardize_error(self, raw_error: Exception, response: Dict[str, Any] = None) -> StandardizedError:
        """Convert exchange-specific error to standardized error. Each exchange must implement this."""
        pass

    async def retry_api_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute API call with retry mechanism.

        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            StandardizedError: If all retries are exhausted
        """
        last_error = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Check rate limits before making request
                await self._enforce_rate_limits()

                # Execute the function
                result = await func(*args, **kwargs)

                # Success - reset error counts and return
                if last_error and last_error.error_type in self._error_counts:
                    self._error_counts[last_error.error_type] = 0

                return result

            except Exception as raw_error:
                # Convert to standardized error
                std_error = self.standardize_error(raw_error)
                last_error = std_error

                # Track error
                self._track_error(std_error)

                # Check if error is retryable
                if std_error.error_type not in self.retry_config.retryable_errors:
                    logging.error(f"[{self.__class__.__name__}] Non-retryable error: {std_error}")
                    raise std_error

                # Check if we should continue retrying
                if attempt >= self.retry_config.max_retries:
                    logging.error(f"[{self.__class__.__name__}] Max retries ({self.retry_config.max_retries}) exceeded")
                    raise std_error

                # Calculate delay for next attempt
                delay = self._calculate_retry_delay(attempt, std_error)

                logging.warning(f"[{self.__class__.__name__}] Attempt {attempt + 1}/{self.retry_config.max_retries + 1} failed: {std_error}. Retrying in {delay:.2f}s")

                # Wait before retry
                await asyncio.sleep(delay)

        # This should never be reached, but just in case
        raise last_error

    def _calculate_retry_delay(self, attempt: int, error: StandardizedError) -> float:
        """Calculate delay before next retry attempt."""
        if error.retry_after:
            # Use server-suggested delay
            delay = error.retry_after
        elif self.retry_config.exponential_backoff:
            # Exponential backoff
            delay = min(
                self.retry_config.base_delay * (2 ** attempt),
                self.retry_config.max_delay
            )
        else:
            # Fixed delay
            delay = self.retry_config.base_delay

        # Add jitter to avoid thundering herd
        if self.retry_config.jitter:
            import random
            jitter_factor = 0.1
            jitter = delay * jitter_factor * random.random()
            delay += jitter

        return delay

    def _track_error(self, error: StandardizedError):
        """Track error occurrence for monitoring."""
        self._error_counts[error.error_type] = self._error_counts.get(error.error_type, 0) + 1
        self._last_error_time = error.timestamp

        logging.debug(f"[{self.__class__.__name__}] Error tracked - Type: {error.error_type}, Count: {self._error_counts[error.error_type]}")

    # ===== RATE LIMITING =====

    async def _enforce_rate_limits(self):
        """Enforce rate limiting before making API requests."""
        current_time = time.time()

        # Clean old request records
        self._clean_old_requests(current_time)

        # Check per-second limit
        recent_requests = [t for t in self._request_times if current_time - t < 1.0]
        if len(recent_requests) >= self.rate_limit_config.requests_per_second:
            delay = 1.0 - (current_time - min(recent_requests))
            if delay > 0:
                logging.debug(f"[{self.__class__.__name__}] Rate limit hit, sleeping for {delay:.2f}s")
                await asyncio.sleep(delay)
                current_time = time.time()

        # Check per-minute limit
        minute_requests = [t for t in self._request_times if current_time - t < 60.0]
        if len(minute_requests) >= self.rate_limit_config.requests_per_minute:
            oldest_request = min(minute_requests)
            delay = 60.0 - (current_time - oldest_request)
            if delay > 0:
                logging.warning(f"[{self.__class__.__name__}] Per-minute rate limit hit, sleeping for {delay:.2f}s")
                await asyncio.sleep(delay)
                current_time = time.time()

        # Record this request
        self._request_times.append(current_time)

    def _clean_old_requests(self, current_time: float):
        """Remove old request records to save memory."""
        cutoff_time = current_time - 60.0  # Keep last minute
        self._request_times = [t for t in self._request_times if t > cutoff_time]
        self._request_weights = [(t, w) for t, w in self._request_weights if t > cutoff_time]

    def add_request_weight(self, weight: int):
        """Add weight for weighted rate limiting (e.g., Binance)."""
        current_time = time.time()
        self._request_weights.append((current_time, weight))

        # Check weight-based rate limit
        minute_weight = sum(w for t, w in self._request_weights if current_time - t < 60.0)
        if minute_weight > self.rate_limit_config.weight_per_minute:
            logging.warning(f"[{self.__class__.__name__}] Weight limit exceeded: {minute_weight}/{self.rate_limit_config.weight_per_minute}")

    # ===== CONFIGURATION MANAGEMENT =====

    @abstractmethod
    def get_base_url(self, is_testnet: bool = False) -> str:
        """Get base URL for the exchange. Each exchange must implement this."""
        pass

    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this exchange. Each exchange must implement this."""
        pass

    def validate_api_credentials(self) -> bool:
        """Validate API credentials format."""
        if not self.api_key or not self.api_secret:
            return False

        # Basic validation - each exchange can override for specific rules
        if len(self.api_key) < 10 or len(self.api_secret) < 10:
            return False

        return True

    async def health_check(self) -> bool:
        """Perform basic health check of the exchange connection."""
        try:
            # Try to get server time as a basic connectivity test
            await self.get_server_time()
            return True
        except Exception as e:
            logging.error(f"[{self.__class__.__name__}] Health check failed: {e}")
            return False

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": dict(self._error_counts),
            "last_error_time": self._last_error_time,
            "total_requests": len(self._request_times),
            "recent_requests_per_minute": len([t for t in self._request_times if time.time() - t < 60.0])
        }