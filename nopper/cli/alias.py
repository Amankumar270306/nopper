import typer
from rich.console import Console
from rich.table import Table

from nopper.config import load_config, update_config

app = typer.Typer(help="Manage model aliases.")
console = Console()

@app.command("add")
def add_alias(alias: str = typer.Argument(..., help="The alias name"), model: str = typer.Argument(..., help="The actual model name")):
    """Add or update an alias for a model."""
    settings = load_config()
    aliases = settings.aliases
    aliases[alias] = model
    try:
        update_config("aliases", aliases)
        console.print(f"[green]Successfully added alias:[/green] [bold]{alias}[/bold] -> [bold]{model}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command("list")
def list_aliases():
    """List all registered aliases."""
    settings = load_config()
    if not settings.aliases:
        console.print("[yellow]No aliases configured.[/yellow]")
        return
        
    table = Table(title="Model Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Model", style="green")
    
    for alias, model in settings.aliases.items():
        table.add_row(alias, model)
        
    console.print(table)

@app.command("remove")
def remove_alias(alias: str = typer.Argument(..., help="The alias to remove")):
    """Remove a registered alias."""
    settings = load_config()
    aliases = settings.aliases
    if alias not in aliases:
        console.print(f"[red]Error:[/red] Alias '{alias}' not found.")
        raise typer.Exit(1)
        
    del aliases[alias]
    try:
        update_config("aliases", aliases)
        console.print(f"[green]Successfully removed alias:[/green] [bold]{alias}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)
