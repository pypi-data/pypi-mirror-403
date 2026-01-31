"""
Sematryx CLI
"""

import json
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from . import __version__
from .client import Sematryx
from .exceptions import SematryxError, AuthenticationError

app = typer.Typer(
    name="sematryx",
    help="Sematryx CLI - AI-powered optimization that explains itself",
    add_completion=False,
)
console = Console()


def get_api_key() -> str:
    """Get API key from environment or prompt"""
    api_key = os.environ.get("sematryx_API_KEY")
    if not api_key:
        console.print("[red]Error:[/red] sematryx_API_KEY environment variable not set")
        console.print("\nSet it with:")
        console.print("  export sematryx_API_KEY=sk-your-api-key")
        console.print("\nOr get a key at: https://sematryx.com/api-keys")
        raise typer.Exit(1)
    return api_key


@app.command()
def version():
    """Show version information"""
    console.print(f"Sematryx CLI v{__version__}")


@app.command()
def health():
    """Check API health status"""
    api_key = get_api_key()
    
    with console.status("Checking API health..."):
        try:
            client = Sematryx(api_key=api_key)
            status = client.health()
            
            console.print(Panel(
                f"[green]✓[/green] API is healthy\n"
                f"Version: {status.version}\n"
                f"Latency: {status.latency_ms:.0f}ms",
                title="Sematryx API Status"
            ))
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def usage():
    """Show current usage and limits"""
    api_key = get_api_key()
    
    with console.status("Fetching usage info..."):
        try:
            client = Sematryx(api_key=api_key)
            info = client.get_usage()
            
            table = Table(title="Account Usage")
            table.add_column("Metric", style="cyan")
            table.add_column("Used", style="yellow")
            table.add_column("Limit", style="green")
            
            table.add_row(
                "Optimizations",
                str(info.optimizations_used),
                str(info.optimizations_limit) if info.optimizations_limit > 0 else "Unlimited"
            )
            table.add_row(
                "Private Storage",
                f"{info.private_storage_used_mb:.1f} MB",
                f"{info.private_storage_limit_mb:.0f} MB" if info.private_storage_limit_mb > 0 else "Unlimited"
            )
            table.add_row(
                "Learning Accesses",
                str(info.learning_accesses_used),
                str(info.learning_accesses_limit) if info.learning_accesses_limit > 0 else "Unlimited"
            )
            
            console.print(table)
            console.print(f"\n[dim]Tier: {info.tier}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def optimize(
    objective: str = typer.Argument(..., help="Objective function as string expression"),
    bounds: str = typer.Option(
        ..., "--bounds", "-b",
        help="Variable bounds as JSON, e.g., '{\"x\": [-5, 5], \"y\": [-5, 5]}'"
    ),
    minimize: bool = typer.Option(True, "--minimize/--maximize", help="Minimize or maximize"),
    max_evals: int = typer.Option(1000, "--max-evals", "-n", help="Maximum evaluations"),
    explain: int = typer.Option(2, "--explain", "-e", help="Explanation level (0-4)"),
    strategy: str = typer.Option("auto", "--strategy", "-s", help="Optimization strategy"),
    output: str = typer.Option("pretty", "--output", "-o", help="Output format: pretty, json"),
):
    """
    Run an optimization from the command line.
    
    Example:
        sematryx optimize "x**2 + y**2" --bounds '{"x": [-5, 5], "y": [-5, 5]}'
    """
    api_key = get_api_key()
    
    try:
        bounds_dict = json.loads(bounds)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing bounds:[/red] {e}")
        console.print("Bounds should be valid JSON, e.g., '{\"x\": [-5, 5]}'")
        raise typer.Exit(1)
    
    variables = [
        {"name": name, "bounds": tuple(b)}
        for name, b in bounds_dict.items()
    ]
    
    with console.status("Running optimization..."):
        try:
            client = Sematryx(api_key=api_key)
            result = client.optimize(
                objective="minimize" if minimize else "maximize",
                variables=variables,
                objective_function=objective,
                max_evaluations=max_evals,
                explanation_level=explain,
                strategy=strategy,
            )
            
            if output == "json":
                print(json.dumps(result.model_dump(), indent=2, default=str))
            else:
                # Pretty output
                console.print(Panel(
                    f"[green]✓[/green] Optimization {'succeeded' if result.success else 'failed'}",
                    title="Result"
                ))
                
                table = Table(title="Solution")
                table.add_column("Variable", style="cyan")
                table.add_column("Value", style="yellow")
                
                for var, val in result.solution.items():
                    table.add_row(var, f"{val:.6f}")
                
                console.print(table)
                console.print(f"\n[bold]Objective Value:[/bold] {result.objective_value:.6f}")
                console.print(f"[dim]Strategy: {result.strategy_used} | Evaluations: {result.evaluations_used} | Time: {result.duration_seconds:.2f}s[/dim]")
                
                if result.explanation:
                    console.print(Panel(result.explanation, title="Explanation"))
                
                if result.audit_id:
                    console.print(f"\n[dim]Audit ID: {result.audit_id}[/dim]")
                    
        except AuthenticationError:
            console.print("[red]Error:[/red] Invalid API key")
            raise typer.Exit(1)
        except SematryxError as e:
            console.print(f"[red]Error:[/red] {e.message}")
            raise typer.Exit(1)


@app.command()
def configure():
    """Configure Sematryx CLI (set API key)"""
    console.print("[bold]Sematryx CLI Configuration[/bold]\n")
    
    current_key = os.environ.get("sematryx_API_KEY", "")
    if current_key:
        masked = current_key[:7] + "..." + current_key[-4:]
        console.print(f"Current API key: {masked}")
    
    console.print("\nTo set your API key, add to your shell profile:")
    console.print("\n  [cyan]export sematryx_API_KEY=sk-your-api-key[/cyan]")
    console.print("\nGet your API key at: [link]https://sematryx.com/api-keys[/link]")


def main():
    """CLI entry point"""
    app()


if __name__ == "__main__":
    main()

