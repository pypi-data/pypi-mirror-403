"""Error mitigation for quantum circuits.

This module provides error mitigation techniques to improve the quality
of results from noisy quantum hardware. Currently supports Zero-Noise
Extrapolation (ZNE) via the Mitiq library.

**What is error mitigation?**

Real quantum computers are noisy - gates aren't perfect, and qubits
can lose their state. Error mitigation techniques try to reduce the
impact of this noise on your results without requiring full quantum
error correction.

**Zero-Noise Extrapolation (ZNE):**

ZNE works by:
1. Running your circuit at different noise levels
2. Observing how results change with noise
3. Extrapolating to estimate what the "zero noise" result would be

This requires running your circuit multiple times with artificially
increased noise, then using math to project back to zero noise.

Example:
    >>> from quantum_bridge.mitigation import apply_zne
    >>> mitigated_result = apply_zne(
    ...     circuit=my_circuit,
    ...     result=raw_result,
    ...     backend=my_backend,
    ...     shots=1024,
    ... )
"""

from quantum_bridge.mitigation.zne import apply_zne, is_mitiq_available

__all__ = [
    "apply_zne",
    "is_mitiq_available",
]
