"""
Quantum backend registry and lazy loading.

Backends are loaded lazily to avoid import errors when optional
dependencies (qiskit, cirq) are not installed.

Example:
    from quantum_bridge.backends import get_backend, list_backends

    # Get a specific backend
    backend = get_backend("simulator")  # Always available
    backend = get_backend("qiskit")     # Requires qiskit

    # List available backends
    for name in list_backends():
        print(name)
"""

from typing import TYPE_CHECKING, Callable

from quantum_bridge.backends.base import (
    BackendCapabilities,
    BackendStatus,
    QuantumBackend,
)
from quantum_bridge.exceptions import BackendUnavailableError

if TYPE_CHECKING:
    from quantum_bridge.backends.cirq_backend import CirqBackend
    from quantum_bridge.backends.qiskit_backend import QiskitBackend
    from quantum_bridge.backends.simulator import SimulatorBackend


__all__ = [
    "QuantumBackend",
    "BackendCapabilities",
    "BackendStatus",
    "get_backend",
    "get_backend_class",
    "list_backends",
    "list_available_backends",
    "register_backend",
]


# Backend registry: name -> (loader_function, requires_package)
_BACKEND_REGISTRY: dict[str, tuple[Callable[[], type[QuantumBackend]], str | None]] = {}


def _register_builtin_backends():
    """Register the built-in backends."""

    def load_simulator():
        from quantum_bridge.backends.simulator import SimulatorBackend
        return SimulatorBackend

    def load_qiskit():
        from quantum_bridge.backends.qiskit_backend import QiskitBackend
        return QiskitBackend

    def load_cirq():
        from quantum_bridge.backends.cirq_backend import CirqBackend
        return CirqBackend

    _BACKEND_REGISTRY["simulator"] = (load_simulator, None)
    _BACKEND_REGISTRY["builtin"] = (load_simulator, None)  # Alias
    _BACKEND_REGISTRY["qiskit"] = (load_qiskit, "qiskit")
    _BACKEND_REGISTRY["cirq"] = (load_cirq, "cirq")


# Initialize on module load
_register_builtin_backends()


def register_backend(
    name: str,
    loader: Callable[[], type[QuantumBackend]],
    requires_package: str | None = None,
):
    """
    Register a custom backend.

    Args:
        name: Backend name for get_backend()
        loader: Function that returns the backend class
        requires_package: Optional package name required for this backend

    Example:
        def load_my_backend():
            from my_package import MyBackend
            return MyBackend

        register_backend("my_backend", load_my_backend, "my_package")
    """
    _BACKEND_REGISTRY[name] = (loader, requires_package)


def get_backend_class(name: str) -> type[QuantumBackend]:
    """
    Get a backend class by name.

    Args:
        name: Backend name ("simulator", "qiskit", "cirq", etc.)

    Returns:
        Backend class (not instance)

    Raises:
        BackendUnavailableError: If backend not found or dependency missing
    """
    if name not in _BACKEND_REGISTRY:
        available = ", ".join(_BACKEND_REGISTRY.keys())
        raise BackendUnavailableError(
            f"Unknown backend: '{name}'. Available: {available}",
            backend_name=name,
        )

    loader, requires = _BACKEND_REGISTRY[name]

    try:
        return loader()
    except ImportError as e:
        if requires:
            raise BackendUnavailableError(
                f"Backend '{name}' requires '{requires}'. "
                f"Install with: pip install quantum-bridge[{requires}]",
                backend_name=name,
            ) from e
        raise BackendUnavailableError(
            f"Failed to load backend '{name}': {e}",
            backend_name=name,
        ) from e


def get_backend(name: str, **kwargs) -> QuantumBackend:
    """
    Get an initialized backend instance.

    Args:
        name: Backend name ("simulator", "qiskit", "cirq", etc.)
        **kwargs: Arguments passed to backend constructor

    Returns:
        Initialized backend instance

    Raises:
        BackendUnavailableError: If backend not found or dependency missing

    Example:
        # Simple usage
        backend = get_backend("simulator")

        # With configuration
        backend = get_backend("qiskit", backend_name="ibm_brisbane", use_ibm=True)
    """
    backend_class = get_backend_class(name)
    return backend_class(**kwargs)


def list_backends() -> list[str]:
    """
    List all registered backend names.

    Returns:
        List of backend names (may not all be available)
    """
    return list(_BACKEND_REGISTRY.keys())


def list_available_backends() -> list[str]:
    """
    List backends that can be loaded (dependencies satisfied).

    Returns:
        List of available backend names
    """
    available = []
    for name in _BACKEND_REGISTRY:
        try:
            get_backend_class(name)
            available.append(name)
        except BackendUnavailableError:
            pass
    return available


def is_backend_available(name: str) -> bool:
    """
    Check if a backend can be loaded.

    Args:
        name: Backend name

    Returns:
        True if backend is available
    """
    try:
        get_backend_class(name)
        return True
    except BackendUnavailableError:
        return False


# Convenience function for auto-selecting best available backend
def get_best_backend(prefer_hardware: bool = False) -> QuantumBackend:
    """
    Get the best available backend.

    Priority (prefer_hardware=False):
    1. Built-in simulator (always available)

    Priority (prefer_hardware=True):
    1. Qiskit (if available and configured for IBM)
    2. Cirq (if available)
    3. Built-in simulator

    Args:
        prefer_hardware: If True, prefer cloud/hardware backends

    Returns:
        Best available backend instance
    """
    if prefer_hardware:
        # Try cloud backends first
        for name in ["qiskit", "cirq"]:
            if is_backend_available(name):
                return get_backend(name)

    # Fall back to simulator
    return get_backend("simulator")
