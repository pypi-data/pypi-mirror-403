"""Configuration management for quantum-bridge.

This module provides dataclass-based configuration with validation
for execution settings, backend preferences, and fallback behavior.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BackendConfig:
    """Configuration for a specific backend.

    Attributes:
        name: Backend identifier (e.g., "qiskit", "cirq", "simulator")
        priority: Lower numbers = higher priority in fallback chain
        enabled: Whether this backend is available for use
        options: Backend-specific configuration options

    Example:
        >>> config = BackendConfig(name="qiskit", priority=1)
        >>> config.enabled
        True
    """

    name: str
    priority: int = 0
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Backend name cannot be empty")
        if self.priority < 0:
            raise ValueError("Priority cannot be negative")


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior.

    Attributes:
        enabled: Whether automatic fallback is enabled
        max_attempts: Maximum backends to try before giving up
        timeout_seconds: Per-backend execution timeout
        retry_on_timeout: Whether to retry the same backend on timeout

    Example:
        >>> config = FallbackConfig(timeout_seconds=60.0)
        >>> config.max_attempts
        3
    """

    enabled: bool = True
    max_attempts: int = 3
    timeout_seconds: float = 300.0
    retry_on_timeout: bool = False

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass
class MitigationConfig:
    """Configuration for error mitigation.

    Attributes:
        enabled: Whether to apply error mitigation
        technique: Mitigation technique ("zne", "pec", or "none")
        zne_scale_factors: Noise scale factors for ZNE
        zne_extrapolation: Extrapolation method ("linear", "polynomial", "exponential")

    Example:
        >>> config = MitigationConfig(enabled=True, technique="zne")
        >>> config.zne_scale_factors
        (1.0, 2.0, 3.0)
    """

    enabled: bool = False
    technique: str = "zne"
    zne_scale_factors: tuple[float, ...] = (1.0, 2.0, 3.0)
    zne_extrapolation: str = "linear"

    def __post_init__(self) -> None:
        valid_techniques = {"zne", "pec", "none"}
        if self.technique not in valid_techniques:
            raise ValueError(f"technique must be one of {valid_techniques}")

        valid_extrapolations = {"linear", "polynomial", "exponential"}
        if self.zne_extrapolation not in valid_extrapolations:
            raise ValueError(f"zne_extrapolation must be one of {valid_extrapolations}")

        if len(self.zne_scale_factors) < 2:
            raise ValueError("zne_scale_factors must have at least 2 values")


@dataclass
class ExecutionConfig:
    """Main configuration for HybridExecutor.

    This is the primary configuration object that controls all aspects
    of circuit execution, including backend selection, fallback behavior,
    and error mitigation.

    Attributes:
        default_shots: Default number of shots if not specified
        max_qubits: Maximum qubits allowed (0 = no limit)
        fallback: Fallback configuration
        mitigation: Error mitigation configuration
        backends: List of backend configurations (ordered by priority)
        log_level: Logging verbosity ("debug", "info", "warning", "error")

    Example:
        >>> config = ExecutionConfig(default_shots=2048)
        >>> config.fallback.enabled
        True
    """

    default_shots: int = 1024
    max_qubits: int = 0
    fallback: FallbackConfig = field(default_factory=FallbackConfig)
    mitigation: MitigationConfig = field(default_factory=MitigationConfig)
    backends: list[BackendConfig] = field(default_factory=list)
    log_level: str = "info"

    def __post_init__(self) -> None:
        if self.default_shots < 1:
            raise ValueError("default_shots must be at least 1")
        if self.max_qubits < 0:
            raise ValueError("max_qubits cannot be negative")

        valid_log_levels = {"debug", "info", "warning", "error"}
        if self.log_level not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}")

    def get_backend_order(self) -> list[str]:
        """Return backend names sorted by priority.

        Returns:
            List of backend names, lowest priority number first.

        Example:
            >>> config = ExecutionConfig(backends=[
            ...     BackendConfig("simulator", priority=2),
            ...     BackendConfig("qiskit", priority=1),
            ... ])
            >>> config.get_backend_order()
            ['qiskit', 'simulator']
        """
        enabled = [b for b in self.backends if b.enabled]
        sorted_backends = sorted(enabled, key=lambda b: b.priority)
        return [b.name for b in sorted_backends]


def default_config() -> ExecutionConfig:
    """Create a sensible default configuration.

    Returns:
        ExecutionConfig with simulator as primary backend.

    Example:
        >>> config = default_config()
        >>> config.get_backend_order()
        ['simulator']
    """
    return ExecutionConfig(
        backends=[
            BackendConfig(name="simulator", priority=0, enabled=True),
        ],
        fallback=FallbackConfig(enabled=True),
        mitigation=MitigationConfig(enabled=False),
    )


def config_with_qiskit(
    ibm_token: str | None = None,
    instance: str = "ibm-q/open/main",
) -> ExecutionConfig:
    """Create configuration optimized for IBM Quantum.

    This sets up Qiskit as the primary backend with simulator fallback.

    Args:
        ibm_token: IBM Quantum API token (can also use IBM_QUANTUM_TOKEN env var)
        instance: IBM Quantum instance path

    Returns:
        ExecutionConfig with Qiskit primary, simulator fallback.

    Example:
        >>> config = config_with_qiskit()
        >>> config.get_backend_order()
        ['qiskit', 'simulator']
    """
    qiskit_options: dict[str, Any] = {"instance": instance}
    if ibm_token:
        qiskit_options["token"] = ibm_token

    return ExecutionConfig(
        backends=[
            BackendConfig(name="qiskit", priority=0, options=qiskit_options),
            BackendConfig(name="simulator", priority=1),
        ],
        fallback=FallbackConfig(enabled=True, timeout_seconds=300.0),
    )


def config_with_cirq() -> ExecutionConfig:
    """Create configuration optimized for Google Cirq.

    This sets up Cirq as the primary backend with simulator fallback.

    Returns:
        ExecutionConfig with Cirq primary, simulator fallback.

    Example:
        >>> config = config_with_cirq()
        >>> config.get_backend_order()
        ['cirq', 'simulator']
    """
    return ExecutionConfig(
        backends=[
            BackendConfig(name="cirq", priority=0),
            BackendConfig(name="simulator", priority=1),
        ],
        fallback=FallbackConfig(enabled=True),
    )
