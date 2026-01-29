"""Tests for error mitigation."""

import pytest
from unittest.mock import MagicMock, patch

from quantum_bridge.config import MitigationConfig
from quantum_bridge.mitigation.zne import (
    is_mitiq_available,
    apply_zne,
    _counts_to_expectation,
    _expectation_to_counts,
)


class MockCircuitIR:
    """Mock circuit for testing."""

    def __init__(self):
        self.num_qubits = 2
        self.gates = [
            MagicMock(name="h", qubits=(0,), params=()),
            MagicMock(name="cx", qubits=(0, 1), params=()),
        ]
        self.measurements = [
            MagicMock(qubit=0, classical_bit=0),
            MagicMock(qubit=1, classical_bit=1),
        ]


class MockResult:
    """Mock result for testing."""

    def __init__(self, counts=None):
        self.counts = counts or {"00": 512, "11": 512}
        self.shots = sum(self.counts.values())
        self.backend_name = "mock"
        self.execution_time_ms = 10.0
        self.metadata = {}


class MockBackend:
    """Mock backend for testing."""

    def __init__(self):
        self.name = "mock"
        self.run_count = 0

    def run(self, circuit, shots):
        self.run_count += 1
        from quantum_bridge.ir import Result
        return Result(
            counts={"00": shots // 2, "11": shots // 2},
            shots=shots,
            backend_name=self.name,
            execution_time_ms=10.0,
            metadata={},
        )

    def health_check(self):
        return True


class TestMitiqAvailability:
    """Tests for Mitiq availability check."""

    def test_is_mitiq_available_returns_bool(self):
        """Test availability check returns boolean."""
        result = is_mitiq_available()
        assert isinstance(result, bool)


class TestCountsConversion:
    """Tests for counts <-> expectation conversion."""

    def test_counts_to_expectation_balanced(self):
        """Test expectation from balanced counts."""
        counts = {"00": 500, "11": 500}
        exp = _counts_to_expectation(counts)
        assert abs(exp - 1.0) < 0.01

    def test_counts_to_expectation_all_zeros(self):
        """Test expectation when all results are 00."""
        counts = {"00": 1000}
        exp = _counts_to_expectation(counts)
        assert abs(exp - 1.0) < 0.01

    def test_counts_to_expectation_mixed_parity(self):
        """Test expectation with mixed parity."""
        counts = {"01": 500, "10": 500}
        exp = _counts_to_expectation(counts)
        assert abs(exp - (-1.0)) < 0.01

    def test_counts_to_expectation_empty(self):
        """Test expectation from empty counts."""
        exp = _counts_to_expectation({})
        assert exp == 0.0

    def test_expectation_to_counts_preserves_structure(self):
        """Test that counts conversion preserves structure."""
        original = {"00": 400, "11": 600}
        exp = 0.8

        result = _expectation_to_counts(exp, original, 1000)

        assert set(result.keys()) == set(original.keys())
        assert abs(sum(result.values()) - 1000) < 100

    def test_expectation_to_counts_empty_returns_empty(self):
        """Test that empty original counts returns empty."""
        result = _expectation_to_counts(0.5, {}, 1000)
        assert result == {}


class TestApplyZNE:
    """Tests for apply_zne function."""

    def test_apply_zne_requires_mitiq(self):
        """Test that apply_zne raises if mitiq not installed."""
        with patch("quantum_bridge.mitigation.zne.is_mitiq_available", return_value=False):
            circuit = MockCircuitIR()
            result = MockResult()
            backend = MockBackend()

            with pytest.raises(ImportError, match="Mitiq is required"):
                apply_zne(circuit, result, backend, 1024)


class TestMitigationConfig:
    """Tests for MitigationConfig validation."""

    def test_mitigation_config_defaults(self):
        """Test MitigationConfig default values."""
        config = MitigationConfig()

        assert config.enabled is False
        assert config.technique == "zne"
        assert config.zne_scale_factors == (1.0, 2.0, 3.0)
        assert config.zne_extrapolation == "linear"

    def test_mitigation_config_invalid_technique(self):
        """Test invalid technique raises."""
        with pytest.raises(ValueError, match="technique"):
            MitigationConfig(technique="invalid")

    def test_mitigation_config_invalid_extrapolation(self):
        """Test invalid extrapolation raises."""
        with pytest.raises(ValueError, match="extrapolation"):
            MitigationConfig(zne_extrapolation="invalid")

    def test_mitigation_config_too_few_scale_factors(self):
        """Test too few scale factors raises."""
        with pytest.raises(ValueError, match="scale_factors"):
            MitigationConfig(zne_scale_factors=(1.0,))


class TestZNEWithMitiq:
    """Tests that require Mitiq to be installed."""

    @pytest.fixture(autouse=True)
    def skip_without_mitiq(self):
        """Skip tests if Mitiq is not installed."""
        if not is_mitiq_available():
            pytest.skip("Mitiq not installed")

    def test_apply_zne_returns_result(self):
        """Test that apply_zne returns a Result object."""
        circuit = MockCircuitIR()
        result = MockResult()
        backend = MockBackend()

        config = MitigationConfig(enabled=True)

        with patch("quantum_bridge.mitigation.zne._to_mitiq_circuit"):
            with patch("mitiq.zne.execute_with_zne", return_value=0.9):
                mitigated = apply_zne(circuit, result, backend, 1024, config)

        assert mitigated.metadata.get("zne_applied") is True
