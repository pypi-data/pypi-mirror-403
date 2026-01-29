"""
Abstract base class for quantum backends.

All backend implementations must inherit from QuantumBackend and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from quantum_bridge.ir import CircuitIR, Result


@dataclass(frozen=True)
class BackendCapabilities:
    """
    Capabilities and constraints of a quantum backend.

    Attributes:
        max_qubits: Maximum number of qubits supported
        native_gates: Set of natively supported gate names
        supports_mid_circuit_measurement: Whether mid-circuit measurement is supported
        is_simulator: Whether this is a classical simulator
        is_local: Whether the backend runs locally (vs cloud)
        max_shots: Maximum shots per execution (None = unlimited)
        coupling_map: Qubit connectivity, or None if fully connected
    """

    max_qubits: int
    native_gates: frozenset[str]
    supports_mid_circuit_measurement: bool = False
    is_simulator: bool = True
    is_local: bool = True
    max_shots: int | None = None
    coupling_map: tuple[tuple[int, int], ...] | None = None

    def supports_gate(self, gate_name: str) -> bool:
        """Check if a gate is natively supported."""
        return gate_name.lower() in self.native_gates

    def can_run_circuit(self, circuit: CircuitIR) -> tuple[bool, str | None]:
        """
        Check if a circuit can run on this backend.

        Returns:
            Tuple of (can_run, reason_if_not)
        """
        if circuit.num_qubits > self.max_qubits:
            return False, f"Circuit has {circuit.num_qubits} qubits, backend supports {self.max_qubits}"

        # Check for unsupported gates
        unsupported = set()
        for gate in circuit.gates:
            if not self.supports_gate(gate.name):
                unsupported.add(gate.name)

        if unsupported:
            return False, f"Unsupported gates: {', '.join(sorted(unsupported))}"

        return True, None


@dataclass
class BackendStatus:
    """
    Current status of a backend.

    Attributes:
        available: Whether the backend is currently available
        queue_depth: Number of jobs in queue (if applicable)
        message: Human-readable status message
        last_calibration: ISO timestamp of last calibration (for real hardware)
        error_rate: Current average error rate (if known)
    """

    available: bool
    queue_depth: int = 0
    message: str = ""
    last_calibration: str | None = None
    error_rate: float | None = None


class QuantumBackend(ABC):
    """
    Abstract base class for quantum backends.

    Implementations must provide:
    - run(): Execute a circuit and return results
    - capabilities: Backend capabilities
    - name: Unique backend identifier
    - health_check(): Verify backend is responsive

    Optional overrides:
    - transpile(): Optimize circuit for this backend
    - status(): Get current backend status
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this backend."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """Get backend capabilities."""
        ...

    @abstractmethod
    def run(self, circuit: CircuitIR, shots: int = 1024) -> Result:
        """
        Execute a circuit on this backend.

        Args:
            circuit: Circuit to execute (in IR format)
            shots: Number of shots (repetitions)

        Returns:
            Execution result with counts

        Raises:
            BackendError: If execution fails
            BackendTimeoutError: If execution times out
            TranspilationError: If circuit cannot be transpiled
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the backend is responsive and available.

        Returns:
            True if backend is healthy, False otherwise
        """
        ...

    def transpile(self, circuit: CircuitIR) -> CircuitIR:
        """
        Optimize/transpile a circuit for this backend.

        Default implementation returns the circuit unchanged.
        Backends should override this to perform gate decomposition,
        routing, and optimization.

        Args:
            circuit: Input circuit

        Returns:
            Transpiled circuit optimized for this backend
        """
        return circuit

    def status(self) -> BackendStatus:
        """
        Get current backend status.

        Default implementation checks health and returns basic status.
        """
        available = self.health_check()
        return BackendStatus(
            available=available,
            message="Backend is available" if available else "Backend unavailable",
        )

    def validate_circuit(self, circuit: CircuitIR) -> None:
        """
        Validate that a circuit can run on this backend.

        Raises:
            CircuitError: If circuit is incompatible
        """
        from quantum_bridge.exceptions import CircuitError

        can_run, reason = self.capabilities.can_run_circuit(circuit)
        if not can_run:
            raise CircuitError(f"Circuit incompatible with backend '{self.name}': {reason}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
