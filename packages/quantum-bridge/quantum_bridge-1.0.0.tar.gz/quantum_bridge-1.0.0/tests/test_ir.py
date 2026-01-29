"""
Tests for Circuit IR and conversion functions.
"""

import math
import pytest

from quantum_bridge.ir import (
    CircuitIR,
    Gate,
    Measurement,
    Result,
    normalize_circuit,
)
from quantum_bridge.exceptions import CircuitConversionError


class TestGate:
    """Tests for Gate dataclass."""

    def test_gate_creation(self):
        """Test basic gate creation."""
        gate = Gate(name="h", qubits=(0,))
        assert gate.name == "h"
        assert gate.qubits == (0,)
        assert gate.params == ()

    def test_gate_with_params(self):
        """Test gate with parameters."""
        gate = Gate(name="rx", qubits=(0,), params=(math.pi / 2,))
        assert gate.name == "rx"
        assert gate.params == (math.pi / 2,)

    def test_gate_name_normalization(self):
        """Test that gate names are normalized to lowercase."""
        gate = Gate(name="RX", qubits=(0,), params=(0.5,))
        assert gate.name == "rx"

    def test_gate_is_frozen(self):
        """Test that Gate is immutable."""
        gate = Gate(name="h", qubits=(0,))
        with pytest.raises(AttributeError):
            gate.name = "x"

    def test_two_qubit_gate(self):
        """Test two-qubit gate."""
        gate = Gate(name="cx", qubits=(0, 1))
        assert gate.qubits == (0, 1)

    def test_three_qubit_gate(self):
        """Test three-qubit gate."""
        gate = Gate(name="ccx", qubits=(0, 1, 2))
        assert gate.qubits == (0, 1, 2)


class TestMeasurement:
    """Tests for Measurement dataclass."""

    def test_measurement_creation(self):
        """Test measurement creation."""
        m = Measurement(qubit=0, classical_bit=0)
        assert m.qubit == 0
        assert m.classical_bit == 0

    def test_measurement_is_frozen(self):
        """Test that Measurement is immutable."""
        m = Measurement(qubit=0, classical_bit=0)
        with pytest.raises(AttributeError):
            m.qubit = 1


class TestCircuitIR:
    """Tests for CircuitIR dataclass."""

    def test_empty_circuit(self):
        """Test empty circuit creation."""
        circuit = CircuitIR(num_qubits=2)
        assert circuit.num_qubits == 2
        assert circuit.gates == []
        assert circuit.measurements == []
        assert circuit.metadata == {}

    def test_circuit_with_gates(self, bell_state_ir):
        """Test circuit with gates."""
        assert bell_state_ir.num_qubits == 2
        assert len(bell_state_ir.gates) == 2
        assert bell_state_ir.gates[0].name == "h"
        assert bell_state_ir.gates[1].name == "cx"

    def test_circuit_depth(self, bell_state_ir):
        """Test depth calculation."""
        # H on q0, then CX on (q0, q1) = depth 2
        assert bell_state_ir.depth == 2

    def test_circuit_depth_parallel(self):
        """Test depth with parallel gates."""
        circuit = CircuitIR(
            num_qubits=4,
            gates=[
                Gate(name="h", qubits=(0,)),
                Gate(name="h", qubits=(1,)),  # Parallel with first
                Gate(name="cx", qubits=(0, 1)),
                Gate(name="cx", qubits=(2, 3)),  # Parallel with previous
            ],
        )
        # h(0), h(1) in layer 1
        # cx(0,1), cx(2,3) in layer 2
        assert circuit.depth == 2

    def test_gate_count(self, bell_state_ir):
        """Test gate count."""
        assert bell_state_ir.gate_count == 2

    def test_gate_counts(self, bell_state_ir):
        """Test gate type counts."""
        counts = bell_state_ir.gate_counts()
        assert counts == {"h": 1, "cx": 1}


class TestCircuitIRFromQasm:
    """Tests for QASM parsing."""

    def test_parse_bell_state(self, bell_state_qasm):
        """Test parsing Bell state QASM."""
        circuit = CircuitIR.from_qasm(bell_state_qasm)
        assert circuit.num_qubits == 2
        assert len(circuit.gates) == 2
        assert circuit.gates[0].name == "h"
        assert circuit.gates[1].name == "cx"
        assert len(circuit.measurements) == 2

    def test_parse_parametrized(self, parametrized_qasm):
        """Test parsing parametrized QASM."""
        circuit = CircuitIR.from_qasm(parametrized_qasm)
        assert circuit.num_qubits == 1
        assert len(circuit.gates) == 2

        # Check rx(pi/2) ≈ 1.5708
        assert circuit.gates[0].name == "rx"
        assert abs(circuit.gates[0].params[0] - math.pi / 2) < 0.001

        # Check rz(pi/4) ≈ 0.7854
        assert circuit.gates[1].name == "rz"
        assert abs(circuit.gates[1].params[0] - math.pi / 4) < 0.001

    def test_parse_no_qubits_error(self):
        """Test error when no qubits defined."""
        qasm = """OPENQASM 2.0;
include "qelib1.inc";
"""
        with pytest.raises(CircuitConversionError) as exc_info:
            CircuitIR.from_qasm(qasm)
        assert "No qubits" in str(exc_info.value)

    def test_parse_multiple_registers(self):
        """Test parsing with multiple qubit registers."""
        qasm = """OPENQASM 2.0;
qreg a[2];
qreg b[1];
creg c[3];
h a[0];
cx a[0],b[0];
"""
        circuit = CircuitIR.from_qasm(qasm)
        assert circuit.num_qubits == 3


class TestCircuitIRFromQiskit:
    """Tests for Qiskit circuit conversion."""

    @pytest.fixture
    def skip_without_qiskit(self):
        pytest.importorskip("qiskit")

    def test_from_qiskit_bell_state(self, skip_without_qiskit):
        """Test converting Qiskit Bell state circuit."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        circuit = CircuitIR.from_qiskit(qc)
        assert circuit.num_qubits == 2
        assert len(circuit.gates) == 2
        assert circuit.gates[0].name == "h"
        assert circuit.gates[1].name == "cx"
        assert len(circuit.measurements) == 2

    def test_from_qiskit_parametrized(self, skip_without_qiskit):
        """Test converting parametrized Qiskit circuit."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(1)
        qc.rx(math.pi / 2, 0)
        qc.rz(0.5, 0)

        circuit = CircuitIR.from_qiskit(qc)
        assert circuit.gates[0].name == "rx"
        assert abs(circuit.gates[0].params[0] - math.pi / 2) < 0.001

    def test_from_qiskit_skips_barriers(self, skip_without_qiskit):
        """Test that barriers are skipped."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(2)
        qc.h(0)
        qc.barrier()
        qc.cx(0, 1)

        circuit = CircuitIR.from_qiskit(qc)
        assert len(circuit.gates) == 2  # No barrier

    def test_to_qiskit_roundtrip(self, skip_without_qiskit, bell_state_ir):
        """Test roundtrip conversion."""
        qc = bell_state_ir.to_qiskit()
        circuit2 = CircuitIR.from_qiskit(qc)

        assert circuit2.num_qubits == bell_state_ir.num_qubits
        assert len(circuit2.gates) == len(bell_state_ir.gates)


class TestCircuitIRFromCirq:
    """Tests for Cirq circuit conversion."""

    @pytest.fixture
    def skip_without_cirq(self):
        pytest.importorskip("cirq")

    def test_from_cirq_bell_state(self, skip_without_cirq):
        """Test converting Cirq Bell state circuit."""
        import cirq

        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit([
            cirq.H(q0),
            cirq.CNOT(q0, q1),
            cirq.measure(q0, q1, key="result"),
        ])

        ir = CircuitIR.from_cirq(circuit)
        assert ir.num_qubits == 2
        assert len(ir.gates) == 2
        assert ir.gates[0].name == "h"

    def test_to_cirq_roundtrip(self, skip_without_cirq, bell_state_ir):
        """Test roundtrip conversion."""
        import cirq

        cirq_circuit = bell_state_ir.to_cirq()
        ir2 = CircuitIR.from_cirq(cirq_circuit)

        assert ir2.num_qubits == bell_state_ir.num_qubits
        # Gate counts should match (measurements handled differently)
        assert len(ir2.gates) == len(bell_state_ir.gates)


class TestNormalizeCircuit:
    """Tests for normalize_circuit function."""

    def test_normalize_ir_passthrough(self, bell_state_ir):
        """Test that CircuitIR passes through unchanged."""
        result = normalize_circuit(bell_state_ir)
        assert result is bell_state_ir

    def test_normalize_qasm_string(self, bell_state_qasm):
        """Test normalizing QASM string."""
        result = normalize_circuit(bell_state_qasm)
        assert isinstance(result, CircuitIR)
        assert result.num_qubits == 2

    def test_normalize_unsupported_type(self):
        """Test error for unsupported type."""
        with pytest.raises(CircuitConversionError) as exc_info:
            normalize_circuit(12345)
        assert "Unsupported circuit type" in str(exc_info.value)


class TestResult:
    """Tests for Result dataclass."""

    def test_result_creation(self, bell_state_result):
        """Test result creation."""
        assert bell_state_result.shots == 1000
        assert bell_state_result.counts == {"00": 500, "11": 500}

    def test_probabilities(self, bell_state_result):
        """Test probability calculation."""
        probs = bell_state_result.probabilities()
        assert probs["00"] == 0.5
        assert probs["11"] == 0.5

    def test_most_common(self, noisy_bell_result):
        """Test most common outcomes."""
        common = noisy_bell_result.most_common(2)
        assert len(common) == 2
        # "00" (480) and "11" (470) should be most common
        assert common[0][0] in ("00", "11")
        assert common[1][0] in ("00", "11")
