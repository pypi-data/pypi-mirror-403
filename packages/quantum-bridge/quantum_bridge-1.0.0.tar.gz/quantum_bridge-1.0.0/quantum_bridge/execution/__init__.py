"""Execution orchestration for quantum-bridge.

This module provides the HybridExecutor for running quantum circuits
with automatic backend selection and fallback.
"""

from quantum_bridge.execution.engine import (
    BatchResult,
    ExecutionPlan,
    HybridExecutor,
)
from quantum_bridge.execution.fallback import FallbackChain

__all__ = [
    "BatchResult",
    "ExecutionPlan",
    "FallbackChain",
    "HybridExecutor",
]
