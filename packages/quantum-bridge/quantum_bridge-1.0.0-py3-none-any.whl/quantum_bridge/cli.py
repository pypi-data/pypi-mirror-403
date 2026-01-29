"""Command-line interface for quantum-bridge.

Provides commands for running circuits, checking backends, and managing
configuration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.version_option(package_name="quantum-bridge")
def main() -> None:
    """Quantum-Bridge: Backend-agnostic quantum circuit execution.

    Run quantum circuits across multiple backends with automatic fallback
    and error mitigation.

    \b
    Quick start:
      qbridge backends list          # See available backends
      qbridge run circuit.qasm       # Run a circuit
      qbridge run circuit.qasm --mitigate  # Run with error mitigation

    For Python developers learning quantum computing, see our docs at:
    https://quantum-bridge.readthedocs.io
    """
    pass


@main.group()
def backends() -> None:
    """Manage quantum backends."""
    pass


@backends.command("list")
def backends_list() -> None:
    """List available quantum backends.

    Shows all backends that can be used, including which are installed
    and which require additional packages.
    """
    table = Table(title="Available Backends")
    table.add_column("Backend", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Install Command", style="dim")

    # Check simulator (always available with numpy)
    try:
        import numpy  # noqa: F401

        table.add_row("simulator", "[green]Available[/green]", "-")
    except ImportError:
        table.add_row("simulator", "[red]Missing numpy[/red]", "pip install numpy")

    # Check Qiskit
    try:
        import qiskit  # noqa: F401

        table.add_row("qiskit", "[green]Available[/green]", "-")
    except ImportError:
        table.add_row("qiskit", "[yellow]Not installed[/yellow]", "pip install quantum-bridge[qiskit]")

    # Check Cirq
    try:
        import cirq  # noqa: F401

        table.add_row("cirq", "[green]Available[/green]", "-")
    except ImportError:
        table.add_row("cirq", "[yellow]Not installed[/yellow]", "pip install quantum-bridge[cirq]")

    # Check Mitiq
    try:
        import mitiq  # noqa: F401

        table.add_row("mitiq (ZNE)", "[green]Available[/green]", "-")
    except ImportError:
        table.add_row("mitiq (ZNE)", "[yellow]Not installed[/yellow]", "pip install quantum-bridge[mitiq]")

    console.print(table)


@backends.command("health")
def backends_health() -> None:
    """Check health status of all backends.

    Verifies that backends can execute circuits successfully.
    """
    from quantum_bridge.execution import HybridExecutor

    console.print("[bold]Checking backend health...[/bold]\n")

    try:
        executor = HybridExecutor()
        health = executor.fallback_chain.health_check()

        for backend_name, is_healthy in health.items():
            status = "[green]Healthy[/green]" if is_healthy else "[red]Unhealthy[/red]"
            console.print(f"  {backend_name}: {status}")

    except ValueError as e:
        console.print(f"[red]No backends available: {e}[/red]")


@main.command()
@click.argument("circuit_file", type=click.Path(exists=True))
@click.option("--shots", "-s", default=1024, help="Number of measurement shots")
@click.option("--backend", "-b", help="Specific backend to use")
@click.option("--mitigate/--no-mitigate", default=False, help="Apply error mitigation (requires mitiq)")
@click.option("--output", "-o", type=click.Path(), help="Output file for results (JSON)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(
    circuit_file: str,
    shots: int,
    backend: Optional[str],
    mitigate: bool,
    output: Optional[str],
    verbose: bool,
) -> None:
    """Execute a quantum circuit.

    CIRCUIT_FILE can be an OpenQASM file (.qasm) or a Python file (.py)
    that defines a circuit.

    \b
    Examples:
      qbridge run bell.qasm
      qbridge run bell.qasm --shots 2048
      qbridge run bell.qasm --backend simulator
      qbridge run bell.qasm --mitigate
    """
    from quantum_bridge.config import ExecutionConfig, BackendConfig
    from quantum_bridge.execution import HybridExecutor

    # Load circuit from file
    circuit_path = Path(circuit_file)
    circuit = _load_circuit(circuit_path)

    if circuit is None:
        console.print(f"[red]Could not load circuit from {circuit_file}[/red]")
        sys.exit(1)

    # Configure execution
    config = ExecutionConfig(
        default_shots=shots,
    )

    if backend:
        config.backends = [BackendConfig(name=backend, priority=0)]

    # Create executor and run
    try:
        executor = HybridExecutor(config=config)

        if verbose:
            plan = executor.plan(circuit, shots=shots, mitigate=mitigate)
            console.print(Panel(str(plan), title="Execution Plan"))

        with console.status("[bold green]Executing circuit..."):
            result = executor.execute(circuit, shots=shots, mitigate=mitigate)

        # Display results
        _display_result(result, verbose)

        # Save to file if requested
        if output:
            _save_result(result, output)
            console.print(f"\n[dim]Results saved to {output}[/dim]")

    except ImportError as e:
        console.print(f"[red]Missing dependency: {e}[/red]")
        console.print("[dim]Try: pip install quantum-bridge[all][/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@main.command()
@click.argument("circuit_file", type=click.Path(exists=True))
@click.option("--shots", "-s", default=1024, help="Number of measurement shots")
@click.option("--backend", "-b", help="Specific backend to use")
def plan(circuit_file: str, shots: int, backend: Optional[str]) -> None:
    """Show execution plan without running.

    Displays what would happen if you ran the circuit, including
    backend selection and fallback chain.
    """
    from quantum_bridge.config import ExecutionConfig, BackendConfig
    from quantum_bridge.execution import HybridExecutor

    circuit_path = Path(circuit_file)
    circuit = _load_circuit(circuit_path)

    if circuit is None:
        console.print(f"[red]Could not load circuit from {circuit_file}[/red]")
        sys.exit(1)

    config = ExecutionConfig(default_shots=shots)
    if backend:
        config.backends = [BackendConfig(name=backend, priority=0)]

    try:
        executor = HybridExecutor(config=config)
        execution_plan = executor.plan(circuit, shots=shots)
        console.print(Panel(str(execution_plan), title="Execution Plan"))

        if execution_plan.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in execution_plan.warnings:
                console.print(f"  - {warning}")

    except Exception as e:
        console.print(f"[red]Planning failed: {e}[/red]")
        sys.exit(1)


@main.command()
def info() -> None:
    """Show information about quantum-bridge installation."""
    from quantum_bridge import __version__

    console.print(Panel(
        f"[bold cyan]quantum-bridge[/bold cyan] v{__version__}\n\n"
        "Backend-agnostic bridge for quantum-classical hybrid workflows.\n\n"
        "[dim]Documentation: https://quantum-bridge.readthedocs.io[/dim]",
        title="About"
    ))

    # Show installed extras
    console.print("\n[bold]Installed Components:[/bold]")

    components = [
        ("numpy", "Core numerics"),
        ("qiskit", "IBM Quantum backend"),
        ("cirq", "Google Cirq backend"),
        ("mitiq", "Error mitigation"),
    ]

    for pkg, desc in components:
        try:
            __import__(pkg)
            console.print(f"  [green]OK[/green] {pkg} - {desc}")
        except ImportError:
            console.print(f"  [dim]--[/dim] {pkg} - {desc} [dim](not installed)[/dim]")


def _load_circuit(path: Path):
    """Load a circuit from a file.

    Supports:
    - .qasm files (OpenQASM format)
    - .py files (must define a 'circuit' variable)
    """
    suffix = path.suffix.lower()

    if suffix == ".qasm":
        # Read QASM file
        return path.read_text()

    elif suffix == ".py":
        # Execute Python file and extract circuit
        import importlib.util

        spec = importlib.util.spec_from_file_location("circuit_module", path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            console.print(f"[red]Error loading Python file: {e}[/red]")
            return None

        # Look for 'circuit' variable
        if hasattr(module, "circuit"):
            return module.circuit
        else:
            console.print("[red]Python file must define a 'circuit' variable[/red]")
            return None

    else:
        console.print(f"[red]Unsupported file type: {suffix}[/red]")
        console.print("[dim]Supported: .qasm, .py[/dim]")
        return None


def _display_result(result, verbose: bool) -> None:
    """Display execution result in a nice format."""
    console.print("\n[bold green]Execution Complete![/bold green]\n")

    # Results table
    table = Table(title="Measurement Results")
    table.add_column("Bitstring", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Probability", justify="right")

    total = sum(result.counts.values())
    sorted_counts = sorted(result.counts.items(), key=lambda x: -x[1])

    # Show top 10 results
    for bitstring, count in sorted_counts[:10]:
        prob = count / total if total > 0 else 0
        table.add_row(bitstring, str(count), f"{prob:.4f}")

    if len(sorted_counts) > 10:
        table.add_row("...", f"({len(sorted_counts) - 10} more)", "")

    console.print(table)

    # Metadata
    console.print(f"\n[dim]Backend: {result.backend_name}[/dim]")
    console.print(f"[dim]Shots: {result.shots}[/dim]")
    console.print(f"[dim]Time: {result.execution_time_ms:.1f}ms[/dim]")

    if verbose and result.metadata:
        console.print("\n[dim]Metadata:[/dim]")
        for key, value in result.metadata.items():
            console.print(f"  [dim]{key}: {value}[/dim]")


def _save_result(result, output_path: str) -> None:
    """Save result to JSON file."""
    data = {
        "counts": result.counts,
        "shots": result.shots,
        "backend": result.backend_name,
        "execution_time_ms": result.execution_time_ms,
        "metadata": result.metadata,
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
