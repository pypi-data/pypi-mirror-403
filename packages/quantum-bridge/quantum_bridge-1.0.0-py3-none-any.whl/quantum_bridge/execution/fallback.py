"""Fallback chain management for backend failures.

This module implements the automatic fallback logic that allows the executor
to gracefully handle backend failures by trying alternative backends.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from quantum_bridge.config import FallbackConfig

if TYPE_CHECKING:
    from quantum_bridge.backends.base import QuantumBackend
    from quantum_bridge.ir import CircuitIR, Result

logger = logging.getLogger(__name__)


@dataclass
class FallbackAttempt:
    """Record of a single execution attempt.

    Attributes:
        backend_name: Which backend was tried
        success: Whether execution succeeded
        error: Exception if failed, None if succeeded
        duration_ms: How long the attempt took
    """

    backend_name: str
    success: bool
    error: Exception | None
    duration_ms: float


@dataclass
class FallbackHistory:
    """History of all attempts during a fallback chain execution.

    Useful for debugging and understanding why certain backends were used.

    Attributes:
        attempts: List of all attempted executions
        final_backend: Which backend ultimately succeeded (or None)
    """

    attempts: list[FallbackAttempt] = field(default_factory=list)
    final_backend: str | None = None

    def add_attempt(
        self,
        backend_name: str,
        success: bool,
        error: Exception | None,
        duration_ms: float,
    ) -> None:
        """Record an execution attempt."""
        self.attempts.append(
            FallbackAttempt(
                backend_name=backend_name,
                success=success,
                error=error,
                duration_ms=duration_ms,
            )
        )
        if success:
            self.final_backend = backend_name

    @property
    def total_attempts(self) -> int:
        """Total number of backends tried."""
        return len(self.attempts)

    @property
    def failed_backends(self) -> list[str]:
        """List of backends that failed."""
        return [a.backend_name for a in self.attempts if not a.success]


class FallbackChain:
    """Manages fallback between multiple backends.

    The fallback chain tries backends in priority order until one succeeds.
    It handles various failure modes:
    - Backend unavailable/unreachable
    - Execution timeout
    - Runtime errors during execution

    **How fallback works:**

    1. Backends are ordered by priority (from configuration)
    2. We try the highest-priority backend first
    3. If it fails, we log the error and try the next backend
    4. We continue until one succeeds or all backends are exhausted

    Example:
        >>> chain = FallbackChain([qiskit_backend, simulator_backend])
        >>> result = chain.execute(circuit, shots=1024)
        >>> print(chain.last_history.final_backend)  # 'simulator' if qiskit failed

    Attributes:
        backends: List of available backends
        config: Fallback configuration
        last_history: History of the most recent execution
        current_backend: The backend currently being used
    """

    def __init__(
        self,
        backends: list[QuantumBackend],
        config: FallbackConfig | None = None,
    ) -> None:
        """Initialize the fallback chain.

        Args:
            backends: List of backends in priority order.
            config: Fallback configuration. Defaults to standard config.

        Raises:
            ValueError: If no backends are provided.
        """
        if not backends:
            raise ValueError("At least one backend is required")

        self._backends = {b.name: b for b in backends}
        self._priority_order = [b.name for b in backends]
        self.config = config or FallbackConfig()
        self.last_history: FallbackHistory | None = None
        self._current_backend: QuantumBackend | None = None

    @property
    def current_backend(self) -> QuantumBackend | None:
        """The backend that was last successfully used."""
        return self._current_backend

    def get_order(self) -> list[str]:
        """Return the current backend priority order.

        Returns:
            List of backend names in priority order.
        """
        return list(self._priority_order)

    def reorder(self, backend_names: list[str]) -> None:
        """Change the backend priority order.

        Args:
            backend_names: New priority order. Must contain only known backends.

        Raises:
            ValueError: If an unknown backend is specified.
        """
        for name in backend_names:
            if name not in self._backends:
                raise ValueError(f"Unknown backend: {name}")
        self._priority_order = list(backend_names)

    def disable_backend(self, name: str) -> None:
        """Temporarily disable a backend from the fallback chain.

        Args:
            name: Backend name to disable.
        """
        if name in self._priority_order:
            self._priority_order.remove(name)
            logger.info("Disabled backend: %s", name)

    def enable_backend(self, name: str, priority: int | None = None) -> None:
        """Re-enable a previously disabled backend.

        Args:
            name: Backend name to enable.
            priority: Position in priority order (0 = highest). If None, appends.
        """
        if name not in self._backends:
            raise ValueError(f"Unknown backend: {name}")

        if name not in self._priority_order:
            if priority is not None and 0 <= priority <= len(self._priority_order):
                self._priority_order.insert(priority, name)
            else:
                self._priority_order.append(name)
            logger.info("Enabled backend: %s at priority %s", name, priority)

    def health_check(self) -> dict[str, bool]:
        """Check health of all backends.

        Returns:
            Dictionary mapping backend names to health status.
        """
        status = {}
        for name, backend in self._backends.items():
            try:
                status[name] = backend.health_check()
            except Exception as e:
                logger.warning("Health check failed for %s: %s", name, e)
                status[name] = False
        return status

    def execute(
        self,
        circuit: CircuitIR,
        shots: int,
    ) -> Result:
        """Execute circuit with automatic fallback on failure.

        Tries backends in priority order until one succeeds. Records
        all attempts in the history for debugging.

        Args:
            circuit: The circuit to execute (in IR format).
            shots: Number of measurement shots.

        Returns:
            Result from the first successful backend.

        Raises:
            FallbackExhaustedError: If all backends fail.
            BackendError: If a backend error occurs and fallback is disabled.
        """
        from quantum_bridge.exceptions import (
            BackendError,
            BackendTimeoutError,
            BackendUnavailableError,
            FallbackExhaustedError,
        )

        if not self.config.enabled:
            # No fallback - try only the first backend
            return self._execute_single(
                self._backends[self._priority_order[0]],
                circuit,
                shots,
            )

        history = FallbackHistory()
        last_error: Exception | None = None
        attempts = 0

        for backend_name in self._priority_order:
            if attempts >= self.config.max_attempts:
                logger.warning("Max fallback attempts (%d) reached", self.config.max_attempts)
                break

            backend = self._backends[backend_name]
            attempts += 1

            logger.debug("Attempting execution on %s (attempt %d)", backend_name, attempts)

            start_time = time.time()
            try:
                result = self._execute_single(backend, circuit, shots)
                duration_ms = (time.time() - start_time) * 1000

                history.add_attempt(backend_name, True, None, duration_ms)
                self.last_history = history
                self._current_backend = backend

                logger.info(
                    "Successfully executed on %s after %d attempt(s)",
                    backend_name,
                    attempts,
                )
                return result

            except BackendTimeoutError as e:
                duration_ms = (time.time() - start_time) * 1000
                history.add_attempt(backend_name, False, e, duration_ms)
                last_error = e
                logger.warning("Backend %s timed out: %s", backend_name, e)

            except BackendUnavailableError as e:
                duration_ms = (time.time() - start_time) * 1000
                history.add_attempt(backend_name, False, e, duration_ms)
                last_error = e
                logger.warning("Backend %s unavailable: %s", backend_name, e)

            except BackendError as e:
                duration_ms = (time.time() - start_time) * 1000
                history.add_attempt(backend_name, False, e, duration_ms)
                last_error = e
                logger.warning("Backend %s error: %s", backend_name, e)

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                history.add_attempt(backend_name, False, e, duration_ms)
                last_error = e
                logger.warning("Unexpected error on %s: %s", backend_name, e)

        self.last_history = history
        raise FallbackExhaustedError(
            f"All {attempts} backend(s) failed. "
            f"Tried: {history.failed_backends}. "
            f"Last error: {last_error}"
        )

    def _execute_single(
        self,
        backend: QuantumBackend,
        circuit: CircuitIR,
        shots: int,
    ) -> Result:
        """Execute on a single backend with timeout handling.

        Args:
            backend: The backend to use.
            circuit: The circuit to execute.
            shots: Number of shots.

        Returns:
            Execution result.

        Raises:
            BackendTimeoutError: If execution exceeds timeout.
            BackendUnavailableError: If backend is not available.
            BackendError: If execution fails.
        """
        from quantum_bridge.exceptions import (
            BackendTimeoutError,
            BackendUnavailableError,
        )

        # Check backend health first
        try:
            if not backend.health_check():
                raise BackendUnavailableError(f"Backend {backend.name} health check failed")
        except Exception as e:
            raise BackendUnavailableError(f"Backend {backend.name} unreachable: {e}") from e

        # Execute with timeout
        # Note: Real timeout handling would use threading/asyncio
        # For now, we rely on the backend's internal timeout
        start = time.time()
        result = backend.run(circuit, shots)
        elapsed = time.time() - start

        if elapsed > self.config.timeout_seconds:
            raise BackendTimeoutError(
                f"Backend {backend.name} exceeded timeout "
                f"({elapsed:.1f}s > {self.config.timeout_seconds}s)"
            )

        return result
