import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from nopper.config import load_config, reset_config, update_config

app = typer.Typer(help="Manage Nopper configuration.")
console = Console()

@app.command("show")
def show():
    """Display the current configuration."""
    settings = load_config()
    table = Table(title="Nopper Configuration")

    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in settings.model_dump().items():

        if key == "api_keys":
            masked_keys = {k: "********" for k in value}
            table.add_row(key, str(masked_keys))
        else:
            table.add_row(key, str(value))

    console.print(table)

@app.command("set")
def set_key(key: str = typer.Argument(..., help="Configuration key to set"), value: str = typer.Argument(..., help="Value to set")):
    """Update a specific configuration value."""
    try:
        update_config(key, value)
        console.print(f"[green]Successfully updated [bold]{key}[/bold] to [bold]{value}[/bold][/green]")
    except KeyError as e:
        console.print(f"[red]Error:[/red] {e}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}")

@app.command("reset")
def reset():
    """Reset configuration to defaults."""
    confirm = typer.confirm("Are you sure you want to reset all configuration to defaults?")
    if confirm:
        reset_config()
        console.print("[green]Configuration reset successfully.[/green]")
    else:
        console.print("[yellow]Reset cancelled.[/yellow]")

