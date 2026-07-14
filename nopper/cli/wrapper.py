import json

import typer
from rich.console import Console
from rich.table import Table

from nopper.core.config import WrapperConfig
from nopper.core.manager import WrapperManager

app = typer.Typer(help="Manage AI wrappers")
console = Console()

@app.command()
def create(
    name: str, 
    node: str = typer.Option(None, "-n", "--node", help="Custom node to bind to the wrapper"),
    provider: str = typer.Option("openai", help="Default provider"),
    model: str = typer.Option("gpt-4o", help="Default model")
):
    """Create a new AI wrapper."""
    config = WrapperConfig(name=name, provider=provider, model=model, node=node)
    WrapperManager.save(config)
    console.print(f"[green]Wrapper '{name}' created successfully.[/green]")

@app.command("list")
def list_wrappers():
    """List all wrappers."""
    wrappers = WrapperManager.list()
    if not wrappers:
        console.print("No wrappers found.")
        return
        
    table = Table("Name", "Provider", "Model", "Node")
    for w in wrappers:
        try:
            config = WrapperManager.get(w)
            table.add_row(config.name, config.provider, config.model, config.node or "-")
        except Exception:
            table.add_row(w, "[red]ERROR[/red]", "-", "-")
    console.print(table)

@app.command()
def show(name: str):
    """Show details of a wrapper."""
    try:
        config = WrapperManager.get(name)
        console.print(config.model_dump_json(indent=2))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def delete(name: str):
    """Delete a wrapper."""
    if WrapperManager.delete(name):
        console.print(f"[green]Wrapper '{name}' deleted.[/green]")
    else:
        console.print(f"[red]Wrapper '{name}' not found.[/red]")

@app.command()
def use(
    name: str, 
    provider: str,
    node: str = typer.Option(None, "-cn", "--node", help="Update the node bound to the wrapper")
):
    """Update the provider (and optionally the node) of a wrapper."""
    try:
        config = WrapperManager.get(name)
        config.provider = provider
        if node is not None:
            config.node = node
        WrapperManager.save(config)
        console.print(f"[green]Wrapper '{name}' updated to use provider '{provider}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def model(name: str, model: str):
    """Update the model of a wrapper."""
    try:
        config = WrapperManager.get(name)
        config.model = model
        WrapperManager.save(config)
        console.print(f"[green]Wrapper '{name}' updated to use model '{model}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def temperature(name: str, temp: float):
    """Update the temperature of a wrapper."""
    try:
        config = WrapperManager.get(name)
        config.parameters["temperature"] = temp
        WrapperManager.save(config)
        console.print(f"[green]Wrapper '{name}' updated temperature to {temp}.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command("export")
def export_wrapper(name: str, file: str):
    """Export a wrapper to a file."""
    try:
        config = WrapperManager.get(name)
        with open(file, "w") as f:
            f.write(config.model_dump_json(indent=2))
        console.print(f"[green]Wrapper '{name}' exported to {file}.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command("import")
def import_wrapper(name: str, file: str):
    """Import a wrapper from a file."""
    try:
        with open(file, "r") as f:
            data = json.load(f)
        config = WrapperConfig(**data)
        config.name = name  # Ensure the name matches the intended import name
        WrapperManager.save(config)
        console.print(f"[green]Wrapper '{name}' imported from {file}.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def clone(name: str, new_name: str):
    """Clone an existing wrapper."""
    try:
        config = WrapperManager.get(name)
        config.name = new_name
        WrapperManager.save(config)
        console.print(f"[green]Wrapper '{name}' cloned to '{new_name}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def rename(name: str, new_name: str):
    """Rename an existing wrapper."""
    try:
        config = WrapperManager.get(name)
        config.name = new_name
        WrapperManager.save(config)
        WrapperManager.delete(name)
        console.print(f"[green]Wrapper '{name}' renamed to '{new_name}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
