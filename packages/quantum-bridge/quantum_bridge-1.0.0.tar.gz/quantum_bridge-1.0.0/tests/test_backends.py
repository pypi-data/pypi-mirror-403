"""
Tests for quantum backends.
"""

import pytest

from quantum_bridge.backends import (
    get_backend,
    get_backend_class,
    list_backends,
    list_available_backends,
    is_backend_available,
    get_best_backend,
)
from quantum_bridge.backends.base import (
    BackendCapabilities,
    BackendStatus,
    QuantumBackend,
)
from quantum_bridge.backends.simulator import SimulatorBackend
from quantum_bridge.exceptions import (
    BackendUnavailableError,
    BackendError,
    CircuitError,
)
from quantum_bridge.ir import CircuitIR, Gate, Measurement

from tests.conftest import assert_valid_counts, assert_bell_state_distribution


class TestBackendRegistry:
    """Tests for backend registry functions."""

    def test_list_backends(self):
        """Test listing registered backends."""
        backends = list_backends()
        assert "simulator" in backends
        assert "builtin" in backends
        assert "qiskit" in backends
        assert "cirq" in backends

    def test_get_backend_class_simulator(self):
        """Test getting simulator backend class."""
        cls = get_backend_class("simulator")
        assert cls is SimulatorBackend

    def test_get_backend_class_unknown(self):
        """Test error for unknown backend."""
        with pytest.raises(BackendUnavailableError) as exc_info:
            get_backend_class("nonexistent")
        assert "Unknown backend" in str(exc_info.value)

    def test_get_backend_instance(self):
        """Test getting backend instance."""
        backend = get_backend("simulator", seed=42)
        assert isinstance(backend, SimulatorBackend)

    def test_list_available_backends(self):
        """Test listing available backends."""
        available = list_available_backends()
        # Simulator should always be available
        assert "simulator" in available

    def test_is_backend_available(self):
        """Test checking backend availability."""
        assert is_backend_available("simulator")
        assert not is_backend_available("nonexistent")

    def test_get_best_backend(self):
        """Test getting best available backend."""
        backend = get_best_backend()
        assert isinstance(backend, QuantumBackend)


class TestBackendCapabilities:
    """Tests for BackendCapabilities."""

    def test_supports_gate(self):
        """Test gate support checking."""
        caps = BackendCapabilities(
            max_qubits=10,
            native_gates=frozenset(["h", "cx", "rz"]),
        )
        assert caps.supports_gate("h")
        assert caps.supports_gate("CX")  # Case insensitive
        assert not caps.supports_gate("swap")

    def test_can_run_circuit_success(self, bell_state_ir):
        """Test circuit compatibility check - success."""
        caps = BackendCapabilities(
            max_qubits=10,
            native_gates=frozenset(["h", "cx", "rz"]),
        )
        can_run, reason = caps.can_run_circuit(bell_state_ir)
        assert can_run
        assert reason is None

    def test_can_run_circuit_too_many_qubits(self, bell_state_ir):
        """Test circuit compatibility - too many qubits."""
        caps = BackendCapabilities(
            max_qubits=1,
            native_gates=frozenset(["h", "cx"]),
        )
        can_run, reason = caps.can_run_circuit(bell_state_ir)
        assert not can_run
        assert "qubits" in reason.lower()

    def test_can_run_circuit_unsupported_gate(self, bell_state_ir):
        """Test circuit compatibility - unsupported gate."""
        caps = BackendCapabilities(
            max_qubits=10,
            native_gates=frozenset(["x", "y"]),  # No h or cx
        )
        can_run, reason = caps.can_run_circuit(bell_state_ir)
        assert not can_run
        assert "Unsupported gates" in reason


class TestSimulatorBackend:
    """Tests for built-in simulator backend."""

    def test_simulator_creation(self):
        """Test simulator creation."""
        sim = SimulatorBackend(seed=42)
        assert sim.name == "simulator:builtin"
        assert sim.health_check()

    def test_simulator_capabilities(self):
        """Test simulator capabilities."""
        sim = SimulatorBackend()
        caps = sim.capabilities
        assert caps.max_qubits == 20
        assert caps.is_simulator
        assert caps.is_local
        assert "h" in caps.native_gates

    def test_run_bell_state(self, simulator_backend, bell_state_ir):
        """Test running Bell state circuit."""
        result = simulator_backend.run(bell_state_ir, shots=1000)

        assert result.shots == 1000
        assert result.backend_name == "simulator:builtin"
        assert_valid_counts(result.counts, num_qubits=2, shots=1000)
        assert_bell_state_distribution(result.counts, tolerance=0.1)

    def test_run_ghz_state(self, simulator_backend, ghz_state_ir):
        """Test running GHZ state circuit."""
        result = simulator_backend.run(ghz_state_ir, shots=1000)

        assert result.shots == 1000
        # GHZ should give |000> and |111>
        probs = result.probabilities()
        assert probs.get("000", 0) > 0.4
        assert probs.get("111", 0) > 0.4

    def test_run_parametrized_circuit(self, simulator_backend, parametrized_circuit_ir):
        """Test running parametrized circuit."""
        result = simulator_backend.run(parametrized_circuit_ir, shots=1000)
        assert result.shots == 1000
        assert_valid_counts(result.counts, num_qubits=1, shots=1000)

    def test_run_empty_circuit(self, simulator_backend, empty_circuit_ir):
        """Test running empty circuit."""
        # Empty circuit should always give |00>
        result = simulator_backend.run(empty_circuit_ir, shots=100)
        assert "00" in result.counts
        assert result.counts["00"] == 100

    def test_reproducibility(self, bell_state_ir):
        """Test that seeded simulator is reproducible."""
        sim1 = SimulatorBackend(seed=42)
        sim2 = SimulatorBackend(seed=42)

        result1 = sim1.run(bell_state_ir, shots=100)
        result2 = sim2.run(bell_state_ir, shots=100)

        assert result1.counts == result2.counts

    def test_too_many_qubits_error(self):
        """Test error when circuit has too many qubits."""
        sim = SimulatorBackend(max_qubits=5)
        big_circuit = CircuitIR(num_qubits=10, gates=[Gate(name="h", qubits=(0,))])

        with pytest.raises(CircuitError):
            sim.run(big_circuit)

    def test_status(self, simulator_backend):
        """Test status reporting."""
        status = simulator_backend.status()
        assert isinstance(status, BackendStatus)
        assert status.available
        assert status.queue_depth == 0


class TestSimulatorGates:
    """Test individual gate implementations."""

    @pytest.fixture
    def sim(self):
        return SimulatorBackend(seed=42)

    def test_x_gate(self, sim):
        """Test X (NOT) gate: |0> -> |1>."""
        circuit = CircuitIR(
            num_qubits=1,
            gates=[Gate(name="x", qubits=(0,))],
            measurements=[Measurement(qubit=0, classical_bit=0)],
        )
        result = sim.run(circuit, shots=100)
        assert result.counts.get("1", 0) == 100

    def test_h_gate_superposition(self, sim):
        """Test H gate creates superposition."""
        circuit = CircuitIR(
            num_qubits=1,
            gates=[Gate(name="h", qubits=(0,))],
            measurements=[Measurement(qubit=0, classical_bit=0)],
        )
        result = sim.run(circuit, shots=1000)
        probs = result.probabilities()
        # Should be roughly 50/50
        assert 0.4 < probs.get("0", 0) < 0.6
        assert 0.4 < probs.get("1", 0) < 0.6

    def test_z_gate(self, sim):
        """Test Z gate (phase flip, no amplitude change on |0>)."""
        circuit = CircuitIR(
            num_qubits=1,
            gates=[Gate(name="z", qubits=(0,))],
            measurements=[Measurement(qubit=0, classical_bit=0)],
        )
        result = sim.run(circuit, shots=100)
        # Z on |0> = |0>
        assert result.counts.get("0", 0) == 100

    def test_swap_gate(self, sim):
        """Test SWAP gate."""
        # Prepare |10>, swap to |01>
        circuit = CircuitIR(
            num_qubits=2,
            gates=[
                Gate(name="x", qubits=(0,)),  # |10>
                Gate(name="swap", qubits=(0, 1)),  # -> |01>
            ],
            measurements=[
                Measurement(qubit=0, classical_bit=0),
                Measurement(qubit=1, classical_bit=1),
            ],
        )
        result = sim.run(circuit, shots=100)
        assert result.counts.get("01", 0) == 100

    def test_cz_gate(self, sim):
        """Test CZ gate."""
        # CZ flips phase on |11> only
        # Start with |11>, apply CZ, verify state unchanged in computational basis
        circuit = CircuitIR(
            num_qubits=2,
            gates=[
                Gate(name="x", qubits=(0,)),  # |10>
                Gate(name="x", qubits=(1,)),  # |11>
                Gate(name="cz", qubits=(0, 1)),  # Phase flip (invisible in Z basis)
            ],
            measurements=[
                Measurement(qubit=0, classical_bit=0),
                Measurement(qubit=1, classical_bit=1),
            ],
        )
        result = sim.run(circuit, shots=100)
        # CZ on |11> only adds a phase, state remains |11> in Z basis
        assert result.counts.get("11", 0) == 100


class TestQiskitBackend:
    """Tests for Qiskit backend."""

    @pytest.fixture
    def skip_without_qiskit(self):
        pytest.importorskip("qiskit")
        pytest.importorskip("qiskit_aer")

    def test_qiskit_backend_creation(self, skip_without_qiskit):
        """Test creating Qiskit backend."""
        from quantum_bridge.backends.qiskit_backend import QiskitBackend

        backend = QiskitBackend()
        assert "qiskit" in backend.name

    def test_qiskit_run_bell_state(self, skip_without_qiskit, bell_state_ir):
        """Test running Bell state on Qiskit Aer."""
        from quantum_bridge.backends.qiskit_backend import QiskitBackend

        backend = QiskitBackend(backend_name="aer_simulator")
        result = backend.run(bell_state_ir, shots=1000)

        assert result.shots == 1000
        assert_bell_state_distribution(result.counts, tolerance=0.1)

    def test_qiskit_health_check(self, skip_without_qiskit):
        """Test Qiskit backend health check."""
        from quantum_bridge.backends.qiskit_backend import QiskitBackend

        backend = QiskitBackend()
        assert backend.health_check()


class TestCirqBackend:
    """Tests for Cirq backend."""

    @pytest.fixture
    def skip_without_cirq(self):
        pytest.importorskip("cirq")

    def test_cirq_backend_creation(self, skip_without_cirq):
        """Test creating Cirq backend."""
        from quantum_bridge.backends.cirq_backend import CirqBackend

        backend = CirqBackend()
        assert "cirq" in backend.name

    def test_cirq_run_bell_state(self, skip_without_cirq, bell_state_ir):
        """Test running Bell state on Cirq simulator."""
        from quantum_bridge.backends.cirq_backend import CirqBackend

        backend = CirqBackend()
        result = backend.run(bell_state_ir, shots=1000)

        assert result.shots == 1000
        # Cirq may return different bitstring ordering
        total_00_11 = result.counts.get("00", 0) + result.counts.get("11", 0)
        assert total_00_11 > 900  # Should be mostly 00 and 11

    def test_cirq_health_check(self, skip_without_cirq):
        """Test Cirq backend health check."""
        from quantum_bridge.backends.cirq_backend import CirqBackend

        backend = CirqBackend()
        assert backend.health_check()
