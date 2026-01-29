"""
Exception hierarchy for Quantum Bridge.

All exceptions inherit from QuantumBridgeError for easy catch-all handling.
"""


class QuantumBridgeError(Exception):
    """Base exception for all Quantum Bridge errors."""

    pass


class BackendError(QuantumBridgeError):
    """Backend-specific failure."""

    def __init__(self, message: str, backend_name: str | None = None):
        self.backend_name = backend_name
        super().__init__(message)


class BackendUnavailableError(BackendError):
    """Backend is down, unreachable, or not configured."""

    pass


class BackendTimeoutError(BackendError):
    """Execution timed out waiting for backend."""

    def __init__(
        self,
        message: str,
        backend_name: str | None = None,
        timeout_seconds: float | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, backend_name)


class TranspilationError(QuantumBridgeError):
    """Circuit couldn't be transpiled for target backend."""

    def __init__(
        self,
        message: str,
        backend_name: str | None = None,
        unsupported_gates: list[str] | None = None,
    ):
        self.backend_name = backend_name
        self.unsupported_gates = unsupported_gates or []
        super().__init__(message)


class CircuitError(QuantumBridgeError):
    """Invalid circuit (too many qubits, unsupported gates, etc.)."""

    pass


class CircuitConversionError(CircuitError):
    """Failed to convert circuit to internal IR."""

    def __init__(self, message: str, source_type: str | None = None):
        self.source_type = source_type
        super().__init__(message)


class FallbackExhaustedError(QuantumBridgeError):
    """All backends in fallback chain failed."""

    def __init__(self, message: str, attempted_backends: list[str] | None = None):
        self.attempted_backends = attempted_backends or []
        super().__init__(message)


class ConfigurationError(QuantumBridgeError):
    """Invalid configuration."""

    pass


class MitigationError(QuantumBridgeError):
    """Error during error mitigation."""

    pass
