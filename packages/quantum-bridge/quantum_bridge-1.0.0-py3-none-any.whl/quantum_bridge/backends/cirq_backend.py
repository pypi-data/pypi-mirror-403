"""
Cirq backend implementation for Google Quantum.

Provides a local Cirq simulator backend. Google Quantum hardware access
requires additional setup with Google Cloud.
"""

import time
from typing import Any

from quantum_bridge.backends.base import (
    BackendCapabilities,
    BackendStatus,
    QuantumBackend,
)
from quantum_bridge.exceptions import (
    BackendError,
    BackendUnavailableError,
)
from quantum_bridge.ir import CircuitIR, Result


# Standard gates supported by Cirq
CIRQ_STANDARD_GATES = frozenset([
    "id", "x", "y", "z", "h", "s", "t", "sdg", "tdg",
    "rx", "ry", "rz",
    "cx", "cnot", "cz", "swap", "iswap",
    "ccx", "toffoli",
])


class CirqBackend(QuantumBackend):
    """
    Backend for Google Cirq simulator.

    This backend uses Cirq's built-in simulator for local execution.
    For Google Quantum hardware, additional configuration is required.

    Example:
        backend = CirqBackend()
        result = backend.run(circuit, shots=1024)
    """

    def __init__(
        self,
        simulator_type: str = "density_matrix",
        noise_model: Any = None,
        seed: int | None = None,
    ):
        """
        Initialize Cirq backend.

        Args:
            simulator_type: Type of simulator ("density_matrix", "state_vector", "clifford")
            noise_model: Optional Cirq noise model
            seed: Random seed for reproducibility
        """
        self._simulator_type = simulator_type
        self._noise_model = noise_model
        self._seed = seed
        self._simulator: Any = None

    @property
    def name(self) -> str:
        return f"cirq:{self._simulator_type}"

    @property
    def capabilities(self) -> BackendCapabilities:
        max_qubits = 25 if self._simulator_type == "density_matrix" else 32

        return BackendCapabilities(
            max_qubits=max_qubits,
            native_gates=CIRQ_STANDARD_GATES,
            supports_mid_circuit_measurement=True,
            is_simulator=True,
            is_local=True,
            max_shots=None,
        )

    def _ensure_simulator(self) -> Any:
        """Lazy-load the Cirq simulator."""
        if self._simulator is not None:
            return self._simulator

        try:
            import cirq

            if self._simulator_type == "density_matrix":
                self._simulator = cirq.DensityMatrixSimulator(
                    noise=self._noise_model,
                    seed=self._seed,
                )
            elif self._simulator_type == "state_vector":
                self._simulator = cirq.Simulator(seed=self._seed)
            elif self._simulator_type == "clifford":
                self._simulator = cirq.CliffordSimulator(seed=self._seed)
            else:
                raise ValueError(f"Unknown simulator type: {self._simulator_type}")

        except ImportError:
            raise BackendUnavailableError(
                "Cirq not installed. Install with: pip install quantum-bridge[cirq]",
                backend_name=self.name,
            )

        return self._simulator

    def run(self, circuit: CircuitIR, shots: int = 1024) -> Result:
        """Execute circuit on Cirq simulator."""
        try:
            import cirq
        except ImportError:
            raise BackendUnavailableError(
                "Cirq not installed. Install with: pip install quantum-bridge[cirq]",
                backend_name=self.name,
            )

        self.validate_circuit(circuit)

        simulator = self._ensure_simulator()
        cirq_circuit = circuit.to_cirq()

        # Ensure circuit has measurements
        if not circuit.measurements:
            # Add measurements for all qubits
            qubits = sorted(cirq_circuit.all_qubits(), key=lambda q: str(q))
            cirq_circuit.append(cirq.measure(*qubits, key="result"))

        start_time = time.time()

        try:
            result = simulator.run(cirq_circuit, repetitions=shots)
        except Exception as e:
            raise BackendError(
                f"Cirq execution failed: {e}",
                backend_name=self.name,
            )

        execution_time = (time.time() - start_time) * 1000

        # Convert Cirq result to counts
        counts = self._result_to_counts(result)

        return Result(
            counts=counts,
            shots=shots,
            backend_name=self.name,
            execution_time_ms=execution_time,
            metadata={
                "simulator_type": self._simulator_type,
            },
        )

    def _result_to_counts(self, result: Any) -> dict[str, int]:
        """Convert Cirq result to counts dictionary."""
        counts: dict[str, int] = {}

        # Get measurement results
        # Cirq stores results per measurement key
        for key in result.measurements:
            data = result.measurements[key]

            for row in data:
                # Convert measurement outcomes to bitstring
                bitstring = "".join(str(bit) for bit in row)
                counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts

    def transpile(self, circuit: CircuitIR) -> CircuitIR:
        """
        Transpile circuit for Cirq.

        Cirq's decomposition happens automatically during simulation,
        so this just validates the circuit.
        """
        # For now, just return the circuit unchanged
        # Cirq handles decomposition internally
        return circuit

    def health_check(self) -> bool:
        """Check if Cirq simulator is available."""
        try:
            self._ensure_simulator()
            return True
        except Exception:
            return False

    def status(self) -> BackendStatus:
        """Get simulator status."""
        if self.health_check():
            return BackendStatus(
                available=True,
                queue_depth=0,
                message=f"Cirq {self._simulator_type} simulator ready",
            )
        else:
            return BackendStatus(
                available=False,
                message="Cirq not available - install with: pip install cirq",
            )


class CirqSamplerBackend(QuantumBackend):
    """
    Backend using Cirq's Sampler interface.

    This can wrap any Cirq-compatible sampler, including
    hardware samplers from IonQ, Rigetti, etc. via cirq-* packages.
    """

    def __init__(self, sampler: Any, name: str = "cirq_sampler"):
        """
        Initialize with a Cirq Sampler.

        Args:
            sampler: Any Cirq Sampler implementation
            name: Name for this backend instance
        """
        self._sampler = sampler
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> BackendCapabilities:
        # Conservative defaults - actual capabilities depend on sampler
        return BackendCapabilities(
            max_qubits=20,
            native_gates=CIRQ_STANDARD_GATES,
            supports_mid_circuit_measurement=False,
            is_simulator=False,  # Assume hardware
            is_local=False,
        )

    def run(self, circuit: CircuitIR, shots: int = 1024) -> Result:
        """Execute circuit via sampler."""
        try:
            import cirq
        except ImportError:
            raise BackendUnavailableError(
                "Cirq not installed",
                backend_name=self.name,
            )

        self.validate_circuit(circuit)
        cirq_circuit = circuit.to_cirq()

        # Ensure measurements
        if not circuit.measurements:
            qubits = sorted(cirq_circuit.all_qubits(), key=lambda q: str(q))
            cirq_circuit.append(cirq.measure(*qubits, key="result"))

        start_time = time.time()

        try:
            result = self._sampler.run(cirq_circuit, repetitions=shots)
        except Exception as e:
            raise BackendError(
                f"Sampler execution failed: {e}",
                backend_name=self.name,
            )

        execution_time = (time.time() - start_time) * 1000

        # Convert to counts
        counts: dict[str, int] = {}
        for key in result.measurements:
            data = result.measurements[key]
            for row in data:
                bitstring = "".join(str(bit) for bit in row)
                counts[bitstring] = counts.get(bitstring, 0) + 1

        return Result(
            counts=counts,
            shots=shots,
            backend_name=self.name,
            execution_time_ms=execution_time,
        )

    def health_check(self) -> bool:
        """Check sampler health."""
        try:
            # Try to verify sampler is callable
            return hasattr(self._sampler, "run")
        except Exception:
            return False
