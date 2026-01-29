"""
Qiskit backend implementation for IBM Quantum.

Supports both IBM Quantum hardware (via qiskit-ibm-runtime) and
local Aer simulator.
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
    BackendTimeoutError,
    BackendUnavailableError,
    TranspilationError,
)
from quantum_bridge.ir import CircuitIR, Result


# Standard gates supported by most IBM backends
IBM_STANDARD_GATES = frozenset([
    "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "u", "u1", "u2", "u3", "p",
    "cx", "cz", "swap", "ccx", "ecr", "sx", "sxdg",
])


class QiskitBackend(QuantumBackend):
    """
    Backend for IBM Quantum via Qiskit.

    Can connect to:
    - Real IBM Quantum hardware (requires IBM Quantum account)
    - Local Aer simulator (no account needed)

    Example:
        # Use local Aer simulator
        backend = QiskitBackend()

        # Use IBM Quantum hardware
        backend = QiskitBackend(backend_name="ibm_brisbane", use_ibm=True)
    """

    def __init__(
        self,
        backend_name: str = "aer_simulator",
        use_ibm: bool = False,
        optimization_level: int = 1,
        timeout_seconds: float = 300.0,
    ):
        """
        Initialize Qiskit backend.

        Args:
            backend_name: Name of backend ("aer_simulator" or IBM backend name)
            use_ibm: If True, connect to IBM Quantum cloud
            optimization_level: Transpilation optimization (0-3)
            timeout_seconds: Timeout for job execution
        """
        self._backend_name = backend_name
        self._use_ibm = use_ibm
        self._optimization_level = optimization_level
        self._timeout_seconds = timeout_seconds
        self._qiskit_backend: Any = None
        self._capabilities: BackendCapabilities | None = None

    @property
    def name(self) -> str:
        return f"qiskit:{self._backend_name}"

    @property
    def capabilities(self) -> BackendCapabilities:
        if self._capabilities is None:
            self._capabilities = self._get_capabilities()
        return self._capabilities

    def _ensure_backend(self) -> Any:
        """Lazy-load the Qiskit backend."""
        if self._qiskit_backend is not None:
            return self._qiskit_backend

        try:
            if self._use_ibm:
                from qiskit_ibm_runtime import QiskitRuntimeService

                service = QiskitRuntimeService()
                self._qiskit_backend = service.backend(self._backend_name)
            else:
                from qiskit_aer import AerSimulator

                if self._backend_name == "aer_simulator":
                    self._qiskit_backend = AerSimulator()
                else:
                    # Try to get noise model from IBM backend name
                    self._qiskit_backend = AerSimulator()

        except ImportError as e:
            if "qiskit_ibm_runtime" in str(e):
                raise BackendUnavailableError(
                    "qiskit-ibm-runtime not installed. Install with: "
                    "pip install quantum-bridge[qiskit]",
                    backend_name=self.name,
                )
            elif "qiskit_aer" in str(e):
                raise BackendUnavailableError(
                    "qiskit-aer not installed. Install with: "
                    "pip install quantum-bridge[qiskit]",
                    backend_name=self.name,
                )
            raise BackendUnavailableError(str(e), backend_name=self.name)
        except Exception as e:
            raise BackendUnavailableError(
                f"Failed to initialize Qiskit backend: {e}",
                backend_name=self.name,
            )

        return self._qiskit_backend

    def _get_capabilities(self) -> BackendCapabilities:
        """Get backend capabilities."""
        try:
            backend = self._ensure_backend()

            # Try to get from backend configuration
            if hasattr(backend, "configuration"):
                config = backend.configuration()
                max_qubits = config.n_qubits
                coupling = None
                if hasattr(config, "coupling_map") and config.coupling_map:
                    coupling = tuple(tuple(pair) for pair in config.coupling_map)

                return BackendCapabilities(
                    max_qubits=max_qubits,
                    native_gates=IBM_STANDARD_GATES,
                    supports_mid_circuit_measurement=False,
                    is_simulator=self._backend_name == "aer_simulator",
                    is_local=not self._use_ibm,
                    max_shots=100000,
                    coupling_map=coupling,
                )

            # Fallback for Aer simulator
            return BackendCapabilities(
                max_qubits=29,  # Aer default
                native_gates=IBM_STANDARD_GATES,
                supports_mid_circuit_measurement=True,
                is_simulator=True,
                is_local=True,
                max_shots=None,
            )

        except Exception:
            # Return conservative defaults
            return BackendCapabilities(
                max_qubits=5,
                native_gates=IBM_STANDARD_GATES,
                is_simulator=not self._use_ibm,
                is_local=not self._use_ibm,
            )

    def run(self, circuit: CircuitIR, shots: int = 1024) -> Result:
        """Execute circuit on Qiskit backend."""
        try:
            from qiskit import transpile as qiskit_transpile
        except ImportError:
            raise BackendUnavailableError(
                "Qiskit not installed. Install with: pip install quantum-bridge[qiskit]",
                backend_name=self.name,
            )

        self.validate_circuit(circuit)

        backend = self._ensure_backend()
        qc = circuit.to_qiskit()

        # Transpile for target backend
        try:
            transpiled = qiskit_transpile(
                qc,
                backend=backend,
                optimization_level=self._optimization_level,
            )
        except Exception as e:
            raise TranspilationError(
                f"Transpilation failed: {e}",
                backend_name=self.name,
            )

        # Execute
        start_time = time.time()

        try:
            if self._use_ibm:
                # IBM Runtime execution
                from qiskit_ibm_runtime import SamplerV2 as Sampler

                sampler = Sampler(backend)
                job = sampler.run([transpiled], shots=shots)

                # Wait for result with timeout
                try:
                    result = job.result(timeout=self._timeout_seconds)
                except Exception as e:
                    if "timeout" in str(e).lower():
                        raise BackendTimeoutError(
                            f"Execution timed out after {self._timeout_seconds}s",
                            backend_name=self.name,
                            timeout_seconds=self._timeout_seconds,
                        )
                    raise

                # Extract counts from sampler result
                pub_result = result[0]
                counts = pub_result.data.meas.get_counts()

            else:
                # Local Aer execution
                job = backend.run(transpiled, shots=shots)
                result = job.result()
                counts = result.get_counts()

        except BackendTimeoutError:
            raise
        except Exception as e:
            raise BackendError(
                f"Execution failed: {e}",
                backend_name=self.name,
            )

        execution_time = (time.time() - start_time) * 1000

        return Result(
            counts=dict(counts),
            shots=shots,
            backend_name=self.name,
            execution_time_ms=execution_time,
            metadata={
                "transpiled_depth": transpiled.depth(),
                "transpiled_gates": transpiled.count_ops(),
            },
        )

    def transpile(self, circuit: CircuitIR) -> CircuitIR:
        """Transpile circuit for this backend."""
        try:
            from qiskit import transpile as qiskit_transpile
        except ImportError:
            return circuit  # Return unchanged if qiskit unavailable

        backend = self._ensure_backend()
        qc = circuit.to_qiskit()

        transpiled = qiskit_transpile(
            qc,
            backend=backend,
            optimization_level=self._optimization_level,
        )

        # Convert back to IR
        return CircuitIR.from_qiskit(transpiled)

    def health_check(self) -> bool:
        """Check if backend is available."""
        try:
            backend = self._ensure_backend()

            if self._use_ibm:
                # Check IBM backend status
                status = backend.status()
                return status.operational and status.status_msg == "active"
            else:
                # Local simulator is always healthy
                return True

        except Exception:
            return False

    def status(self) -> BackendStatus:
        """Get detailed backend status."""
        try:
            backend = self._ensure_backend()

            if self._use_ibm:
                status = backend.status()
                return BackendStatus(
                    available=status.operational,
                    queue_depth=status.pending_jobs,
                    message=status.status_msg,
                )
            else:
                return BackendStatus(
                    available=True,
                    queue_depth=0,
                    message="Local simulator ready",
                )

        except Exception as e:
            return BackendStatus(
                available=False,
                message=f"Error checking status: {e}",
            )
