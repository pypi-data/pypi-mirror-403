"""
Circuit Intermediate Representation (IR) for Quantum Bridge.

Provides a backend-agnostic representation of quantum circuits that can be
converted to/from Qiskit, Cirq, and OpenQASM formats.
"""

from dataclasses import dataclass, field
from typing import Any

from quantum_bridge.exceptions import CircuitConversionError


@dataclass(frozen=True)
class Gate:
    """
    A quantum gate operation.

    Attributes:
        name: Gate name (lowercase). Standard names: h, x, y, z, cx, cz, rx, ry, rz,
              swap, ccx, u, u1, u2, u3, s, t, sdg, tdg, id
        qubits: Tuple of qubit indices this gate acts on
        params: Tuple of numeric parameters (angles in radians)
    """

    name: str
    qubits: tuple[int, ...]
    params: tuple[float, ...] = ()

    def __post_init__(self):
        # Normalize gate name to lowercase
        if self.name != self.name.lower():
            object.__setattr__(self, "name", self.name.lower())


@dataclass(frozen=True)
class Measurement:
    """
    A measurement operation.

    Attributes:
        qubit: Index of qubit to measure
        classical_bit: Index of classical bit to store result
    """

    qubit: int
    classical_bit: int


@dataclass
class CircuitIR:
    """
    Backend-agnostic circuit representation.

    This is the internal format used by Quantum Bridge. Circuits from Qiskit,
    Cirq, or QASM are converted to this format before execution.

    Attributes:
        num_qubits: Number of qubits in the circuit
        gates: List of gate operations in order
        measurements: List of measurement operations
        metadata: Optional metadata (circuit name, source, etc.)
    """

    num_qubits: int
    gates: list[Gate] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_qiskit(cls, circuit: Any) -> "CircuitIR":
        """
        Convert a Qiskit QuantumCircuit to CircuitIR.

        Args:
            circuit: A qiskit.circuit.QuantumCircuit object

        Returns:
            CircuitIR representation

        Raises:
            CircuitConversionError: If conversion fails
        """
        try:
            # Import here to avoid dependency at module load
            from qiskit.circuit import QuantumCircuit

            if not isinstance(circuit, QuantumCircuit):
                raise CircuitConversionError(
                    f"Expected QuantumCircuit, got {type(circuit).__name__}",
                    source_type="qiskit",
                )
        except ImportError:
            raise CircuitConversionError(
                "Qiskit is not installed. Install with: pip install quantum-bridge[qiskit]",
                source_type="qiskit",
            )

        gates: list[Gate] = []
        measurements: list[Measurement] = []

        # Build qubit index mapping
        qubit_indices = {qubit: i for i, qubit in enumerate(circuit.qubits)}
        clbit_indices = {clbit: i for i, clbit in enumerate(circuit.clbits)}

        for instruction in circuit.data:
            op = instruction.operation
            op_name = op.name.lower()
            qubits = tuple(qubit_indices[q] for q in instruction.qubits)

            # Skip barriers (visual only)
            if op_name == "barrier":
                continue

            # Handle measurements
            if op_name == "measure":
                if instruction.clbits:
                    clbit = clbit_indices[instruction.clbits[0]]
                    measurements.append(Measurement(qubit=qubits[0], classical_bit=clbit))
                continue

            # Skip reset (not supported in v1.0)
            if op_name == "reset":
                raise CircuitConversionError(
                    "Reset operations are not supported in v1.0",
                    source_type="qiskit",
                )

            # Skip conditionals (not supported in v1.0)
            if hasattr(op, "condition") and op.condition is not None:
                raise CircuitConversionError(
                    "Classical conditionals are not supported in v1.0",
                    source_type="qiskit",
                )

            # Extract parameters (must be numeric)
            params: list[float] = []
            for param in op.params:
                try:
                    # Try to get numeric value
                    if hasattr(param, "evalf"):
                        # Sympy expression
                        params.append(float(param.evalf()))
                    elif hasattr(param, "_symbol_expr"):
                        # Qiskit Parameter - not bound
                        raise CircuitConversionError(
                            f"Unbound parameter '{param}' found. Bind parameters before conversion.",
                            source_type="qiskit",
                        )
                    else:
                        params.append(float(param))
                except (TypeError, ValueError) as e:
                    raise CircuitConversionError(
                        f"Could not convert parameter '{param}' to float: {e}",
                        source_type="qiskit",
                    )

            gates.append(Gate(name=op_name, qubits=qubits, params=tuple(params)))

        return cls(
            num_qubits=circuit.num_qubits,
            gates=gates,
            measurements=measurements,
            metadata={"name": circuit.name, "source": "qiskit"},
        )

    @classmethod
    def from_cirq(cls, circuit: Any) -> "CircuitIR":
        """
        Convert a Cirq Circuit to CircuitIR.

        Args:
            circuit: A cirq.Circuit object

        Returns:
            CircuitIR representation

        Raises:
            CircuitConversionError: If conversion fails
        """
        try:
            import cirq
        except ImportError:
            raise CircuitConversionError(
                "Cirq is not installed. Install with: pip install quantum-bridge[cirq]",
                source_type="cirq",
            )

        if not isinstance(circuit, cirq.Circuit):
            raise CircuitConversionError(
                f"Expected cirq.Circuit, got {type(circuit).__name__}",
                source_type="cirq",
            )

        gates: list[Gate] = []
        measurements: list[Measurement] = []

        # Get all qubits and create index mapping
        all_qubits = sorted(circuit.all_qubits(), key=lambda q: str(q))
        qubit_indices = {qubit: i for i, qubit in enumerate(all_qubits)}

        measurement_counter = 0

        for moment in circuit:
            for op in moment:
                qubits = tuple(qubit_indices[q] for q in op.qubits)
                gate = op.gate

                if gate is None:
                    continue

                gate_name = type(gate).__name__.lower()

                # Handle measurements
                if isinstance(gate, cirq.MeasurementGate):
                    for qubit in qubits:
                        measurements.append(
                            Measurement(qubit=qubit, classical_bit=measurement_counter)
                        )
                        measurement_counter += 1
                    continue

                # Map Cirq gate names to standard names
                name_mapping = {
                    "hpowgate": "h",
                    "xpowgate": "x",
                    "ypowgate": "y",
                    "zpowgate": "z",
                    "cnotpowgate": "cx",
                    "czpowgate": "cz",
                    "swappowgate": "swap",
                    "ccxpowgate": "ccx",
                    "iswappowgate": "iswap",
                    "rxpowgate": "rx",
                    "rypowgate": "ry",
                    "rzpowgate": "rz",
                }

                # Check for special Cirq gates
                if gate_name in name_mapping:
                    gate_name = name_mapping[gate_name]
                elif hasattr(gate, "_name"):
                    gate_name = gate._name.lower()

                # Extract parameters
                params: list[float] = []

                # Handle parameterized gates
                if hasattr(gate, "exponent"):
                    exp = gate.exponent
                    if hasattr(exp, "_symbol_expr") or isinstance(exp, str):
                        raise CircuitConversionError(
                            f"Unbound parameter in gate. Resolve parameters before conversion.",
                            source_type="cirq",
                        )
                    # For pow gates, convert exponent to radians if needed
                    if gate_name in ("rx", "ry", "rz"):
                        # Cirq uses exponent * pi for rotation
                        params.append(float(exp) * 3.141592653589793)
                    elif float(exp) != 1.0:
                        params.append(float(exp))

                if hasattr(gate, "theta"):
                    params.append(float(gate.theta))
                if hasattr(gate, "phi"):
                    params.append(float(gate.phi))

                gates.append(Gate(name=gate_name, qubits=qubits, params=tuple(params)))

        return cls(
            num_qubits=len(all_qubits),
            gates=gates,
            measurements=measurements,
            metadata={"source": "cirq"},
        )

    @classmethod
    def from_qasm(cls, qasm: str) -> "CircuitIR":
        """
        Parse OpenQASM 2.0 string to CircuitIR.

        Note: This is a simplified parser that handles common cases.
        For full QASM 3.0 support, use Qiskit's parser via from_qiskit().

        Args:
            qasm: OpenQASM 2.0 string

        Returns:
            CircuitIR representation

        Raises:
            CircuitConversionError: If parsing fails
        """
        import re

        gates: list[Gate] = []
        measurements: list[Measurement] = []
        num_qubits = 0
        num_clbits = 0
        qubit_map: dict[str, int] = {}
        clbit_map: dict[str, int] = {}

        lines = qasm.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                continue

            # Skip OPENQASM version and includes
            if line.startswith("OPENQASM") or line.startswith("include"):
                continue

            # Parse qubit register: qreg q[5];
            qreg_match = re.match(r"qreg\s+(\w+)\[(\d+)\];", line)
            if qreg_match:
                name, size = qreg_match.groups()
                size = int(size)
                for i in range(size):
                    qubit_map[f"{name}[{i}]"] = num_qubits + i
                num_qubits += size
                continue

            # Parse classical register: creg c[5];
            creg_match = re.match(r"creg\s+(\w+)\[(\d+)\];", line)
            if creg_match:
                name, size = creg_match.groups()
                size = int(size)
                for i in range(size):
                    clbit_map[f"{name}[{i}]"] = num_clbits + i
                num_clbits += size
                continue

            # Skip barriers
            if line.startswith("barrier"):
                continue

            # Parse measurement: measure q[0] -> c[0];
            meas_match = re.match(r"measure\s+(\w+\[\d+\])\s*->\s*(\w+\[\d+\]);", line)
            if meas_match:
                qubit_str, clbit_str = meas_match.groups()
                if qubit_str in qubit_map and clbit_str in clbit_map:
                    measurements.append(
                        Measurement(
                            qubit=qubit_map[qubit_str],
                            classical_bit=clbit_map[clbit_str],
                        )
                    )
                continue

            # Parse gate: h q[0]; or cx q[0],q[1]; or rz(0.5) q[0];
            gate_match = re.match(
                r"(\w+)(?:\(([\d\.,\-\+\*\/\s\w]+)\))?\s+([\w\[\],\s]+);", line
            )
            if gate_match:
                gate_name, params_str, qubits_str = gate_match.groups()

                # Parse parameters
                params: list[float] = []
                if params_str:
                    for p in params_str.split(","):
                        p = p.strip()
                        # Handle pi
                        p = p.replace("pi", "3.141592653589793")
                        try:
                            params.append(float(eval(p)))
                        except Exception:
                            raise CircuitConversionError(
                                f"Could not parse parameter: {p}",
                                source_type="qasm",
                            )

                # Parse qubit arguments
                qubit_strs = [q.strip() for q in qubits_str.split(",")]
                qubits: list[int] = []
                for qs in qubit_strs:
                    if qs in qubit_map:
                        qubits.append(qubit_map[qs])
                    else:
                        raise CircuitConversionError(
                            f"Unknown qubit: {qs}",
                            source_type="qasm",
                        )

                gates.append(
                    Gate(name=gate_name.lower(), qubits=tuple(qubits), params=tuple(params))
                )
                continue

        if num_qubits == 0:
            raise CircuitConversionError(
                "No qubits defined in QASM",
                source_type="qasm",
            )

        return cls(
            num_qubits=num_qubits,
            gates=gates,
            measurements=measurements,
            metadata={"source": "qasm"},
        )

    def to_qiskit(self) -> Any:
        """
        Convert CircuitIR to a Qiskit QuantumCircuit.

        Returns:
            qiskit.circuit.QuantumCircuit

        Raises:
            CircuitConversionError: If conversion fails
        """
        try:
            from qiskit.circuit import QuantumCircuit
        except ImportError:
            raise CircuitConversionError(
                "Qiskit is not installed. Install with: pip install quantum-bridge[qiskit]",
                source_type="qiskit",
            )

        # Determine number of classical bits needed
        num_clbits = max((m.classical_bit for m in self.measurements), default=-1) + 1

        qc = QuantumCircuit(self.num_qubits, num_clbits)

        if "name" in self.metadata:
            qc.name = self.metadata["name"]

        # Add gates
        for gate in self.gates:
            try:
                if gate.name == "h":
                    qc.h(gate.qubits[0])
                elif gate.name == "x":
                    qc.x(gate.qubits[0])
                elif gate.name == "y":
                    qc.y(gate.qubits[0])
                elif gate.name == "z":
                    qc.z(gate.qubits[0])
                elif gate.name == "s":
                    qc.s(gate.qubits[0])
                elif gate.name == "t":
                    qc.t(gate.qubits[0])
                elif gate.name == "sdg":
                    qc.sdg(gate.qubits[0])
                elif gate.name == "tdg":
                    qc.tdg(gate.qubits[0])
                elif gate.name == "rx":
                    qc.rx(gate.params[0], gate.qubits[0])
                elif gate.name == "ry":
                    qc.ry(gate.params[0], gate.qubits[0])
                elif gate.name == "rz":
                    qc.rz(gate.params[0], gate.qubits[0])
                elif gate.name in ("cx", "cnot"):
                    qc.cx(gate.qubits[0], gate.qubits[1])
                elif gate.name == "cz":
                    qc.cz(gate.qubits[0], gate.qubits[1])
                elif gate.name == "swap":
                    qc.swap(gate.qubits[0], gate.qubits[1])
                elif gate.name in ("ccx", "toffoli"):
                    qc.ccx(gate.qubits[0], gate.qubits[1], gate.qubits[2])
                elif gate.name == "u":
                    qc.u(gate.params[0], gate.params[1], gate.params[2], gate.qubits[0])
                elif gate.name == "u1":
                    qc.p(gate.params[0], gate.qubits[0])  # u1 -> p in newer qiskit
                elif gate.name == "u2":
                    qc.u(3.141592653589793 / 2, gate.params[0], gate.params[1], gate.qubits[0])
                elif gate.name == "u3":
                    qc.u(gate.params[0], gate.params[1], gate.params[2], gate.qubits[0])
                elif gate.name == "id":
                    qc.id(gate.qubits[0])
                else:
                    raise CircuitConversionError(
                        f"Unknown gate: {gate.name}",
                        source_type="ir",
                    )
            except IndexError:
                raise CircuitConversionError(
                    f"Gate {gate.name} has insufficient qubits or parameters",
                    source_type="ir",
                )

        # Add measurements
        for m in self.measurements:
            qc.measure(m.qubit, m.classical_bit)

        return qc

    def to_cirq(self) -> Any:
        """
        Convert CircuitIR to a Cirq Circuit.

        Returns:
            cirq.Circuit

        Raises:
            CircuitConversionError: If conversion fails
        """
        try:
            import cirq
        except ImportError:
            raise CircuitConversionError(
                "Cirq is not installed. Install with: pip install quantum-bridge[cirq]",
                source_type="cirq",
            )

        qubits = cirq.LineQubit.range(self.num_qubits)
        ops: list[Any] = []

        for gate in self.gates:
            try:
                q = [qubits[i] for i in gate.qubits]

                if gate.name == "h":
                    ops.append(cirq.H(q[0]))
                elif gate.name == "x":
                    ops.append(cirq.X(q[0]))
                elif gate.name == "y":
                    ops.append(cirq.Y(q[0]))
                elif gate.name == "z":
                    ops.append(cirq.Z(q[0]))
                elif gate.name == "s":
                    ops.append(cirq.S(q[0]))
                elif gate.name == "t":
                    ops.append(cirq.T(q[0]))
                elif gate.name == "rx":
                    ops.append(cirq.rx(gate.params[0])(q[0]))
                elif gate.name == "ry":
                    ops.append(cirq.ry(gate.params[0])(q[0]))
                elif gate.name == "rz":
                    ops.append(cirq.rz(gate.params[0])(q[0]))
                elif gate.name in ("cx", "cnot"):
                    ops.append(cirq.CNOT(q[0], q[1]))
                elif gate.name == "cz":
                    ops.append(cirq.CZ(q[0], q[1]))
                elif gate.name == "swap":
                    ops.append(cirq.SWAP(q[0], q[1]))
                elif gate.name in ("ccx", "toffoli"):
                    ops.append(cirq.CCX(q[0], q[1], q[2]))
                elif gate.name == "id":
                    ops.append(cirq.I(q[0]))
                else:
                    raise CircuitConversionError(
                        f"Gate {gate.name} not supported for Cirq conversion",
                        source_type="ir",
                    )
            except IndexError:
                raise CircuitConversionError(
                    f"Gate {gate.name} has insufficient qubits",
                    source_type="ir",
                )

        # Add measurements
        measured_qubits = [qubits[m.qubit] for m in self.measurements]
        if measured_qubits:
            ops.append(cirq.measure(*measured_qubits, key="result"))

        return cirq.Circuit(ops)

    @property
    def depth(self) -> int:
        """
        Estimate circuit depth (number of gate layers).

        This is an approximation assuming optimal parallelization.
        """
        if not self.gates:
            return 0

        # Track when each qubit is free
        qubit_depth = [0] * self.num_qubits

        for gate in self.gates:
            # Gate starts after all its qubits are free
            start = max(qubit_depth[q] for q in gate.qubits)
            end = start + 1
            for q in gate.qubits:
                qubit_depth[q] = end

        return max(qubit_depth)

    @property
    def gate_count(self) -> int:
        """Total number of gates."""
        return len(self.gates)

    def gate_counts(self) -> dict[str, int]:
        """Count of each gate type."""
        counts: dict[str, int] = {}
        for gate in self.gates:
            counts[gate.name] = counts.get(gate.name, 0) + 1
        return counts


@dataclass
class Result:
    """
    Result of a quantum circuit execution.

    Attributes:
        counts: Dictionary mapping bitstrings to counts
        shots: Total number of shots executed
        backend_name: Name of the backend that executed the circuit
        execution_time_ms: Execution time in milliseconds
        metadata: Additional backend-specific metadata
    """

    counts: dict[str, int]
    shots: int
    backend_name: str
    execution_time_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def probabilities(self) -> dict[str, float]:
        """Get probabilities for each outcome."""
        return {k: v / self.shots for k, v in self.counts.items()}

    def most_common(self, n: int = 1) -> list[tuple[str, int]]:
        """Get the n most common outcomes."""
        sorted_counts = sorted(self.counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:n]


def normalize_circuit(circuit: Any) -> CircuitIR:
    """
    Convert any supported circuit type to CircuitIR.

    Supports:
    - CircuitIR (passthrough)
    - str (OpenQASM)
    - qiskit.circuit.QuantumCircuit
    - cirq.Circuit

    Args:
        circuit: Circuit in any supported format

    Returns:
        CircuitIR representation

    Raises:
        CircuitConversionError: If circuit type is not supported
    """
    if isinstance(circuit, CircuitIR):
        return circuit

    if isinstance(circuit, str):
        return CircuitIR.from_qasm(circuit)

    # Type sniffing for qiskit/cirq without importing
    type_module = type(circuit).__module__
    type_name = type(circuit).__name__

    if "qiskit" in type_module.lower():
        return CircuitIR.from_qiskit(circuit)

    if "cirq" in type_module.lower():
        return CircuitIR.from_cirq(circuit)

    raise CircuitConversionError(
        f"Unsupported circuit type: {type_name} from module {type_module}. "
        "Supported types: CircuitIR, str (QASM), qiskit.QuantumCircuit, cirq.Circuit",
        source_type=type_name,
    )
