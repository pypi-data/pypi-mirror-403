"""Tests for the fallback chain."""

import pytest
from unittest.mock import MagicMock

from quantum_bridge.config import FallbackConfig
from quantum_bridge.execution.fallback import FallbackChain, FallbackHistory


class MockBackend:
    """Mock backend for testing.

    Note: should_fail controls run() behavior, not health_check().
    A failing backend reports healthy but fails when run() is called.
    This matches real-world behavior where a backend can appear healthy
    but fail during execution.
    """

    def __init__(
        self,
        name: str,
        should_fail: bool = False,
        fail_with: Exception | None = None,
        unhealthy: bool = False,
    ):
        self.name = name
        self.should_fail = should_fail
        self.fail_with = fail_with
        self.unhealthy = unhealthy  # Separate flag for health status
        self.run_count = 0

    def run(self, circuit, shots: int):
        self.run_count += 1
        if self.should_fail:
            if self.fail_with:
                raise self.fail_with
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
        # Only unhealthy flag affects health check, not should_fail
        return not self.unhealthy


class MockCircuitIR:
    """Mock circuit for testing."""

    def __init__(self):
        self.num_qubits = 2
        self.gates = []
        self.measurements = []


@pytest.fixture
def healthy_backend():
    """Create a healthy backend."""
    return MockBackend("healthy")


@pytest.fixture
def failing_backend():
    """Create a failing backend."""
    return MockBackend("failing", should_fail=True)


@pytest.fixture
def mock_circuit():
    """Create a mock circuit."""
    return MockCircuitIR()


class TestFallbackHistory:
    """Tests for FallbackHistory."""

    def test_add_attempt(self):
        """Test adding attempts to history."""
        history = FallbackHistory()
        history.add_attempt("backend1", True, None, 100.0)

        assert history.total_attempts == 1
        assert history.final_backend == "backend1"
        assert len(history.failed_backends) == 0

    def test_track_failures(self):
        """Test tracking failed attempts."""
        history = FallbackHistory()
        error = Exception("test error")

        history.add_attempt("backend1", False, error, 50.0)
        history.add_attempt("backend2", True, None, 100.0)

        assert history.total_attempts == 2
        assert history.final_backend == "backend2"
        assert history.failed_backends == ["backend1"]


class TestFallbackChain:
    """Tests for FallbackChain."""

    def test_init_requires_backends(self):
        """Test that init fails without backends."""
        with pytest.raises(ValueError, match="At least one backend"):
            FallbackChain([])

    def test_init_with_backends(self, healthy_backend):
        """Test normal initialization."""
        chain = FallbackChain([healthy_backend])

        assert chain.get_order() == ["healthy"]
        assert chain.current_backend is None

    def test_get_order(self, healthy_backend, failing_backend):
        """Test getting backend order."""
        chain = FallbackChain([healthy_backend, failing_backend])

        assert chain.get_order() == ["healthy", "failing"]

    def test_reorder_backends(self, healthy_backend, failing_backend):
        """Test reordering backends."""
        chain = FallbackChain([healthy_backend, failing_backend])
        chain.reorder(["failing", "healthy"])

        assert chain.get_order() == ["failing", "healthy"]

    def test_reorder_unknown_backend_raises(self, healthy_backend):
        """Test that reordering with unknown backend raises."""
        chain = FallbackChain([healthy_backend])

        with pytest.raises(ValueError, match="Unknown backend"):
            chain.reorder(["nonexistent"])

    def test_disable_backend(self, healthy_backend, failing_backend):
        """Test disabling a backend."""
        chain = FallbackChain([healthy_backend, failing_backend])
        chain.disable_backend("failing")

        assert "failing" not in chain.get_order()
        assert chain.get_order() == ["healthy"]

    def test_enable_backend(self, healthy_backend, failing_backend):
        """Test enabling a disabled backend."""
        chain = FallbackChain([healthy_backend, failing_backend])
        chain.disable_backend("failing")
        chain.enable_backend("failing", priority=0)

        assert chain.get_order() == ["failing", "healthy"]

    def test_health_check_all_backends(self, healthy_backend):
        """Test health check returns status for all backends."""
        # Create an explicitly unhealthy backend for this test
        unhealthy_backend = MockBackend("unhealthy", unhealthy=True)
        chain = FallbackChain([healthy_backend, unhealthy_backend])
        status = chain.health_check()

        assert status["healthy"] is True
        assert status["unhealthy"] is False

    def test_execute_uses_first_backend(self, healthy_backend, mock_circuit):
        """Test that execute uses first available backend."""
        chain = FallbackChain([healthy_backend])
        result = chain.execute(mock_circuit, shots=1024)

        assert result.backend_name == "healthy"
        assert healthy_backend.run_count == 1

    def test_execute_fallback_on_failure(self, failing_backend, healthy_backend, mock_circuit):
        """Test fallback when first backend fails."""
        chain = FallbackChain([failing_backend, healthy_backend])
        result = chain.execute(mock_circuit, shots=1024)

        assert result.backend_name == "healthy"
        assert failing_backend.run_count == 1
        assert healthy_backend.run_count == 1

    def test_execute_records_history(self, failing_backend, healthy_backend, mock_circuit):
        """Test that execution history is recorded."""
        chain = FallbackChain([failing_backend, healthy_backend])
        chain.execute(mock_circuit, shots=1024)

        assert chain.last_history is not None
        assert chain.last_history.total_attempts == 2
        assert chain.last_history.final_backend == "healthy"
        assert "failing" in chain.last_history.failed_backends

    def test_execute_exhausted_raises(self, failing_backend, mock_circuit):
        """Test that FallbackExhaustedError is raised when all fail."""
        chain = FallbackChain([failing_backend])

        from quantum_bridge.exceptions import FallbackExhaustedError
        with pytest.raises(FallbackExhaustedError):
            chain.execute(mock_circuit, shots=1024)

    def test_execute_respects_max_attempts(self, mock_circuit):
        """Test that max_attempts limit is respected."""
        backends = [
            MockBackend(f"failing{i}", should_fail=True)
            for i in range(5)
        ]

        config = FallbackConfig(max_attempts=2)
        chain = FallbackChain(backends, config=config)

        from quantum_bridge.exceptions import FallbackExhaustedError
        with pytest.raises(FallbackExhaustedError):
            chain.execute(mock_circuit, shots=1024)

        total_runs = sum(b.run_count for b in backends)
        assert total_runs == 2

    def test_execute_sets_current_backend(self, healthy_backend, mock_circuit):
        """Test that current_backend is set after execution."""
        chain = FallbackChain([healthy_backend])

        assert chain.current_backend is None
        chain.execute(mock_circuit, shots=1024)
        assert chain.current_backend is healthy_backend

    def test_handles_timeout_error(self, mock_circuit):
        """Test handling of timeout errors."""
        from quantum_bridge.exceptions import BackendTimeoutError

        timeout_backend = MockBackend(
            "timeout",
            should_fail=True,
            fail_with=BackendTimeoutError("Timed out"),
        )
        healthy_backend = MockBackend("healthy")

        chain = FallbackChain([timeout_backend, healthy_backend])
        result = chain.execute(mock_circuit, shots=1024)

        assert result.backend_name == "healthy"
        assert "timeout" in chain.last_history.failed_backends
