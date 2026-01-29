"""
Built-in classical simulator backend.

Provides a lightweight state-vector simulator that doesn't require
Qiskit or Cirq. Good for testing and small circuits.
"""

import cmath
import math
import random
import time
from typing import Any

from quantum_bridge.backends.base import (
    BackendCapabilities,
    BackendStatus,
    QuantumBackend,
)
from quantum_bridge.exceptions import BackendError, CircuitError
from quantum_bridge.ir import CircuitIR, Gate, Result


# Gates we can simulate
SUPPORTED_GATES = frozenset([
    "id", "x", "y", "z", "h", "s", "t", "sdg", "tdg",
    "rx", "ry", "rz", "p", "u1",
    "cx", "cnot", "cz", "swap",
])


class SimulatorBackend(QuantumBackend):
    """
    Lightweight built-in state-vector simulator.

    This simulator is written in pure Python/NumPy and doesn't require
    Qiskit or Cirq. It's suitable for:
    - Small circuits (< 20 qubits)
    - Testing and development
    - Environments where Qiskit/Cirq aren't available

    Example:
        backend = SimulatorBackend()
        result = backend.run(circuit, shots=1000)
    """

    def __init__(self, seed: int | None = None, max_qubits: int = 20):
        """
        Initialize the simulator.

        Args:
            seed: Random seed for reproducibility
            max_qubits: Maximum qubits to simulate (memory-limited)
        """
        self._seed = seed
        self._max_qubits = max_qubits
        self._rng = random.Random(seed)

    @property
    def name(self) -> str:
        return "simulator:builtin"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            max_qubits=self._max_qubits,
            native_gates=SUPPORTED_GATES,
            supports_mid_circuit_measurement=False,
            is_simulator=True,
            is_local=True,
            max_shots=None,
        )

    def run(self, circuit: CircuitIR, shots: int = 1024) -> Result:
        """Execute circuit on the built-in simulator."""
        self.validate_circuit(circuit)

        n_qubits = circuit.num_qubits

        if n_qubits > self._max_qubits:
            raise CircuitError(
                f"Circuit has {n_qubits} qubits, simulator limited to {self._max_qubits}"
            )

        start_time = time.time()

        try:
            # Initialize state vector |00...0>
            state = self._init_state(n_qubits)

            # Apply gates
            for gate in circuit.gates:
                state = self._apply_gate(state, gate, n_qubits)

            # Sample measurements
            counts = self._sample(state, shots, n_qubits, circuit.measurements)

        except Exception as e:
            raise BackendError(
                f"Simulation failed: {e}",
                backend_name=self.name,
            )

        execution_time = (time.time() - start_time) * 1000

        return Result(
            counts=counts,
            shots=shots,
            backend_name=self.name,
            execution_time_ms=execution_time,
            metadata={
                "num_qubits": n_qubits,
                "gate_count": len(circuit.gates),
            },
        )

    def _init_state(self, n_qubits: int) -> list[complex]:
        """Initialize state vector to |00...0>."""
        size = 2**n_qubits
        state = [complex(0, 0)] * size
        state[0] = complex(1, 0)
        return state

    def _apply_gate(
        self, state: list[complex], gate: Gate, n_qubits: int
    ) -> list[complex]:
        """Apply a gate to the state vector."""
        name = gate.name
        qubits = gate.qubits
        params = gate.params

        if name == "id":
            return state

        elif name == "x":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._x_gate())

        elif name == "y":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._y_gate())

        elif name == "z":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._z_gate())

        elif name == "h":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._h_gate())

        elif name == "s":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._s_gate())

        elif name == "sdg":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._sdg_gate())

        elif name == "t":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._t_gate())

        elif name == "tdg":
            return self._apply_single_qubit(state, qubits[0], n_qubits, self._tdg_gate())

        elif name == "rx":
            return self._apply_single_qubit(
                state, qubits[0], n_qubits, self._rx_gate(params[0])
            )

        elif name == "ry":
            return self._apply_single_qubit(
                state, qubits[0], n_qubits, self._ry_gate(params[0])
            )

        elif name in ("rz", "p", "u1"):
            return self._apply_single_qubit(
                state, qubits[0], n_qubits, self._rz_gate(params[0])
            )

        elif name in ("cx", "cnot"):
            return self._apply_cx(state, qubits[0], qubits[1], n_qubits)

        elif name == "cz":
            return self._apply_cz(state, qubits[0], qubits[1], n_qubits)

        elif name == "swap":
            return self._apply_swap(state, qubits[0], qubits[1], n_qubits)

        else:
            raise BackendError(
                f"Gate '{name}' not supported by built-in simulator",
                backend_name=self.name,
            )

    def _apply_single_qubit(
        self,
        state: list[complex],
        qubit: int,
        n_qubits: int,
        gate_matrix: list[list[complex]],
    ) -> list[complex]:
        """Apply a single-qubit gate."""
        new_state = [complex(0, 0)] * len(state)

        for i in range(len(state)):
            # Get the bit value for this qubit
            bit = (i >> (n_qubits - 1 - qubit)) & 1

            # Flip the bit to get partner index
            partner = i ^ (1 << (n_qubits - 1 - qubit))

            if bit == 0:
                # |0> component
                new_state[i] += gate_matrix[0][0] * state[i]
                new_state[i] += gate_matrix[0][1] * state[partner]
            else:
                # |1> component
                new_state[i] += gate_matrix[1][0] * state[partner]
                new_state[i] += gate_matrix[1][1] * state[i]

        return new_state

    def _apply_cx(
        self, state: list[complex], control: int, target: int, n_qubits: int
    ) -> list[complex]:
        """Apply CNOT gate."""
        new_state = state.copy()

        for i in range(len(state)):
            control_bit = (i >> (n_qubits - 1 - control)) & 1
            if control_bit == 1:
                # Flip target bit
                partner = i ^ (1 << (n_qubits - 1 - target))
                new_state[i], new_state[partner] = state[partner], state[i]

        return new_state

    def _apply_cz(
        self, state: list[complex], q1: int, q2: int, n_qubits: int
    ) -> list[complex]:
        """Apply CZ gate."""
        new_state = state.copy()

        for i in range(len(state)):
            bit1 = (i >> (n_qubits - 1 - q1)) & 1
            bit2 = (i >> (n_qubits - 1 - q2)) & 1
            if bit1 == 1 and bit2 == 1:
                new_state[i] = -state[i]

        return new_state

    def _apply_swap(
        self, state: list[complex], q1: int, q2: int, n_qubits: int
    ) -> list[complex]:
        """Apply SWAP gate."""
        new_state = state.copy()

        for i in range(len(state)):
            bit1 = (i >> (n_qubits - 1 - q1)) & 1
            bit2 = (i >> (n_qubits - 1 - q2)) & 1
            if bit1 != bit2:
                # Swap the bits
                partner = i ^ (1 << (n_qubits - 1 - q1)) ^ (1 << (n_qubits - 1 - q2))
                if i < partner:
                    new_state[i], new_state[partner] = state[partner], state[i]

        return new_state

    def _sample(
        self,
        state: list[complex],
        shots: int,
        n_qubits: int,
        measurements: list[Any],
    ) -> dict[str, int]:
        """Sample measurement outcomes from state vector."""
        # Calculate probabilities
        probs = [abs(amp) ** 2 for amp in state]

        # Normalize (handle numerical errors)
        total = sum(probs)
        if total > 0:
            probs = [p / total for p in probs]

        # Determine which qubits to measure
        if measurements:
            measured_qubits = sorted(set(m.qubit for m in measurements))
        else:
            measured_qubits = list(range(n_qubits))

        # Sample outcomes
        counts: dict[str, int] = {}

        for _ in range(shots):
            # Sample full state
            r = self._rng.random()
            cumulative = 0.0
            outcome = 0
            for i, p in enumerate(probs):
                cumulative += p
                if r < cumulative:
                    outcome = i
                    break

            # Extract measured bits
            bitstring = ""
            for q in measured_qubits:
                bit = (outcome >> (n_qubits - 1 - q)) & 1
                bitstring += str(bit)

            counts[bitstring] = counts.get(bitstring, 0) + 1

        return counts

    # Gate matrices
    def _x_gate(self) -> list[list[complex]]:
        return [[0, 1], [1, 0]]

    def _y_gate(self) -> list[list[complex]]:
        return [[0, -1j], [1j, 0]]

    def _z_gate(self) -> list[list[complex]]:
        return [[1, 0], [0, -1]]

    def _h_gate(self) -> list[list[complex]]:
        s = 1 / math.sqrt(2)
        return [[s, s], [s, -s]]

    def _s_gate(self) -> list[list[complex]]:
        return [[1, 0], [0, 1j]]

    def _sdg_gate(self) -> list[list[complex]]:
        return [[1, 0], [0, -1j]]

    def _t_gate(self) -> list[list[complex]]:
        return [[1, 0], [0, cmath.exp(1j * math.pi / 4)]]

    def _tdg_gate(self) -> list[list[complex]]:
        return [[1, 0], [0, cmath.exp(-1j * math.pi / 4)]]

    def _rx_gate(self, theta: float) -> list[list[complex]]:
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        return [[c, -1j * s], [-1j * s, c]]

    def _ry_gate(self, theta: float) -> list[list[complex]]:
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        return [[c, -s], [s, c]]

    def _rz_gate(self, theta: float) -> list[list[complex]]:
        return [
            [cmath.exp(-1j * theta / 2), 0],
            [0, cmath.exp(1j * theta / 2)],
        ]

    def health_check(self) -> bool:
        """Built-in simulator is always healthy."""
        return True

    def status(self) -> BackendStatus:
        """Get simulator status."""
        return BackendStatus(
            available=True,
            queue_depth=0,
            message=f"Built-in simulator ready (max {self._max_qubits} qubits)",
        )
