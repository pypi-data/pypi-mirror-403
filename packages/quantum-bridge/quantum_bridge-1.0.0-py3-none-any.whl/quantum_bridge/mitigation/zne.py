"""Zero-Noise Extrapolation (ZNE) via Mitiq.

This module wraps Mitiq's ZNE implementation to provide error mitigation
for quantum circuits executed through quantum-bridge.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from quantum_bridge.config import MitigationConfig

if TYPE_CHECKING:
    from quantum_bridge.backends.base import QuantumBackend
    from quantum_bridge.ir import CircuitIR, Result

logger = logging.getLogger(__name__)

# Lazy import check for Mitiq
_MITIQ_AVAILABLE: bool | None = None


def is_mitiq_available() -> bool:
    """Check if Mitiq is installed and importable.

    Returns:
        True if mitiq can be imported, False otherwise.

    Example:
        >>> if is_mitiq_available():
        ...     result = apply_zne(circuit, result, backend, shots)
        ... else:
        ...     print("Install mitiq for error mitigation: pip install quantum-bridge[mitiq]")
    """
    global _MITIQ_AVAILABLE
    if _MITIQ_AVAILABLE is None:
        try:
            import mitiq  # noqa: F401

            _MITIQ_AVAILABLE = True
        except ImportError:
            _MITIQ_AVAILABLE = False
    return _MITIQ_AVAILABLE


def apply_zne(
    circuit: CircuitIR,
    result: Result,
    backend: QuantumBackend,
    shots: int,
    config: MitigationConfig | None = None,
) -> Result:
    """Apply Zero-Noise Extrapolation to improve result quality.

    ZNE works by running the circuit at multiple noise levels and
    extrapolating to estimate the zero-noise result. This requires
    additional circuit executions.

    **How it works:**

    1. We convert your circuit to a format Mitiq understands
    2. Mitiq creates "folded" versions with artificially increased noise
    3. We run each folded circuit on the backend
    4. Mitiq extrapolates the results to estimate zero-noise values

    **Requirements:**
    - Mitiq must be installed: `pip install quantum-bridge[mitiq]`
    - The backend must support running circuits

    Args:
        circuit: The original circuit in IR format.
        result: The original (unmitigated) result.
        backend: Backend to use for additional executions.
        shots: Number of shots per execution.
        config: Mitigation configuration (scale factors, extrapolation method).

    Returns:
        Result with mitigated counts.

    Raises:
        ImportError: If Mitiq is not installed.
        ValueError: If configuration is invalid.

    Example:
        >>> from quantum_bridge.mitigation import apply_zne
        >>> config = MitigationConfig(
        ...     enabled=True,
        ...     zne_scale_factors=(1.0, 2.0, 3.0),
        ...     zne_extrapolation="linear",
        ... )
        >>> mitigated = apply_zne(circuit, result, backend, 1024, config)
        >>> print(f"Original: {result.counts}")
        >>> print(f"Mitigated: {mitigated.counts}")
    """
    if not is_mitiq_available():
        raise ImportError(
            "Mitiq is required for error mitigation. "
            "Install with: pip install quantum-bridge[mitiq]"
        )

    from mitiq import zne
    from mitiq.zne.inference import (
        ExpFactory,
        LinearFactory,
        PolyFactory,
    )

    from quantum_bridge.ir import Result

    config = config or MitigationConfig(enabled=True)

    # Select extrapolation factory based on config
    scale_factors = list(config.zne_scale_factors)

    if config.zne_extrapolation == "linear":
        factory = LinearFactory(scale_factors)
    elif config.zne_extrapolation == "polynomial":
        factory = PolyFactory(scale_factors, order=len(scale_factors) - 1)
    elif config.zne_extrapolation == "exponential":
        factory = ExpFactory(scale_factors)
    else:
        raise ValueError(f"Unknown extrapolation method: {config.zne_extrapolation}")

    # Create executor function for Mitiq
    def executor(mitiq_circuit) -> float:
        """Execute circuit and return expectation value."""
        # Convert Mitiq circuit back to our IR
        ir = _from_mitiq_circuit(mitiq_circuit, circuit)

        # Run on backend
        run_result = backend.run(ir, shots)

        # Calculate expectation value (counts-weighted average)
        return _counts_to_expectation(run_result.counts)

    # Convert our circuit to Mitiq format
    mitiq_circuit = _to_mitiq_circuit(circuit)

    # Run ZNE
    logger.info(
        "Applying ZNE with scale factors %s and %s extrapolation",
        scale_factors,
        config.zne_extrapolation,
    )

    try:
        mitigated_expectation = zne.execute_with_zne(
            circuit=mitiq_circuit,
            executor=executor,
            factory=factory,
        )
    except Exception as e:
        logger.warning("ZNE failed, returning original result: %s", e)
        return result

    # Convert expectation back to counts (approximate)
    mitigated_counts = _expectation_to_counts(
        expectation=mitigated_expectation,
        original_counts=result.counts,
        shots=result.shots,
    )

    return Result(
        counts=mitigated_counts,
        shots=result.shots,
        backend_name=result.backend_name,
        execution_time_ms=result.execution_time_ms,
        metadata={
            **result.metadata,
            "zne_applied": True,
            "zne_scale_factors": scale_factors,
            "zne_extrapolation": config.zne_extrapolation,
            "zne_mitigated_expectation": mitigated_expectation,
        },
    )


def _to_mitiq_circuit(circuit: CircuitIR):
    """Convert CircuitIR to a Mitiq-compatible circuit.

    Mitiq works with Cirq circuits internally, so we convert to Cirq.
    """
    try:
        import cirq
    except ImportError:
        # Fall back to Qiskit if Cirq not available
        try:
            from qiskit import QuantumCircuit

            return _ir_to_qiskit(circuit)
        except ImportError:
            raise ImportError(
                "Mitiq requires either cirq or qiskit to be installed. "
                "Install with: pip install quantum-bridge[cirq] or "
                "pip install quantum-bridge[qiskit]"
            )

    # Convert to Cirq circuit
    qubits = [cirq.LineQubit(i) for i in range(circuit.num_qubits)]
    ops = []

    for gate in circuit.gates:
        cirq_gate = _get_cirq_gate(gate.name, gate.params)
        target_qubits = [qubits[i] for i in gate.qubits]
        ops.append(cirq_gate(*target_qubits))

    return cirq.Circuit(ops)


def _from_mitiq_circuit(mitiq_circuit, original_ir: CircuitIR) -> CircuitIR:
    """Convert a Mitiq circuit back to CircuitIR.

    This handles the folded circuits that Mitiq creates for ZNE.
    """
    from quantum_bridge.ir import CircuitIR, Gate, Measurement

    # Try to detect circuit type
    circuit_type = type(mitiq_circuit).__module__

    if "cirq" in circuit_type:
        return _cirq_to_ir(mitiq_circuit)
    elif "qiskit" in circuit_type:
        return CircuitIR.from_qiskit(mitiq_circuit)
    else:
        # Fallback: return original (may not work for folded circuits)
        logger.warning("Unknown Mitiq circuit type, using original IR")
        return original_ir


def _cirq_to_ir(cirq_circuit) -> CircuitIR:
    """Convert Cirq circuit to CircuitIR."""
    import cirq

    from quantum_bridge.ir import CircuitIR, Gate, Measurement

    # Find number of qubits
    qubits = sorted(cirq_circuit.all_qubits(), key=lambda q: q.x if hasattr(q, "x") else 0)
    qubit_map = {q: i for i, q in enumerate(qubits)}
    num_qubits = len(qubits)

    gates = []
    measurements = []

    for moment in cirq_circuit:
        for op in moment:
            gate_qubits = tuple(qubit_map[q] for q in op.qubits)

            if isinstance(op.gate, cirq.MeasurementGate):
                for i, q in enumerate(gate_qubits):
                    measurements.append(Measurement(qubit=q, classical_bit=q))
            else:
                gate_name, params = _cirq_gate_to_name(op.gate)
                gates.append(Gate(name=gate_name, qubits=gate_qubits, params=params))

    return CircuitIR(
        num_qubits=num_qubits,
        gates=gates,
        measurements=measurements if measurements else [Measurement(i, i) for i in range(num_qubits)],
    )


def _ir_to_qiskit(circuit: CircuitIR):
    """Convert CircuitIR to Qiskit QuantumCircuit."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(circuit.num_qubits, len(circuit.measurements) or circuit.num_qubits)

    for gate in circuit.gates:
        _apply_qiskit_gate(qc, gate.name, gate.qubits, gate.params)

    for m in circuit.measurements:
        qc.measure(m.qubit, m.classical_bit)

    return qc


def _get_cirq_gate(name: str, params: tuple[float, ...]):
    """Get Cirq gate from name and parameters."""
    import cirq

    name_lower = name.lower()

    # Single-qubit gates
    if name_lower == "h":
        return cirq.H
    elif name_lower == "x":
        return cirq.X
    elif name_lower == "y":
        return cirq.Y
    elif name_lower == "z":
        return cirq.Z
    elif name_lower == "s":
        return cirq.S
    elif name_lower == "t":
        return cirq.T
    elif name_lower == "rx" and params:
        return cirq.rx(params[0])
    elif name_lower == "ry" and params:
        return cirq.ry(params[0])
    elif name_lower == "rz" and params:
        return cirq.rz(params[0])
    # Two-qubit gates
    elif name_lower in ("cx", "cnot"):
        return cirq.CNOT
    elif name_lower == "cz":
        return cirq.CZ
    elif name_lower == "swap":
        return cirq.SWAP
    else:
        raise ValueError(f"Unknown gate: {name}")


def _cirq_gate_to_name(gate) -> tuple[str, tuple[float, ...]]:
    """Convert Cirq gate to name and parameters."""
    import cirq

    gate_type = type(gate)

    if gate_type == cirq.HPowGate and gate.exponent == 1:
        return "h", ()
    elif gate_type == cirq.XPowGate and gate.exponent == 1:
        return "x", ()
    elif gate_type == cirq.YPowGate and gate.exponent == 1:
        return "y", ()
    elif gate_type == cirq.ZPowGate and gate.exponent == 1:
        return "z", ()
    elif gate_type == cirq.CNotPowGate and gate.exponent == 1:
        return "cx", ()
    elif gate_type == cirq.CZPowGate and gate.exponent == 1:
        return "cz", ()
    elif hasattr(gate, "exponent"):
        # Generic rotation
        import math

        angle = gate.exponent * math.pi
        base_name = type(gate).__name__.replace("PowGate", "").lower()
        return f"r{base_name}", (angle,)
    else:
        return str(gate).lower(), ()


def _apply_qiskit_gate(qc, name: str, qubits: tuple[int, ...], params: tuple[float, ...]) -> None:
    """Apply a gate to a Qiskit circuit."""
    name_lower = name.lower()

    if name_lower == "h":
        qc.h(qubits[0])
    elif name_lower == "x":
        qc.x(qubits[0])
    elif name_lower == "y":
        qc.y(qubits[0])
    elif name_lower == "z":
        qc.z(qubits[0])
    elif name_lower == "s":
        qc.s(qubits[0])
    elif name_lower == "t":
        qc.t(qubits[0])
    elif name_lower == "rx":
        qc.rx(params[0], qubits[0])
    elif name_lower == "ry":
        qc.ry(params[0], qubits[0])
    elif name_lower == "rz":
        qc.rz(params[0], qubits[0])
    elif name_lower in ("cx", "cnot"):
        qc.cx(qubits[0], qubits[1])
    elif name_lower == "cz":
        qc.cz(qubits[0], qubits[1])
    elif name_lower == "swap":
        qc.swap(qubits[0], qubits[1])
    else:
        raise ValueError(f"Unknown gate: {name}")


def _counts_to_expectation(counts: dict[str, int]) -> float:
    """Convert measurement counts to an expectation value.

    Uses parity (Z expectation) on all qubits.
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0

    expectation = 0.0
    for bitstring, count in counts.items():
        # Parity: +1 if even number of 1s, -1 if odd
        parity = 1 if bitstring.count("1") % 2 == 0 else -1
        expectation += parity * count

    return expectation / total


def _expectation_to_counts(
    expectation: float,
    original_counts: dict[str, int],
    shots: int,
) -> dict[str, int]:
    """Convert expectation value back to approximate counts.

    This is an approximation - we adjust the original counts
    to match the mitigated expectation value while preserving
    the relative structure of the distribution.
    """
    if not original_counts:
        return {}

    # Calculate original expectation
    original_exp = _counts_to_expectation(original_counts)

    if abs(original_exp) < 1e-10:
        # Can't scale from zero, return original
        return dict(original_counts)

    # Calculate scaling factor
    scale = expectation / original_exp if abs(original_exp) > 1e-10 else 1.0

    # Clamp scale to reasonable range
    scale = max(-2.0, min(2.0, scale))

    # Adjust counts (this is approximate)
    total = sum(original_counts.values())
    new_counts = {}

    for bitstring, count in original_counts.items():
        parity = 1 if bitstring.count("1") % 2 == 0 else -1

        # Adjust based on parity and scale
        if parity == 1:
            # Even parity states get boosted when expectation increases
            adjusted = count * (1 + (scale - 1) * 0.5)
        else:
            # Odd parity states get reduced when expectation increases
            adjusted = count * (1 - (scale - 1) * 0.5)

        new_counts[bitstring] = max(0, int(round(adjusted)))

    # Normalize to original shot count
    new_total = sum(new_counts.values())
    if new_total > 0:
        factor = total / new_total
        new_counts = {k: max(0, int(round(v * factor))) for k, v in new_counts.items()}

    return new_counts
