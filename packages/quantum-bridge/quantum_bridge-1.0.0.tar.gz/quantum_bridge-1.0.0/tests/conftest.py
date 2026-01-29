"""
Pytest fixtures for Quantum Bridge tests.

Provides mock circuits, backends, and test utilities.
"""

import pytest
from unittest.mock import MagicMock

from quantum_bridge.ir import CircuitIR, Gate, Measurement, Result
from quantum_bridge.backends.base import BackendCapabilities, QuantumBackend
from quantum_bridge.backends.simulator import SimulatorBackend


# ============================================================================
# Circuit Fixtures
# ============================================================================


@pytest.fixture
def bell_state_ir() -> CircuitIR:
    """A simple Bell state circuit (H on q0, CX q0->q1)."""
    return CircuitIR(
        num_qubits=2,
        gates=[
            Gate(name="h", qubits=(0,)),
            Gate(name="cx", qubits=(0, 1)),
        ],
        measurements=[
            Measurement(qubit=0, classical_bit=0),
            Measurement(qubit=1, classical_bit=1),
        ],
        metadata={"name": "bell_state"},
    )


@pytest.fixture
def ghz_state_ir() -> CircuitIR:
    """3-qubit GHZ state circuit."""
    return CircuitIR(
        num_qubits=3,
        gates=[
            Gate(name="h", qubits=(0,)),
            Gate(name="cx", qubits=(0, 1)),
            Gate(name="cx", qubits=(1, 2)),
        ],
        measurements=[
            Measurement(qubit=0, classical_bit=0),
            Measurement(qubit=1, classical_bit=1),
            Measurement(qubit=2, classical_bit=2),
        ],
        metadata={"name": "ghz_state"},
    )


@pytest.fixture
def parametrized_circuit_ir() -> CircuitIR:
    """Circuit with parametrized gates."""
    import math

    return CircuitIR(
        num_qubits=1,
        gates=[
            Gate(name="rx", qubits=(0,), params=(math.pi / 2,)),
            Gate(name="rz", qubits=(0,), params=(math.pi / 4,)),
        ],
        measurements=[
            Measurement(qubit=0, classical_bit=0),
        ],
    )


@pytest.fixture
def empty_circuit_ir() -> CircuitIR:
    """Empty circuit with no gates."""
    return CircuitIR(
        num_qubits=2,
        gates=[],
        measurements=[],
    )


@pytest.fixture
def single_qubit_circuit_ir() -> CircuitIR:
    """Single qubit circuit with various gates."""
    return CircuitIR(
        num_qubits=1,
        gates=[
            Gate(name="h", qubits=(0,)),
            Gate(name="t", qubits=(0,)),
            Gate(name="s", qubits=(0,)),
            Gate(name="x", qubits=(0,)),
        ],
        measurements=[
            Measurement(qubit=0, classical_bit=0),
        ],
    )


# ============================================================================
# QASM Fixtures
# ============================================================================


@pytest.fixture
def bell_state_qasm() -> str:
    """Bell state in OpenQASM 2.0 format."""
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""


@pytest.fixture
def parametrized_qasm() -> str:
    """Parametrized circuit in QASM."""
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
creg c[1];
rx(pi/2) q[0];
rz(pi/4) q[0];
measure q[0] -> c[0];
"""


# ============================================================================
# Backend Fixtures
# ============================================================================


@pytest.fixture
def simulator_backend() -> SimulatorBackend:
    """Built-in simulator backend with fixed seed."""
    return SimulatorBackend(seed=42)


@pytest.fixture
def mock_backend() -> QuantumBackend:
    """Mock backend for testing."""
    backend = MagicMock(spec=QuantumBackend)
    backend.name = "mock:test"
    backend.capabilities = BackendCapabilities(
        max_qubits=10,
        native_gates=frozenset(["h", "cx", "rz", "x", "y", "z"]),
        is_simulator=True,
        is_local=True,
    )
    backend.health_check.return_value = True

    def mock_run(circuit, shots=1024):
        # Return fake Bell state result
        return Result(
            counts={"00": shots // 2, "11": shots // 2},
            shots=shots,
            backend_name="mock:test",
            execution_time_ms=10.0,
        )

    backend.run.side_effect = mock_run
    return backend


@pytest.fixture
def failing_backend() -> QuantumBackend:
    """Backend that always fails."""
    from quantum_bridge.exceptions import BackendError

    backend = MagicMock(spec=QuantumBackend)
    backend.name = "mock:failing"
    backend.capabilities = BackendCapabilities(
        max_qubits=10,
        native_gates=frozenset(["h", "cx"]),
        is_simulator=True,
        is_local=True,
    )
    backend.health_check.return_value = False
    backend.run.side_effect = BackendError("Backend failure", backend_name="mock:failing")
    return backend


# ============================================================================
# Result Fixtures
# ============================================================================


@pytest.fixture
def bell_state_result() -> Result:
    """Expected result from Bell state circuit."""
    return Result(
        counts={"00": 500, "11": 500},
        shots=1000,
        backend_name="test",
        execution_time_ms=50.0,
    )


@pytest.fixture
def noisy_bell_result() -> Result:
    """Bell state result with noise."""
    return Result(
        counts={"00": 480, "11": 470, "01": 25, "10": 25},
        shots=1000,
        backend_name="noisy_test",
        execution_time_ms=100.0,
    )


# ============================================================================
# Skip Markers
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_qiskit: mark test as requiring qiskit"
    )
    config.addinivalue_line(
        "markers", "requires_cirq: mark test as requiring cirq"
    )


@pytest.fixture
def skip_without_qiskit():
    """Skip test if qiskit is not installed."""
    pytest.importorskip("qiskit")


@pytest.fixture
def skip_without_cirq():
    """Skip test if cirq is not installed."""
    pytest.importorskip("cirq")


# ============================================================================
# Utility Functions
# ============================================================================


def assert_valid_counts(counts: dict[str, int], num_qubits: int, shots: int):
    """Assert that counts are valid."""
    total = sum(counts.values())
    assert total == shots, f"Total counts {total} != shots {shots}"

    for bitstring in counts:
        assert len(bitstring) == num_qubits, f"Bitstring '{bitstring}' wrong length"
        assert all(c in "01" for c in bitstring), f"Invalid bitstring: {bitstring}"


def assert_bell_state_distribution(counts: dict[str, int], tolerance: float = 0.1):
    """Assert counts follow Bell state distribution (|00> + |11>)."""
    total = sum(counts.values())
    prob_00 = counts.get("00", 0) / total
    prob_11 = counts.get("11", 0) / total
    prob_01 = counts.get("01", 0) / total
    prob_10 = counts.get("10", 0) / total

    # Should have roughly equal |00> and |11>
    assert abs(prob_00 - 0.5) < tolerance, f"P(00) = {prob_00}, expected ~0.5"
    assert abs(prob_11 - 0.5) < tolerance, f"P(11) = {prob_11}, expected ~0.5"

    # Should have minimal |01> and |10>
    assert prob_01 < tolerance, f"P(01) = {prob_01}, expected ~0"
    assert prob_10 < tolerance, f"P(10) = {prob_10}, expected ~0"
