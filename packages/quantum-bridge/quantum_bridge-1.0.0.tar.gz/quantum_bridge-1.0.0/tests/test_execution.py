"""Tests for the execution engine."""

import pytest
from unittest.mock import MagicMock, patch

from quantum_bridge.config import ExecutionConfig, FallbackConfig, BackendConfig
from quantum_bridge.execution.engine import HybridExecutor, ExecutionPlan, BatchResult


class MockBackend:
    """Mock backend for testing."""

    def __init__(self, name: str = "mock", should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.run_count = 0

    def run(self, circuit, shots: int):
        self.run_count += 1
        if self.should_fail:
            from quantum_bridge.exceptions import BackendError
            raise BackendError(f"Mock failure on {self.name}")

        from quantum_bridge.ir import Result
        return Result(
            counts={"00": shots // 2, "11": shots // 2},
            shots=shots,
            backend_name=self.name,
            execution_time_ms=10.0,
            metadata={},
        )

    def health_check(self) -> bool:
        return not self.should_fail

    def capabilities(self):
        from quantum_bridge.backends.base import BackendCapabilities
        return BackendCapabilities(
            max_qubits=20,
            native_gates=frozenset({"h", "cx", "rz"}),
            supports_mid_circuit_measurement=False,
            is_simulator=True,
            is_local=True,
        )


class MockCircuitIR:
    """Mock circuit IR for testing."""

    def __init__(self, num_qubits: int = 2):
        self.num_qubits = num_qubits
        self.gates = [MagicMock(name="h"), MagicMock(name="cx")]
        self.measurements = [MagicMock(qubit=0), MagicMock(qubit=1)]
        self.metadata = {}

    def bind_parameters(self, params):
        return self


@pytest.fixture
def mock_backend():
    """Create a mock backend."""
    return MockBackend()


@pytest.fixture
def failing_backend():
    """Create a backend that always fails."""
    return MockBackend(name="failing", should_fail=True)


@pytest.fixture
def mock_circuit():
    """Create a mock circuit."""
    return MockCircuitIR()


class TestExecutionPlan:
    """Tests for ExecutionPlan dataclass."""

    def test_plan_str_format(self):
        """Test plan string representation."""
        plan = ExecutionPlan(
            circuit_info={"num_qubits": 2, "gate_count": 3},
            selected_backend="simulator",
            fallback_chain=["qiskit"],
            estimated_shots=1024,
            mitigation_enabled=False,
            warnings=[],
        )

        plan_str = str(plan)
        assert "2 qubits" in plan_str
        assert "simulator" in plan_str
        assert "1024" in plan_str

    def test_plan_with_warnings(self):
        """Test plan displays warnings."""
        plan = ExecutionPlan(
            circuit_info={"num_qubits": 50, "gate_count": 100},
            selected_backend="simulator",
            fallback_chain=[],
            estimated_shots=1024,
            mitigation_enabled=True,
            warnings=["Circuit exceeds qubit limit"],
        )

        plan_str = str(plan)
        assert "Warnings" in plan_str
        assert "exceeds" in plan_str


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_all_succeeded(self):
        """Test all_succeeded property."""
        from quantum_bridge.ir import Result

        result = Result({"00": 512}, 1024, "mock", 10.0, {})
        batch = BatchResult(
            results=[result, result],
            errors=[None, None],
            succeeded=2,
            failed=0,
        )

        assert batch.all_succeeded
        assert len(batch.successful_results()) == 2

    def test_partial_failure(self):
        """Test batch with partial failures."""
        from quantum_bridge.ir import Result

        result = Result({"00": 512}, 1024, "mock", 10.0, {})
        error = Exception("test error")

        batch = BatchResult(
            results=[result, None, result],
            errors=[None, error, None],
            succeeded=2,
            failed=1,
        )

        assert not batch.all_succeeded
        assert len(batch.successful_results()) == 2
        assert batch.failed == 1


class TestHybridExecutor:
    """Tests for HybridExecutor."""

    def test_init_with_backends(self, mock_backend):
        """Test executor initialization with explicit backends."""
        executor = HybridExecutor(backends=[mock_backend])

        assert "mock" in executor.backends
        assert len(executor.backends) == 1

    def test_init_no_backends_raises(self):
        """Test that init fails with no backends."""
        with patch("quantum_bridge.execution.engine.HybridExecutor._discover_backends"):
            with pytest.raises(ValueError, match="No backends available"):
                HybridExecutor(backends=[])

    def test_plan_creates_plan(self, mock_backend, mock_circuit):
        """Test that plan() returns an ExecutionPlan."""
        executor = HybridExecutor(backends=[mock_backend])

        with patch.object(executor, "_to_ir", return_value=mock_circuit):
            plan = executor.plan(mock_circuit, shots=2048)

        assert isinstance(plan, ExecutionPlan)
        assert plan.selected_backend == "mock"
        assert plan.estimated_shots == 2048

    def test_execute_uses_fallback_chain(self, mock_backend, mock_circuit):
        """Test that execute uses the fallback chain."""
        executor = HybridExecutor(backends=[mock_backend])

        with patch.object(executor, "_to_ir", return_value=mock_circuit):
            result = executor.execute(mock_circuit, shots=1024)

        assert result.backend_name == "mock"
        assert result.shots == 1024
        assert mock_backend.run_count == 1

    def test_execute_batch_returns_batch_result(self, mock_backend, mock_circuit):
        """Test batch execution returns BatchResult."""
        executor = HybridExecutor(backends=[mock_backend])

        circuits = [mock_circuit, mock_circuit]

        with patch.object(executor, "_to_ir", return_value=mock_circuit):
            batch = executor.execute_batch(circuits, shots=512)

        assert isinstance(batch, BatchResult)
        assert batch.succeeded == 2
        assert batch.failed == 0

    def test_execute_respects_max_qubits(self, mock_backend):
        """Test that executor enforces max_qubits config."""
        config = ExecutionConfig(max_qubits=5)
        executor = HybridExecutor(backends=[mock_backend], config=config)

        large_circuit = MockCircuitIR(num_qubits=10)

        with patch.object(executor, "_to_ir", return_value=large_circuit):
            from quantum_bridge.exceptions import CircuitError
            with pytest.raises(CircuitError, match="exceeds"):
                executor.execute(large_circuit)

    def test_config_defaults(self, mock_backend):
        """Test default configuration is sensible."""
        executor = HybridExecutor(backends=[mock_backend])

        assert executor.config.default_shots == 1024
        assert executor.config.fallback.enabled is True


class TestCircuitConversion:
    """Tests for circuit type detection and conversion."""

    def test_detect_qiskit_circuit(self, mock_backend):
        """Test detection of Qiskit circuits."""
        executor = HybridExecutor(backends=[mock_backend])

        # Create a mock that looks like a Qiskit circuit
        mock_qiskit = MagicMock()
        mock_qiskit.__class__.__module__ = "qiskit.circuit"
        mock_qiskit.__class__.__name__ = "QuantumCircuit"

        with patch("quantum_bridge.ir.CircuitIR.from_qiskit") as mock_from:
            mock_from.return_value = MockCircuitIR()
            result = executor._to_ir(mock_qiskit)

        mock_from.assert_called_once()

    def test_detect_qasm_string(self, mock_backend):
        """Test detection of QASM strings."""
        executor = HybridExecutor(backends=[mock_backend])

        qasm = "OPENQASM 2.0;\nqreg q[2];\nh q[0];\ncx q[0], q[1];"

        with patch("quantum_bridge.ir.CircuitIR.from_qasm") as mock_from:
            mock_from.return_value = MockCircuitIR()
            result = executor._to_ir(qasm)

        mock_from.assert_called_once_with(qasm)

    def test_unsupported_type_raises(self, mock_backend):
        """Test that unsupported circuit types raise CircuitError."""
        executor = HybridExecutor(backends=[mock_backend])

        with pytest.raises(Exception):  # CircuitError
            executor._to_ir(12345)  # Not a circuit
