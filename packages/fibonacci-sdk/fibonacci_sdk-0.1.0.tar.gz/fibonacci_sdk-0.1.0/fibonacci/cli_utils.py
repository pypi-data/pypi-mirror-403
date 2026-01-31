"""
Fibonacci SDK - CLI Utilities

Banner, formatting, and display utilities for CLI.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


FIBONACCI_BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ███████╗██╗██████╗  ██████╗ ███╗   ██╗ █████╗  ██████╗ ██████╗██╗  ║
║   ██╔════╝██║██╔══██╗██╔═══██╗████╗  ██║██╔══██╗██╔════╝██╔════╝██║  ║
║   █████╗  ██║██████╔╝██║   ██║██╔██╗ ██║███████║██║     ██║     ██║  ║
║   ██╔══╝  ██║██╔══██╗██║   ██║██║╚██╗██║██╔══██║██║     ██║     ██║  ║
║   ██║     ██║██████╔╝╚██████╔╝██║ ╚████║██║  ██║╚██████╗╚██████╗██║  ║
║   ╚═╝     ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝╚═╝  ║
║                                                                      ║
║              AI-Powered Workflow Automation SDK                      ║
║                    Build. Deploy. Execute.                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

FIBONACCI_MINI = """
  _____ _ _                                _   ____  ____  _  __
 |  ___(_) |__   ___  _ __   __ _  ___ ___(_) / ___||  _ \| |/ /
 | |_  | | '_ \ / _ \| '_ \ / _` |/ __/ __| | \___ \| | | | ' / 
 |  _| | | |_) | (_) | | | | (_| | (_| (__| |  ___) | |_| | . \ 
 |_|   |_|_.__/ \___/|_| |_|\__,_|\___\___|_| |____/|____/|_|\_\\
                                                                 
         AI Workflow Automation • Build. Deploy. Execute.
"""

def show_banner(version: str = "0.1.0"):
    """Show the Fibonacci SDK banner."""
    console.print(FIBONACCI_BANNER, style="bold cyan")
    console.print(f"[dim]Version {version} • https://fibonacci.today[/dim]\n")


def show_mini_banner(version: str = "0.1.0"):
    """Show compact banner."""
    console.print(FIBONACCI_MINI, style="bold cyan")
    console.print(f"[dim]v{version}[/dim]\n")


def show_success(message: str):
    """Show success message."""
    console.print(f"[green]✓[/green] {message}")


def show_error(message: str):
    """Show error message."""
    console.print(f"[red]✗[/red] {message}")


def show_info(message: str):
    """Show info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def show_warning(message: str):
    """Show warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def show_step(step_num: int, message: str):
    """Show numbered step."""
    console.print(f"[bold cyan]{step_num}.[/bold cyan] {message}")


def show_panel(title: str, content: str, style: str = "cyan"):
    """Show content in a panel."""
    panel = Panel(
        content,
        title=f"[bold]{title}[/bold]",
        border_style=style,
        box=box.ROUNDED
    )
    console.print(panel)


def show_workflow_summary(
    workflow_id: str,
    name: str,
    nodes: int,
    cost_estimate: float
):
    """Show workflow summary."""
    summary = f"""
[cyan]Workflow ID:[/cyan] {workflow_id}
[cyan]Name:[/cyan] {name}
[cyan]Nodes:[/cyan] {nodes}
[cyan]Est. Cost:[/cyan] ${cost_estimate:.4f}
"""
    show_panel("Workflow Deployed", summary.strip(), style="green")


def show_execution_result(
    run_id: str,
    status: str,
    duration: float,
    cost: float,
    nodes_executed: int
):
    """Show execution result."""
    status_color = "green" if status == "completed" else "red"
    
    result = f"""
[cyan]Run ID:[/cyan] {run_id}
[cyan]Status:[/cyan] [{status_color}]{status}[/{status_color}]
[cyan]Duration:[/cyan] {duration:.2f}s
[cyan]Cost:[/cyan] ${cost:.4f}
[cyan]Nodes Executed:[/cyan] {nodes_executed}
"""
    show_panel("Execution Complete", result.strip(), style=status_color)


def show_progress(message: str):
    """Show progress message."""
    console.print(f"[yellow]⏳[/yellow] {message}...")



__all__ = [
    # Banners
    "FIBONACCI_BANNER",
    "FIBONACCI_MINI",
    "show_banner",
    "show_mini_banner",
    # Messages
    "show_success",
    "show_error",
    "show_info",
    "show_warning",
    "show_step",
    "show_panel",
    "show_progress",
    # Display
    "show_workflow_summary",
    "show_execution_result",
    # Console
    "console",
]


