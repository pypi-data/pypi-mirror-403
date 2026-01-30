import logging
import time
from enum import Enum
from typing import Dict, Any

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.alert import Alert
from ..models.measurement import Measurement
from ..utils.common import human_readable_time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures.

    When the failure threshold is exceeded, the circuit opens and rejects
    requests for a cooldown period. After cooldown, it allows a test request
    to check if the service has recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            half_open_max_calls: Number of test calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
        return self._state

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        return False  # OPEN state

    def record_success(self):
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            logger.info("Circuit breaker CLOSED - service recovered")
        elif self._state == CircuitState.CLOSED:
            # Decay failure count on success
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker OPEN - recovery test failed")
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker OPEN - {self._failure_count} consecutive failures"
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "time_since_last_failure": (
                time.time() - self._last_failure_time
                if self._last_failure_time > 0 else None
            )
        }


class APIService:
    def __init__(
            self,
            endpoints: Dict[str, Dict[str, Dict[str, Any]]],
            max_retries: int,
            retry_interval: int,
            circuit_failure_threshold: int = 5,
            circuit_recovery_timeout: float = 60.0
    ):
        self.endpoints = endpoints
        self.max_retries = max_retries
        self.retry_interval = retry_interval

        # Create persistent session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=10,  # Max 10 concurrent connections
            limit_per_host=5,  # Max 5 connections per host
            ttl_dns_cache=300,  # DNS cache for 5 minutes
            keepalive_timeout=60  # Keep connections alive for 60s
        )

        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

        # Circuit breaker to prevent cascading failures
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout
        )

        logger.info("API service initialized with HTTP connection pooling and circuit breaker")

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            logger.info("API service session closed")

    def _get_client_type(self, target_table: str) -> str:
        """Map target_table to API client_type.

        Args:
            target_table: The target table name (distribution, substation, water)

        Returns:
            API client_type in uppercase (DISTRIBUTION, SUBSTATION, WATER)
        """
        if target_table:
            return target_table.upper()
        return "DISTRIBUTION"  # Default to DISTRIBUTION if not specified

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8)  # Reduced from 4-10 to 2-8
    )
    async def send_measurement(self, measurement: Measurement) -> bool:
        """Sends a measurement to the API. Logs errors without raising exceptions.

        Uses circuit breaker pattern to prevent cascading failures when the
        backend API is unavailable.
        """
        # Check circuit breaker state
        if not self._circuit_breaker.can_execute():
            logger.warning(
                f"Circuit breaker OPEN - skipping measurement send for {measurement.device_id}"
            )
            return False

        endpoint = self.endpoints[measurement.device_type]["measurements"]
        payload = {
            "client_id": measurement.device_id,
            "timestamp": measurement.timestamp,
        }

        # Add client_type based on target_table (new unified API format)
        if measurement.device_type.lower() == "electrical":
            payload["client_type"] = self._get_client_type(measurement.target_table)

        nan_sample = False
        for k, v in measurement.values.items():
            if measurement.device_type.lower() == "electrical":
                if isinstance(v, list):
                    logger.warning(f"invalid data for: {measurement.device_id} at time: {human_readable_time(measurement.timestamp)}")
                    return True
                if str(v).lower() == "nan":
                    nan_sample = True
            payload[k] = v

        # Log payload field count for debugging
        logger.info(f"HTTP payload for {measurement.device_id}: {len(payload)} fields - keys: {list(payload.keys())}")

        try:
            # Use persistent session instead of creating new one
            async with self.session.post(
                    endpoint["url"],
                    json=[payload],
                    headers=endpoint["headers"]
            ) as response:
                if response.status == 200:
                    self._circuit_breaker.record_success()
                    return True
                else:
                    response_text = await response.text()
                    logger.error(f"Failed to send measurement: {response.status} {response.reason} - URL: {endpoint['url']} - Response: {response_text[:500]}")
                    logger.debug(f"Payload was: {payload}")
                    # Record failure for server errors (5xx), not client errors (4xx)
                    if response.status >= 500:
                        self._circuit_breaker.record_failure()
                    return nan_sample
        except Exception as e:
            logger.error(f"Error sending measurement: {e}", exc_info=True)
            self._circuit_breaker.record_failure()
            return False  # Ensure the exception does not propagate

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8)  # Reduced from 4-10 to 2-8
    )
    async def send_alert(self, alert: Alert) -> bool:
        """Sends an alert to the API. Logs errors without raising exceptions.

        Uses circuit breaker pattern to prevent cascading failures.
        """
        # Check circuit breaker state
        if not self._circuit_breaker.can_execute():
            logger.warning(
                f"Circuit breaker OPEN - skipping alert send for {alert.device_id}"
            )
            return False

        endpoint = self.endpoints[alert.device_type]["alerts"]
        try:
            # Use persistent session instead of creating new one
            async with self.session.post(
                    endpoint["url"],
                    json=[alert.to_dict()],
                    headers=endpoint["headers"]
            ) as response:
                if response.status == 200:
                    self._circuit_breaker.record_success()
                    return True
                else:
                    logger.error(f"Failed to send alert: {response.status} {response.reason}")
                    # Record failure for server errors (5xx)
                    if response.status >= 500:
                        self._circuit_breaker.record_failure()
                    return False
        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)
            self._circuit_breaker.record_failure()
            return False  # Ensure the exception does not propagate

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics for monitoring."""
        return self._circuit_breaker.get_stats()