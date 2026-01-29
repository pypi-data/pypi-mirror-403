"""Hybrid execution engine for quantum circuits.

The HybridExecutor orchestrates circuit execution across multiple backends
with automatic fallback, error mitigation, and result normalization.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from quantum_bridge.config import ExecutionConfig, default_config
from quantum_bridge.execution.fallback import FallbackChain

if TYPE_CHECKING:
    from quantum_bridge.backends.base import QuantumBackend
    from quantum_bridge.ir import CircuitIR, Result

logger = logging.getLogger(__name__)


@dataclass
class ExecutionPlan:
    """Pre-execution plan showing what will happen.

    Use executor.plan() to get a plan before executing. This lets users
    inspect and approve the execution strategy.

    Attributes:
        circuit_info: Summary of the circuit (qubits, gates, depth)
        selected_backend: Primary backend that will be used
        fallback_chain: Ordered list of fallback backends
        estimated_shots: Number of shots to execute
        mitigation_enabled: Whether error mitigation will be applied
        warnings: Any warnings about the execution plan

    Example:
        >>> plan = executor.plan(circuit, shots=1024)
        >>> print(f"Will run on: {plan.selected_backend}")
        >>> result = executor.execute(plan)
    """

    circuit_info: dict[str, Any]
    selected_backend: str
    fallback_chain: list[str]
    estimated_shots: int
    mitigation_enabled: bool
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            f"Execution Plan:",
            f"  Circuit: {self.circuit_info.get('num_qubits', '?')} qubits, "
            f"{self.circuit_info.get('gate_count', '?')} gates",
            f"  Backend: {self.selected_backend}",
            f"  Fallback: {' -> '.join(self.fallback_chain) if self.fallback_chain else 'none'}",
            f"  Shots: {self.estimated_shots}",
            f"  Mitigation: {'enabled' if self.mitigation_enabled else 'disabled'}",
        ]
        if self.warnings:
            lines.append(f"  Warnings: {'; '.join(self.warnings)}")
        return "\n".join(lines)


@dataclass
class BatchResult:
    """Result from batch execution of multiple circuits.

    Handles partial failures gracefully - some circuits may succeed
    while others fail.

    Attributes:
        results: List of results (None for failed circuits)
        errors: List of exceptions (None for successful circuits)
        succeeded: Count of successful executions
        failed: Count of failed executions

    Example:
        >>> batch = executor.execute_batch([circuit1, circuit2, circuit3])
        >>> for i, result in enumerate(batch.results):
        ...     if result is not None:
        ...         print(f"Circuit {i}: {result.counts}")
        ...     else:
        ...         print(f"Circuit {i} failed: {batch.errors[i]}")
    """

    results: list[Result | None]
    errors: list[Exception | None]
    succeeded: int
    failed: int

    @property
    def all_succeeded(self) -> bool:
        """Check if all circuits executed successfully."""
        return self.failed == 0

    def successful_results(self) -> list[Result]:
        """Get only the successful results, filtering out None values."""
        return [r for r in self.results if r is not None]


class HybridExecutor:
    """Main execution engine for quantum circuits.

    The HybridExecutor provides a unified interface for running quantum
    circuits across multiple backends with automatic fallback and
    error mitigation.

    **For Python developers learning quantum computing:**

    Quantum circuits are like programs for quantum computers. They consist of:
    - **Qubits**: Quantum bits that can be 0, 1, or both at once (superposition)
    - **Gates**: Operations that manipulate qubits (like H for superposition, CX for entanglement)
    - **Measurements**: Reading the final qubit states (collapses to 0 or 1)

    The executor handles the complexity of:
    - Choosing the best available backend (real quantum computer or simulator)
    - Automatically falling back if a backend fails
    - Optionally applying error mitigation to improve result quality

    Example:
        >>> from quantum_bridge import HybridExecutor
        >>> from quantum_bridge.backends import get_backend
        >>>
        >>> # Create executor with simulator backend
        >>> executor = HybridExecutor([get_backend("simulator")])
        >>>
        >>> # Run a circuit (can be Qiskit, Cirq, or QASM string)
        >>> result = executor.execute(my_circuit, shots=1024)
        >>> print(result.counts)  # {'00': 512, '11': 512}

    Attributes:
        backends: List of available backends
        config: Execution configuration
        fallback_chain: Manages fallback between backends
    """

    def __init__(
        self,
        backends: list[QuantumBackend] | None = None,
        config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize the executor with backends and configuration.

        Args:
            backends: List of backend instances to use. If None, will attempt
                to discover available backends based on installed packages.
            config: Execution configuration. If None, uses sensible defaults.

        Raises:
            ValueError: If no backends are provided or available.
        """
        self.config = config or default_config()
        self._backends: dict[str, QuantumBackend] = {}

        if backends:
            for backend in backends:
                self._backends[backend.name] = backend

        if not self._backends:
            self._discover_backends()

        if not self._backends:
            raise ValueError(
                "No backends available. Install qiskit or cirq, "
                "or provide backend instances directly."
            )

        self.fallback_chain = FallbackChain(
            backends=list(self._backends.values()),
            config=self.config.fallback,
        )

        logger.info(
            "HybridExecutor initialized with backends: %s",
            list(self._backends.keys()),
        )

    def _discover_backends(self) -> None:
        """Auto-discover available backends based on installed packages."""
        # Try to import simulator (always available if numpy is installed)
        try:
            from quantum_bridge.backends import get_backend

            simulator = get_backend("simulator")
            self._backends["simulator"] = simulator
        except ImportError:
            pass

        # Try Qiskit if installed
        try:
            from quantum_bridge.backends import get_backend

            qiskit_backend = get_backend("qiskit")
            self._backends["qiskit"] = qiskit_backend
        except ImportError:
            pass

        # Try Cirq if installed
        try:
            from quantum_bridge.backends import get_backend

            cirq_backend = get_backend("cirq")
            self._backends["cirq"] = cirq_backend
        except ImportError:
            pass

    @property
    def backends(self) -> list[str]:
        """List of available backend names."""
        return list(self._backends.keys())

    def _to_ir(self, circuit: Any) -> CircuitIR:
        """Convert any supported circuit format to internal IR.

        This handles Qiskit circuits, Cirq circuits, and QASM strings.
        The actual conversion is done by CircuitIR class methods.

        Args:
            circuit: A circuit in any supported format.

        Returns:
            CircuitIR representation of the circuit.

        Raises:
            CircuitError: If the circuit type is not supported.
        """
        from quantum_bridge.exceptions import CircuitError
        from quantum_bridge.ir import CircuitIR

        # Already IR
        if isinstance(circuit, CircuitIR):
            return circuit

        # QASM string
        if isinstance(circuit, str):
            return CircuitIR.from_qasm(circuit)

        # Type sniffing for Qiskit/Cirq (avoids importing at module level)
        type_path = f"{type(circuit).__module__}.{type(circuit).__name__}"

        if "qiskit" in type_path.lower():
            return CircuitIR.from_qiskit(circuit)

        if "cirq" in type_path.lower():
            return CircuitIR.from_cirq(circuit)

        raise CircuitError(
            f"Unsupported circuit type: {type(circuit)}. "
            "Supported types: CircuitIR, Qiskit QuantumCircuit, Cirq Circuit, QASM string."
        )

    def plan(
        self,
        circuit: Any,
        shots: int | None = None,
        mitigate: bool | None = None,
    ) -> ExecutionPlan:
        """Create an execution plan without running the circuit.

        This lets you inspect what will happen before committing to execution.
        Useful for cost estimation and approval workflows.

        **What is a plan?**
        A plan shows you:
        - Which backend will run your circuit
        - What fallback options exist
        - Whether error mitigation will be applied
        - Any warnings about your circuit

        Args:
            circuit: The quantum circuit to plan execution for.
            shots: Number of measurement shots. Defaults to config.default_shots.
            mitigate: Whether to apply error mitigation. Defaults to config setting.

        Returns:
            ExecutionPlan describing the execution strategy.

        Example:
            >>> plan = executor.plan(circuit)
            >>> print(plan)
            Execution Plan:
              Circuit: 2 qubits, 3 gates
              Backend: qiskit
              Fallback: simulator
              Shots: 1024
              Mitigation: disabled
            >>> # User approves...
            >>> result = executor.execute(plan)
        """
        ir = self._to_ir(circuit)
        actual_shots = shots if shots is not None else self.config.default_shots
        actual_mitigate = mitigate if mitigate is not None else self.config.mitigation.enabled

        # Get backend order from fallback chain
        backend_order = self.fallback_chain.get_order()
        selected = backend_order[0] if backend_order else "none"
        fallbacks = backend_order[1:] if len(backend_order) > 1 else []

        # Check for warnings
        warnings = []

        if self.config.max_qubits > 0 and ir.num_qubits > self.config.max_qubits:
            warnings.append(
                f"Circuit has {ir.num_qubits} qubits, exceeds max_qubits={self.config.max_qubits}"
            )

        if actual_mitigate:
            try:
                import mitiq  # noqa: F401
            except ImportError:
                warnings.append("Mitigation requested but mitiq not installed")

        return ExecutionPlan(
            circuit_info={
                "num_qubits": ir.num_qubits,
                "gate_count": len(ir.gates),
                "measurement_count": len(ir.measurements),
            },
            selected_backend=selected,
            fallback_chain=fallbacks,
            estimated_shots=actual_shots,
            mitigation_enabled=actual_mitigate,
            warnings=warnings,
        )

    def execute(
        self,
        circuit: Any | ExecutionPlan,
        shots: int | None = None,
        mitigate: bool | None = None,
        parameters: dict[str, float] | None = None,
    ) -> Result:
        """Execute a quantum circuit and return results.

        This is the main entry point for running circuits. It handles:
        1. Converting your circuit to internal format
        2. Selecting the best available backend
        3. Running with automatic fallback on failure
        4. Optionally applying error mitigation
        5. Returning normalized results

        **What are shots?**
        Quantum computers are probabilistic - you get different results each run.
        "Shots" is how many times we run and measure the circuit. More shots =
        more accurate probability estimates, but takes longer.

        Args:
            circuit: The circuit to execute. Can be:
                - A Qiskit QuantumCircuit
                - A Cirq Circuit
                - An OpenQASM string
                - A CircuitIR object
                - An ExecutionPlan from plan()
            shots: Number of measurement shots (default: config.default_shots).
            mitigate: Apply error mitigation (default: config.mitigation.enabled).
            parameters: Parameter values for parametrized circuits.

        Returns:
            Result object with measurement counts and metadata.

        Raises:
            CircuitError: If the circuit format is not supported.
            FallbackExhaustedError: If all backends fail.
            BackendError: If backend execution fails.

        Example:
            >>> result = executor.execute(bell_circuit, shots=2048)
            >>> print(result.counts)
            {'00': 1024, '11': 1024}
            >>> print(result.backend_name)
            'simulator'
        """
        from quantum_bridge.exceptions import FallbackExhaustedError
        from quantum_bridge.ir import Result

        # Handle ExecutionPlan input
        if isinstance(circuit, ExecutionPlan):
            plan = circuit
            # Re-convert circuit (plan doesn't store it)
            raise NotImplementedError(
                "Executing from plan requires passing the original circuit. "
                "Use execute(circuit, shots=plan.estimated_shots) instead."
            )

        ir = self._to_ir(circuit)
        actual_shots = shots if shots is not None else self.config.default_shots
        actual_mitigate = mitigate if mitigate is not None else self.config.mitigation.enabled

        # Bind parameters if provided
        if parameters:
            ir = ir.bind_parameters(parameters)

        # Check qubit limit
        if self.config.max_qubits > 0 and ir.num_qubits > self.config.max_qubits:
            from quantum_bridge.exceptions import CircuitError

            raise CircuitError(
                f"Circuit has {ir.num_qubits} qubits, "
                f"exceeds configured max_qubits={self.config.max_qubits}"
            )

        # Execute with fallback chain
        start_time = time.time()
        result = self.fallback_chain.execute(ir, actual_shots)
        execution_time = time.time() - start_time

        # Apply error mitigation if requested
        if actual_mitigate:
            result = self._apply_mitigation(ir, result, actual_shots)

        # Add execution metadata
        result = Result(
            counts=result.counts,
            shots=result.shots,
            backend_name=result.backend_name,
            execution_time_ms=execution_time * 1000,
            metadata={
                **result.metadata,
                "mitigation_applied": actual_mitigate,
            },
        )

        logger.info(
            "Executed circuit on %s: %d shots in %.2fms",
            result.backend_name,
            result.shots,
            result.execution_time_ms,
        )

        return result

    def execute_batch(
        self,
        circuits: list[Any],
        shots: int | None = None,
        parameters: list[dict[str, float]] | None = None,
    ) -> BatchResult:
        """Execute multiple circuits, handling partial failures.

        Batch execution is more efficient than individual calls when running
        many circuits. This method handles failures gracefully - if one
        circuit fails, others can still succeed.

        **Why batch?**
        Real quantum backends have overhead per job submission. Batching
        multiple circuits into one job reduces this overhead significantly.

        Args:
            circuits: List of circuits to execute.
            shots: Number of shots per circuit (default: config.default_shots).
            parameters: Optional per-circuit parameter dictionaries.

        Returns:
            BatchResult with results and errors for each circuit.

        Example:
            >>> circuits = [circuit1, circuit2, circuit3]
            >>> batch = executor.execute_batch(circuits, shots=1024)
            >>> print(f"Succeeded: {batch.succeeded}, Failed: {batch.failed}")
            >>> for i, r in enumerate(batch.results):
            ...     if r:
            ...         print(f"Circuit {i}: {r.counts}")
        """
        from quantum_bridge.ir import Result

        actual_shots = shots if shots is not None else self.config.default_shots
        params_list = parameters or [None] * len(circuits)

        if len(params_list) != len(circuits):
            raise ValueError(
                f"parameters length ({len(params_list)}) must match "
                f"circuits length ({len(circuits)})"
            )

        results: list[Result | None] = []
        errors: list[Exception | None] = []
        succeeded = 0
        failed = 0

        for i, (circuit, params) in enumerate(zip(circuits, params_list)):
            try:
                result = self.execute(
                    circuit,
                    shots=actual_shots,
                    parameters=params,
                    mitigate=False,  # Mitigation on batch is expensive
                )
                results.append(result)
                errors.append(None)
                succeeded += 1
            except Exception as e:
                logger.warning("Circuit %d failed: %s", i, e)
                results.append(None)
                errors.append(e)
                failed += 1

        return BatchResult(
            results=results,
            errors=errors,
            succeeded=succeeded,
            failed=failed,
        )

    def _apply_mitigation(
        self,
        circuit: CircuitIR,
        result: Result,
        shots: int,
    ) -> Result:
        """Apply error mitigation to results.

        Uses Mitiq if available, otherwise returns unmodified results.
        """
        from quantum_bridge.mitigation import apply_zne

        try:
            return apply_zne(
                circuit=circuit,
                result=result,
                backend=self.fallback_chain.current_backend,
                shots=shots,
                config=self.config.mitigation,
            )
        except ImportError:
            logger.warning("Mitiq not installed, skipping error mitigation")
            return result
        except Exception as e:
            logger.warning("Error mitigation failed: %s", e)
            return result
