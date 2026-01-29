"""Quantum-Bridge: Backend-agnostic quantum circuit execution.

Quantum-Bridge provides a unified interface for running quantum circuits
across multiple backends (IBM Qiskit, Google Cirq, simulators) with
automatic fallback and error mitigation.

**For Python developers learning quantum computing:**

Quantum computing uses qubits instead of classical bits. Unlike regular bits
(which are 0 or 1), qubits can be in "superposition" - both 0 and 1 at once.
When you measure a qubit, it "collapses" to either 0 or 1 randomly
(but with probabilities you can control).

A quantum circuit is a sequence of "gates" (operations) applied to qubits,
followed by measurements. This package helps you run these circuits on
real quantum computers or simulators without worrying about which
backend is available.

Quick Start:
    >>> from quantum_bridge import HybridExecutor
    >>>
    >>> # Create an executor (auto-discovers available backends)
    >>> executor = HybridExecutor()
    >>>
    >>> # Run a circuit (can be Qiskit, Cirq, or QASM string)
    >>> result = executor.execute(my_circuit, shots=1024)
    >>> print(result.counts)  # {'00': 512, '11': 512}

With specific backend:
    >>> from quantum_bridge.backends import get_backend
    >>>
    >>> # Use IBM Quantum
    >>> qiskit_backend = get_backend("qiskit")
    >>> executor = HybridExecutor([qiskit_backend])

With fallback:
    >>> # If Qiskit fails, fall back to simulator
    >>> executor = HybridExecutor([
    ...     get_backend("qiskit"),
    ...     get_backend("simulator"),
    ... ])
    >>> result = executor.execute(circuit)  # Auto-fallback on failure

With error mitigation:
    >>> # Improve result quality using Zero-Noise Extrapolation
    >>> result = executor.execute(circuit, mitigate=True)
"""

__version__ = "1.0.0"
__author__ = "The Quantum Bridge Contributors"

# Lazy imports to avoid loading heavy dependencies at import time
def __getattr__(name: str):
    """Lazy import of main classes."""
    if name == "HybridExecutor":
        from quantum_bridge.execution.engine import HybridExecutor
        return HybridExecutor

    if name == "ExecutionPlan":
        from quantum_bridge.execution.engine import ExecutionPlan
        return ExecutionPlan

    if name == "BatchResult":
        from quantum_bridge.execution.engine import BatchResult
        return BatchResult

    if name == "FallbackChain":
        from quantum_bridge.execution.fallback import FallbackChain
        return FallbackChain

    if name == "ExecutionConfig":
        from quantum_bridge.config import ExecutionConfig
        return ExecutionConfig

    if name == "CircuitIR":
        from quantum_bridge.ir import CircuitIR
        return CircuitIR

    if name == "Result":
        from quantum_bridge.ir import Result
        return Result

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Version
    "__version__",
    # Main classes (lazy-loaded)
    "HybridExecutor",
    "ExecutionPlan",
    "BatchResult",
    "FallbackChain",
    "ExecutionConfig",
    "CircuitIR",
    "Result",
]
