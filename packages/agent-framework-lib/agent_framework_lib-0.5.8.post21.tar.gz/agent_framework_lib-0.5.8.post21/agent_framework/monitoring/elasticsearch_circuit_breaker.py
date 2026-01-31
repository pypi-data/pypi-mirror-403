"""
Elasticsearch Circuit Breaker

This module provides a circuit breaker pattern implementation for Elasticsearch
operations to prevent cascading failures when Elasticsearch is unavailable.

The circuit breaker has three states:
- CLOSED: Normal operation, requests pass through
- OPEN: ES unavailable, requests immediately fail/fallback
- HALF_OPEN: Testing recovery, limited requests allowed

Key Features:
- Automatic failure detection and circuit opening
- Configurable failure threshold
- Recovery timeout with exponential backoff
- Proactive health check background thread
- Thread-safe state management
- Metrics for monitoring

Environment Variables:
- ELASTICSEARCH_CIRCUIT_BREAKER_THRESHOLD: Consecutive failures before opening (default: 5)
- ELASTICSEARCH_CIRCUIT_BREAKER_TIMEOUT: Base recovery timeout in seconds (default: 30)
- ELASTICSEARCH_CIRCUIT_BREAKER_MAX_TIMEOUT: Max recovery timeout in seconds (default: 300)
- ELASTICSEARCH_CIRCUIT_BREAKER_HEALTH_CHECK_INTERVAL: Health check interval in seconds (default: 15)

Example:
    ```python
    from agent_framework.monitoring.elasticsearch_circuit_breaker import ElasticsearchCircuitBreaker

    # Create circuit breaker
    circuit_breaker = ElasticsearchCircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30
    )

    # Check if ES operations should be attempted
    if circuit_breaker.is_available():
        try:
            # Perform ES operation
            result = await es_client.index(...)
            circuit_breaker.record_success()
        except Exception as e:
            circuit_breaker.record_failure()
            # Use fallback
    else:
        # Circuit is open, use fallback immediately
        pass
    ```

Version: 0.2.0
"""

import os
import logging
import time
import asyncio
import threading
from enum import Enum
from threading import Lock, Thread, Event
from typing import Optional, Callable, Any
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, use fallback
    HALF_OPEN = "half_open"  # Testing recovery


class ElasticsearchCircuitBreaker:
    """
    Circuit breaker for Elasticsearch operations.

    Prevents cascading failures by opening the circuit after a threshold of
    consecutive failures. After a recovery timeout (with exponential backoff),
    the circuit transitions to half-open state to test if Elasticsearch has recovered.

    Features:
    - Exponential backoff: recovery timeout doubles after each failed recovery attempt
    - Proactive health check: background thread periodically tests ES availability
    - Separate tracking of circuit open time vs last failure time

    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit
        base_recovery_timeout: Base seconds to wait before attempting recovery
        max_recovery_timeout: Maximum recovery timeout (cap for exponential backoff)
        health_check_interval: Seconds between proactive health checks
        state: Current circuit breaker state
        failure_count: Current count of consecutive failures
        last_failure_time: Timestamp of last failure
        circuit_opened_time: Timestamp when circuit was opened (for recovery timeout)
        consecutive_recovery_failures: Count of failed recovery attempts (for backoff)
        last_state_change: Timestamp of last state change
    """

    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        max_recovery_timeout: Optional[int] = None,
        health_check_interval: Optional[int] = None,
        health_check_fn: Optional[Callable[[], bool]] = None,
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Consecutive failures before opening (default: 5)
            recovery_timeout: Base seconds before attempting recovery (default: 30)
            max_recovery_timeout: Maximum recovery timeout in seconds (default: 300)
            health_check_interval: Seconds between health checks (default: 15)
            health_check_fn: Optional function to test ES availability (returns True if available)
        """
        # Configuration from environment or parameters
        self.failure_threshold = failure_threshold or int(
            os.getenv("ELASTICSEARCH_CIRCUIT_BREAKER_THRESHOLD", "5")
        )
        self.base_recovery_timeout = recovery_timeout or int(
            os.getenv("ELASTICSEARCH_CIRCUIT_BREAKER_TIMEOUT", "30")
        )
        self.max_recovery_timeout = max_recovery_timeout or int(
            os.getenv("ELASTICSEARCH_CIRCUIT_BREAKER_MAX_TIMEOUT", "300")
        )
        self.health_check_interval = health_check_interval or int(
            os.getenv("ELASTICSEARCH_CIRCUIT_BREAKER_HEALTH_CHECK_INTERVAL", "15")
        )

        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.circuit_opened_time: Optional[float] = None  # When circuit was opened
        self.consecutive_recovery_failures: int = 0  # For exponential backoff
        self.last_state_change: float = time.time()

        # Health check
        self._health_check_fn = health_check_fn
        self._health_check_thread: Optional[Thread] = None
        self._stop_health_check = Event()

        # Thread safety
        self._lock = Lock()

        # Backward compatibility
        self.recovery_timeout = self.base_recovery_timeout

        logger.info(
            f"Initialized ElasticsearchCircuitBreaker: "
            f"failure_threshold={self.failure_threshold}, "
            f"base_recovery_timeout={self.base_recovery_timeout}s, "
            f"max_recovery_timeout={self.max_recovery_timeout}s, "
            f"health_check_interval={self.health_check_interval}s"
        )

    def start_health_check(self, health_check_fn: Optional[Callable[[], bool]] = None) -> None:
        """
        Start the proactive health check background thread.

        The health check thread periodically tests ES availability and
        closes the circuit when ES recovers, without waiting for the
        next write attempt.

        Args:
            health_check_fn: Function that returns True if ES is available.
                           If None, uses the one provided at init.
        """
        if health_check_fn:
            self._health_check_fn = health_check_fn

        if not self._health_check_fn:
            logger.warning("Cannot start health check: no health_check_fn provided")
            return

        if self._health_check_thread and self._health_check_thread.is_alive():
            logger.debug("Health check thread already running")
            return

        self._stop_health_check.clear()
        self._health_check_thread = Thread(
            target=self._health_check_loop,
            name="es-circuit-breaker-health-check",
            daemon=True,
        )
        self._health_check_thread.start()
        logger.info(
            f"Started health check thread (interval={self.health_check_interval}s)"
        )

    def stop_health_check(self) -> None:
        """Stop the proactive health check background thread."""
        if not self._health_check_thread:
            return

        self._stop_health_check.set()
        self._health_check_thread.join(timeout=5.0)
        self._health_check_thread = None
        logger.info("Stopped health check thread")

    def _health_check_loop(self) -> None:
        """
        Background loop that proactively checks ES availability.

        When circuit is OPEN and ES becomes available, transitions to
        HALF_OPEN to allow recovery without waiting for next write.
        """
        logger.debug("Health check loop started")

        while not self._stop_health_check.wait(timeout=self.health_check_interval):
            try:
                with self._lock:
                    current_state = self.state

                # Only check when circuit is OPEN
                if current_state != CircuitBreakerState.OPEN:
                    continue

                # Check if recovery timeout has elapsed
                with self._lock:
                    if not self._should_attempt_recovery():
                        current_timeout = self._get_current_recovery_timeout()
                        time_remaining = (
                            current_timeout - (time.time() - self.circuit_opened_time)
                            if self.circuit_opened_time
                            else current_timeout
                        )
                        logger.debug(
                            f"Health check: waiting for recovery timeout "
                            f"({time_remaining:.1f}s remaining)"
                        )
                        continue

                # Test ES availability
                logger.debug("Health check: testing ES availability...")
                try:
                    is_available = self._health_check_fn()
                except Exception as e:
                    logger.warning(f"Health check function failed: {e}")
                    is_available = False

                if is_available:
                    with self._lock:
                        if self.state == CircuitBreakerState.OPEN:
                            self._transition_to_half_open()
                            logger.info(
                                "Health check: ES available, transitioned to HALF_OPEN"
                            )
                else:
                    # ES still unavailable, increase backoff
                    with self._lock:
                        if self.state == CircuitBreakerState.OPEN:
                            self.consecutive_recovery_failures += 1
                            self.circuit_opened_time = time.time()
                            new_timeout = self._get_current_recovery_timeout()
                            logger.warning(
                                f"Health check: ES still unavailable, "
                                f"increasing backoff to {new_timeout:.0f}s "
                                f"(attempt {self.consecutive_recovery_failures})"
                            )

            except Exception as e:
                logger.error(f"Health check loop error: {e}")

        logger.debug("Health check loop stopped")

    def record_failure(self) -> None:
        """
        Record a failure and potentially open the circuit.

        Increments the failure count and opens the circuit if the threshold
        is reached. If failing during HALF_OPEN (recovery attempt), increases
        the backoff multiplier. Thread-safe.
        """
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Check if we should open the circuit
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self._transition_to_open(is_initial_open=True)

            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Failed during recovery test, reopen circuit with increased backoff
                self.consecutive_recovery_failures += 1
                self._transition_to_open(is_initial_open=False)

            logger.debug(
                f"Circuit breaker recorded failure: "
                f"count={self.failure_count}, state={self.state.value}, "
                f"recovery_failures={self.consecutive_recovery_failures}"
            )
    
    def record_success(self) -> None:
        """
        Record a successful operation and potentially close the circuit.

        Resets the failure count, backoff counter, and closes the circuit
        if in half-open state. Thread-safe.
        """
        with self._lock:
            # Reset failure count and backoff
            previous_count = self.failure_count
            previous_recovery_failures = self.consecutive_recovery_failures
            self.failure_count = 0
            self.last_failure_time = None
            self.consecutive_recovery_failures = 0
            self.circuit_opened_time = None

            # Close circuit if in half-open state
            if self.state == CircuitBreakerState.HALF_OPEN:
                self._transition_to_closed()

            if previous_count > 0 or previous_recovery_failures > 0:
                logger.debug(
                    f"Circuit breaker recorded success: "
                    f"reset failure count from {previous_count}, "
                    f"reset recovery failures from {previous_recovery_failures}, "
                    f"state={self.state.value}"
                )
    
    def is_available(self) -> bool:
        """
        Check if Elasticsearch operations should be attempted.
        
        Returns False if circuit is open, True otherwise. Also handles
        automatic transition to half-open state after recovery timeout.
        Thread-safe.
        
        Returns:
            True if operations should be attempted, False otherwise
        """
        with self._lock:
            # Check if we should transition to half-open
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_recovery():
                    self._transition_to_half_open()
            
            # Return availability based on state
            return self.state != CircuitBreakerState.OPEN
    
    def _get_current_recovery_timeout(self) -> float:
        """
        Calculate current recovery timeout with exponential backoff.

        Returns:
            Current recovery timeout in seconds
        """
        # Exponential backoff: base * 2^failures, capped at max
        backoff_multiplier = 2 ** self.consecutive_recovery_failures
        timeout = self.base_recovery_timeout * backoff_multiplier
        return min(timeout, self.max_recovery_timeout)

    def _should_attempt_recovery(self) -> bool:
        """
        Check if enough time has passed to attempt recovery.

        Uses circuit_opened_time (when circuit was opened) instead of
        last_failure_time to avoid the race condition where monitoring
        interval and recovery timeout align.

        Returns:
            True if recovery timeout has elapsed, False otherwise
        """
        if self.circuit_opened_time is None:
            return False

        current_timeout = self._get_current_recovery_timeout()
        time_since_opened = time.time() - self.circuit_opened_time
        should_recover = time_since_opened >= current_timeout

        if should_recover:
            logger.debug(
                f"Recovery check: time_since_opened={time_since_opened:.1f}s >= "
                f"timeout={current_timeout:.1f}s (base={self.base_recovery_timeout}s, "
                f"backoff_failures={self.consecutive_recovery_failures})"
            )

        return should_recover
    
    def _transition_to_open(self, is_initial_open: bool = True) -> None:
        """
        Transition circuit breaker to OPEN state.

        Args:
            is_initial_open: True if this is the first time opening (from CLOSED),
                           False if reopening after failed recovery (from HALF_OPEN)

        Should be called with lock held.
        """
        previous_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.last_state_change = time.time()

        # Only set circuit_opened_time on initial open or if it's None
        # This ensures we track from when the circuit first opened, not from
        # when it reopened after a failed recovery attempt
        if is_initial_open or self.circuit_opened_time is None:
            self.circuit_opened_time = time.time()
            self.consecutive_recovery_failures = 0
        else:
            # Reopening after failed recovery - update circuit_opened_time
            # to start the backoff timer from now
            self.circuit_opened_time = time.time()

        current_timeout = self._get_current_recovery_timeout()

        logger.warning(
            f"Circuit breaker OPENED: "
            f"previous_state={previous_state.value}, "
            f"failure_count={self.failure_count}, "
            f"threshold={self.failure_threshold}, "
            f"recovery_failures={self.consecutive_recovery_failures}, "
            f"next_recovery_in={current_timeout:.0f}s"
        )
    
    def _transition_to_half_open(self) -> None:
        """
        Transition circuit breaker to HALF_OPEN state.
        
        Should be called with lock held.
        """
        previous_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.last_state_change = time.time()
        
        logger.info(
            f"Circuit breaker transitioning to half-open: "
            f"previous_state={previous_state.value}, "
            f"attempting recovery after {self.recovery_timeout}s"
        )
    
    def _transition_to_closed(self) -> None:
        """
        Transition circuit breaker to CLOSED state.
        
        Should be called with lock held.
        """
        previous_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.last_state_change = time.time()
        
        logger.info(
            f"Circuit breaker closed: "
            f"previous_state={previous_state.value}, "
            f"Elasticsearch recovered"
        )
    
    def get_state(self) -> CircuitBreakerState:
        """
        Get the current circuit breaker state.
        
        Thread-safe.
        
        Returns:
            Current circuit breaker state
        """
        with self._lock:
            return self.state
    
    def get_failure_count(self) -> int:
        """
        Get the current failure count.
        
        Thread-safe.
        
        Returns:
            Current consecutive failure count
        """
        with self._lock:
            return self.failure_count
    
    def get_metrics(self) -> dict:
        """
        Get circuit breaker metrics for monitoring.
        
        Thread-safe.
        
        Returns:
            Dictionary containing current metrics
        """
        with self._lock:
            current_timeout = self._get_current_recovery_timeout()
            time_until_recovery = None
            if self.circuit_opened_time and self.state == CircuitBreakerState.OPEN:
                elapsed = time.time() - self.circuit_opened_time
                time_until_recovery = max(0, current_timeout - elapsed)

            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "base_recovery_timeout": self.base_recovery_timeout,
                "max_recovery_timeout": self.max_recovery_timeout,
                "current_recovery_timeout": current_timeout,
                "consecutive_recovery_failures": self.consecutive_recovery_failures,
                "time_until_recovery": time_until_recovery,
                "health_check_active": (
                    self._health_check_thread is not None
                    and self._health_check_thread.is_alive()
                ),
                "last_failure_time": (
                    datetime.fromtimestamp(self.last_failure_time, tz=timezone.utc).isoformat()
                    if self.last_failure_time
                    else None
                ),
                "circuit_opened_time": (
                    datetime.fromtimestamp(self.circuit_opened_time, tz=timezone.utc).isoformat()
                    if self.circuit_opened_time
                    else None
                ),
                "last_state_change": datetime.fromtimestamp(
                    self.last_state_change, tz=timezone.utc
                ).isoformat(),
                "time_since_last_failure": (
                    time.time() - self.last_failure_time
                    if self.last_failure_time
                    else None
                ),
            }
    
    def reset(self) -> None:
        """
        Manually reset the circuit breaker to CLOSED state.
        
        This can be used by administrators to force recovery attempts.
        Thread-safe.
        """
        with self._lock:
            previous_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.circuit_opened_time = None
            self.consecutive_recovery_failures = 0
            self.last_state_change = time.time()
            
            logger.info(
                f"Circuit breaker manually reset: "
                f"previous_state={previous_state.value}"
            )


# Global circuit breaker instance (singleton)
_global_circuit_breaker: Optional[ElasticsearchCircuitBreaker] = None
_circuit_breaker_lock = Lock()


def get_elasticsearch_circuit_breaker() -> ElasticsearchCircuitBreaker:
    """
    Get the global Elasticsearch circuit breaker instance.
    
    Creates a singleton circuit breaker instance on first call.
    Thread-safe.
    
    Returns:
        Global ElasticsearchCircuitBreaker instance
        
    Example:
        ```python
        from agent_framework.monitoring.elasticsearch_circuit_breaker import (
            get_elasticsearch_circuit_breaker
        )
        
        circuit_breaker = get_elasticsearch_circuit_breaker()
        
        if circuit_breaker.is_available():
            # Perform ES operation
            pass
        ```
    """
    global _global_circuit_breaker
    
    with _circuit_breaker_lock:
        if _global_circuit_breaker is None:
            _global_circuit_breaker = ElasticsearchCircuitBreaker()
        
        return _global_circuit_breaker
