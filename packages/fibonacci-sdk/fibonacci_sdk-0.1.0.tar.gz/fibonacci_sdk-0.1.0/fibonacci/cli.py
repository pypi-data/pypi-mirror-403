"""
Fibonacci CLI

Command-line interface for Fibonacci SDK with security features.
"""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from fibonacci import Workflow, __version__
from fibonacci.config import Config
from fibonacci.client import FibonacciClient
from fibonacci.exceptions import FibonacciError
from fibonacci.cli_utils import show_mini_banner

app = typer.Typer(
    name="fibonacci",
    help="Fibonacci Workflow Automation CLI",
    add_completion=False,
)
console = Console()

# Security sub-app
security_app = typer.Typer(help="Security and credential management")

# Audit sub-app
audit_app = typer.Typer(help="Audit log management")


# ============================================================================
# CORE COMMANDS
# ============================================================================

@app.command()
def version():
    """Show Fibonacci SDK version."""
    show_mini_banner(__version__)


@app.command()
def init(name: str):
    """
    Initialize a new workflow project.
    
    Example:
        fibonacci init "My Workflow"
    """
    workflow_path = Path(f"{name.lower().replace(' ', '_')}.py")
    
    if workflow_path.exists():
        console.print(f"[red]Error: {workflow_path} already exists[/red]")
        raise typer.Exit(1)
    
    template = f'''"""
{name} Workflow

Created with Fibonacci SDK.
"""

from fibonacci import Workflow, LLMNode, ToolNode

# Create workflow
wf = Workflow(
    name="{name}",
    description="TODO: Add description"
)

# TODO: Add your nodes here
# Example:
# node = LLMNode(
#     id="analyze",
#     name="Analyze Data",
#     instruction="Analyze this: {{{{input.text}}}}"
# )
# wf.add_node(node)

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("FIBONACCI_API_KEY")
    
    if not api_key:
        print("Error: FIBONACCI_API_KEY not set")
        exit(1)
    
    # Deploy
    workflow_id = wf.deploy(api_key=api_key)
    print(f"Deployed! ID: {{workflow_id}}")
    
    # Execute
    # result = wf.run(input_data={{"text": "hello"}})
    # print(result.output_data)
'''
    
    workflow_path.write_text(template)
    console.print(f"[green]✓[/green] Created: {workflow_path}")
    console.print(f"\nNext: Edit {workflow_path} and add your nodes")


@app.command()
def list():
    """List workflows on Fibonacci platform."""
    async def _list():
        config = Config.from_env()
        config.validate_ready()
        
        async with FibonacciClient(config) as client:
            workflows = await client.list_workflows(limit=20)
            
            if not workflows:
                console.print("[yellow]No workflows found[/yellow]")
                return
            
            table = Table(title="Workflows")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Nodes", justify="right")
            table.add_column("Active", style="green")
            
            for wf in workflows:
                active = "✓" if wf.get("is_active") else "✗"
                nodes = len(wf.get("definition", {}).get("nodes", []))
                wf_id = str(wf["id"])[:8] + "..."
                table.add_row(wf["name"], wf_id, str(nodes), active)
            
            console.print(table)
    
    try:
        asyncio.run(_list())
    except FibonacciError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1)


@app.command()
def run(workflow_id: str, input_json: str):
    """
    Execute a workflow.
    
    Example:
        fibonacci run abc-123 '{"text": "hello"}'
    """
    async def _run():
        config = Config.from_env()
        config.validate_ready()
        
        try:
            input_data = json.loads(input_json)
        except json.JSONDecodeError:
            console.print(f"[red]Invalid JSON[/red]")
            raise typer.Exit(1)
        
        async with FibonacciClient(config) as client:
            console.print(f"[cyan]Executing {workflow_id}...[/cyan]")
            
            run_status = await client.execute_workflow(workflow_id, input_data)
            console.print(f"[yellow]Waiting for completion...[/yellow]")
            run_status = await client.wait_for_completion(run_status.id)
            
            table = Table(title="Results")
            table.add_column("Field", style="cyan")
            table.add_column("Value")
            
            table.add_row("Run ID", run_status.id)
            table.add_row("Status", run_status.status)
            table.add_row("Duration", f"{run_status.duration_seconds:.2f}s" if run_status.duration_seconds else "N/A")
            table.add_row("Cost", f"${run_status.total_cost:.4f}" if run_status.total_cost else "N/A")
            table.add_row("Nodes", str(run_status.nodes_executed))
            
            console.print(table)
            
            if run_status.status == "completed" and run_status.output_data:
                console.print("\n[green]Output:[/green]")
                rprint(run_status.output_data)
            elif run_status.error_message:
                console.print(f"\n[red]Error: {run_status.error_message}[/red]")
    
    try:
        asyncio.run(_run())
    except FibonacciError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1)


@app.command()
def status(run_id: str):
    """
    Check workflow run status.
    
    Example:
        fibonacci status run-123
    """
    async def _status():
        config = Config.from_env()
        config.validate_ready()
        
        async with FibonacciClient(config) as client:
            run_status = await client.get_run_status(run_id)
            
            table = Table(title=f"Run: {run_id}")
            table.add_column("Field", style="cyan")
            table.add_column("Value")
            
            table.add_row("Status", run_status.status)
            table.add_row("Started", run_status.started_at or "N/A")
            table.add_row("Completed", run_status.completed_at or "N/A")
            table.add_row("Duration", f"{run_status.duration_seconds:.2f}s" if run_status.duration_seconds else "N/A")
            table.add_row("Cost", f"${run_status.total_cost:.4f}" if run_status.total_cost else "N/A")
            
            console.print(table)
    
    try:
        asyncio.run(_status())
    except FibonacciError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1)


# ============================================================================
# SECURITY COMMANDS
# ============================================================================

@security_app.command("status")
def security_status():
    """Check security status of API key storage."""
    try:
        from fibonacci.keychain_storage import check_security_status
        
        status = check_security_status()
        
        table = Table(title="🔒 Security Status")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        
        keyring_status = "✅ Available" if status.get('keyring_available') else "❌ Not installed"
        table.add_row("Keyring Support", keyring_status)
        
        if status.get('keyring_available'):
            keyring_working = "✅ Working" if status.get('keyring_working') else "⚠️  Not working"
            table.add_row("Keyring Status", keyring_working)
        
        if status.get('api_key_in_keychain'):
            key_location = "🔐 Keychain (Secure)"
        elif status.get('api_key_in_env'):
            key_location = "⚠️  .env file (Plaintext)"
        else:
            key_location = "❌ Not found"
        table.add_row("API Key Location", key_location)
        
        level = status.get('security_level', 'unknown')
        if level == 'high':
            level_display = "🟢 High (Encrypted)"
        elif level == 'low':
            level_display = "🟡 Low (Plaintext)"
        else:
            level_display = "🔴 None (No key)"
        table.add_row("Security Level", level_display)
        
        console.print(table)
        
        if level == 'low':
            console.print()
            console.print(Panel(
                "⚠️  [bold yellow]Security Recommendation[/bold yellow]\n\n"
                "Your API key is stored in plaintext.\n"
                "Use keychain storage for better security:\n\n"
                "[cyan]fibonacci security migrate[/cyan]",
                border_style="yellow"
            ))
        
    except ImportError:
        console.print("[yellow]⚠️  Keyring not installed[/yellow]")
        console.print("Install with: [cyan]pip install keyring[/cyan]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("save")
def save_api_key(
    api_key: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Save API key to secure keychain."""
    try:
        from fibonacci.keychain_storage import save_api_key_secure
        
        if not api_key.startswith("fib_"):
            console.print("[red]Invalid API key format. Must start with 'fib_'[/red]")
            raise typer.Exit(1)
        
        success = save_api_key_secure(api_key)
        
        if success:
            console.print("[green]✅ API key saved securely![/green]")
            console.print("You can now remove it from .env file")
        else:
            console.print("[red]❌ Failed to save API key[/red]")
            raise typer.Exit(1)
            
    except ImportError:
        console.print("[red]Keyring not installed. Install with:[/red]")
        console.print("[cyan]pip install keyring[/cyan]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("get")
def get_api_key():
    """Retrieve API key from keychain (redacted display)."""
    try:
        from fibonacci.keychain_storage import get_api_key_secure
        from fibonacci.secure_config import redact_api_key
        
        api_key = get_api_key_secure()
        
        if api_key:
            redacted = redact_api_key(api_key)
            console.print(f"[green]✅ API Key:[/green] {redacted}")
        else:
            console.print("[yellow]⚠️  No API key found[/yellow]")
            console.print("Save one with: [cyan]fibonacci security save[/cyan]")
            
    except ImportError:
        console.print("[red]Keyring not installed[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@security_app.command("migrate")
def migrate_to_keychain():
    """Migrate API key from .env to secure keychain."""
    try:
        from fibonacci.keychain_storage import migrate_to_keychain as do_migration
        
        console.print("🔄 Migrating API key to keychain...")
        
        success = do_migration()
        
        if success:
            console.print()
            console.print(Panel(
                "[green]✅ Migration successful![/green]\n\n"
                "Your API key is now stored securely in the system keychain.\n"
                "You can remove FIBONACCI_API_KEY from your .env file.",
                border_style="green"
            ))
        else:
            raise typer.Exit(1)
            
    except ImportError:
        console.print("[red]Keyring not installed. Install with:[/red]")
        console.print("[cyan]pip install keyring[/cyan]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# AUDIT COMMANDS
# ============================================================================

@audit_app.command("view")
def view_audit_logs(
    limit: int = typer.Option(20, help="Number of events to show"),
    event_type: str = typer.Option(None, help="Filter by event type")
):
    """View recent audit log events."""
    try:
        from fibonacci.audit_logging import get_audit_logger, AuditEventType
        
        logger = get_audit_logger()
        
        filter_type = None
        if event_type:
            try:
                filter_type = AuditEventType(event_type)
            except ValueError:
                console.print(f"[red]Invalid event type: {event_type}[/red]")
                raise typer.Exit(1)
        
        events = logger.get_recent_events(event_type=filter_type, limit=limit)
        
        if not events:
            console.print("[yellow]No audit events found[/yellow]")
            return
        
        table = Table(title=f"📋 Audit Log (Last {len(events)} events)")
        table.add_column("Time", style="dim")
        table.add_column("Event", style="cyan")
        table.add_column("Details")
        
        for event in events:
            timestamp = event.get('timestamp', '')[:19]
            event_type_str = event.get('event_type', 'unknown')
            
            details = []
            if 'endpoint' in event:
                details.append(f"Endpoint: {event['endpoint']}")
            if 'status_code' in event:
                details.append(f"Status: {event['status_code']}")
            if 'error' in event:
                details.append(f"Error: {event['error']}")
            
            details_str = " | ".join(details) if details else "-"
            
            table.add_row(timestamp, event_type_str, details_str)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@audit_app.command("clear")
def clear_audit_logs():
    """Clear audit log files."""
    confirm = typer.confirm("Are you sure you want to clear all audit logs?")
    
    if not confirm:
        console.print("Cancelled")
        return
    
    try:
        from pathlib import Path
        
        log_dir = Path.home() / ".fibonacci" / "logs"
        
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                log_file.unlink()
            console.print("[green]✅ Audit logs cleared[/green]")
        else:
            console.print("[yellow]No logs to clear[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


# Register sub-apps
app.add_typer(security_app, name="security")
app.add_typer(audit_app, name="audit")


if __name__ == "__main__":
    app()


__all__ = [
    "app",
    "security_app",
    "audit_app",
]



