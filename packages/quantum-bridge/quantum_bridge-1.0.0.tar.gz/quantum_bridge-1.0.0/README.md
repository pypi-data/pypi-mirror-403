# Quantum-Bridge

Backend-agnostic bridge for quantum-classical hybrid workflows with automatic fallback and error mitigation.

## For Python Developers Learning Quantum Computing

Quantum computing uses **qubits** instead of classical bits. Unlike regular bits (which are 0 or 1), qubits can be in "superposition" - effectively both 0 and 1 at once. When measured, they collapse to a definite value.

A **quantum circuit** is a sequence of operations (gates) applied to qubits:
- **H gate**: Puts a qubit in superposition
- **CX gate**: Entangles two qubits
- **Measurement**: Reads the qubit state (collapses superposition)

Quantum-Bridge lets you run these circuits without worrying about which quantum computer or simulator is available.

## Installation

```bash
# Core package (simulator only)
pip install quantum-bridge

# With IBM Quantum support
pip install quantum-bridge[qiskit]

# With Google Cirq support
pip install quantum-bridge[cirq]

# With error mitigation
pip install quantum-bridge[mitiq]

# Everything
pip install quantum-bridge[all]
```

## Quick Start

### Python API

```python
from quantum_bridge import HybridExecutor

# Create executor (auto-discovers available backends)
executor = HybridExecutor()

# Run a circuit (Qiskit, Cirq, or QASM string)
result = executor.execute(my_circuit, shots=1024)
print(result.counts)  # {'00': 512, '11': 512}
print(result.backend_name)  # 'simulator'
```

### Command Line

```bash
# List available backends
qbridge backends list

# Run a QASM file
qbridge run bell.qasm --shots 2048

# See execution plan before running
qbridge plan my_circuit.qasm

# Run with error mitigation
qbridge run circuit.qasm --mitigate
```

## Features

### Automatic Backend Fallback

If your primary backend fails, Quantum-Bridge automatically tries the next one:

```python
from quantum_bridge import HybridExecutor
from quantum_bridge.backends import get_backend

executor = HybridExecutor([
    get_backend("qiskit"),      # Try IBM Quantum first
    get_backend("simulator"),   # Fall back to simulator
])

# If Qiskit times out or errors, simulator is used automatically
result = executor.execute(circuit)
```

### Multiple Circuit Formats

Accept circuits from any major framework:

```python
# Qiskit circuit
from qiskit import QuantumCircuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
result = executor.execute(qc)

# Cirq circuit
import cirq
q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit([cirq.H(q0), cirq.CNOT(q0, q1)])
result = executor.execute(circuit)

# OpenQASM string
qasm = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
"""
result = executor.execute(qasm)
```

### Error Mitigation

Improve result quality using Zero-Noise Extrapolation (requires `mitiq`):

```python
# Enable mitigation
result = executor.execute(circuit, mitigate=True)

print(result.metadata["zne_applied"])  # True
```

### Execution Plans

Preview what will happen before running:

```python
plan = executor.plan(circuit, shots=2048)
print(plan)
# Execution Plan:
#   Circuit: 2 qubits, 3 gates
#   Backend: qiskit
#   Fallback: simulator
#   Shots: 2048
#   Mitigation: disabled

# Approve and execute
result = executor.execute(circuit, shots=plan.estimated_shots)
```

### Batch Execution

Run multiple circuits efficiently:

```python
circuits = [circuit1, circuit2, circuit3]
batch = executor.execute_batch(circuits, shots=1024)

print(f"Succeeded: {batch.succeeded}, Failed: {batch.failed}")

for result in batch.successful_results():
    print(result.counts)
```

## Configuration

```python
from quantum_bridge import ExecutionConfig, HybridExecutor
from quantum_bridge.config import BackendConfig, FallbackConfig

config = ExecutionConfig(
    default_shots=2048,
    backends=[
        BackendConfig(name="qiskit", priority=0),
        BackendConfig(name="simulator", priority=1),
    ],
    fallback=FallbackConfig(
        enabled=True,
        max_attempts=3,
        timeout_seconds=300,
    ),
)

executor = HybridExecutor(config=config)
```

## Requirements

- Python 3.10+
- numpy

Optional:
- qiskit, qiskit-aer, qiskit-ibm-runtime (for IBM Quantum)
- cirq (for Google Cirq)
- mitiq (for error mitigation)

## License

MIT License - see LICENSE file.

## Support

If you find this project useful, consider supporting development:

- [Ko-fi](https://ko-fi.com/theblank)
- [Buy Me a Coffee](https://buymeacoffee.com/blank_tech)
