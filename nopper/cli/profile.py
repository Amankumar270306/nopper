
import typer
from rich.console import Console
from rich.table import Table

from nopper.config import NodeConfig, load_config, save_config, update_config

app = typer.Typer(help="Manage preset profiles (nodes).")
console = Console()

@app.command("create")
def create_profile(
    name: str = typer.Argument(..., help="Profile name"),
    provider: str = typer.Option(..., "--provider", "-p", help="Provider for this profile (e.g. openai, anthropic)"),
    model: str | None = typer.Option(None, "--model", "-m", help="Default model for this profile"),
):
    """Create a new profile (local preset node)."""
    settings = load_config()
    
    if name in settings.nodes:
        console.print(f"[yellow]Profile '{name}' already exists. Overwriting.[/yellow]")
        
    api_key = settings.api_keys.get(provider)
    if not api_key:
        console.print(f"[yellow]Warning: No API key found for provider '{provider}'.[/yellow]")
        
    settings.nodes[name] = NodeConfig(
        type=provider,
        api_key=api_key,
        model=model
    )
    
    save_config(settings)
    console.print(f"[green]Successfully created profile:[/green] [bold]{name}[/bold]")

@app.command("list")
def list_profiles():
    """List all registered profiles."""
    settings = load_config()
    
    # We only show nodes that don't have base_url
    profiles = {k: v for k, v in settings.nodes.items() if not v.base_url}
    
    if not profiles:
        console.print("[yellow]No profiles configured.[/yellow]")
        return
        
    table = Table(title="Nopper Profiles")
    table.add_column("Profile Name", style="cyan")
    table.add_column("Provider", style="blue")
    table.add_column("Model", style="green")
    
    for name, node in profiles.items():
        table.add_row(name, node.type, node.model or "Not Set")
        
    console.print(table)

@app.command("remove")
def remove_profile(name: str = typer.Argument(..., help="The profile to remove")):
    """Remove a profile."""
    settings = load_config()
    
    if name not in settings.nodes:
        console.print(f"[red]Error:[/red] Profile '{name}' not found.")
        raise typer.Exit(1)
        
    del settings.nodes[name]
    save_config(settings)
    console.print(f"[green]Successfully removed profile:[/green] [bold]{name}[/bold]")

@app.command("use")
def use_profile(name: str = typer.Argument(..., help="The profile to use globally")):
    """Switch the globally active provider to this profile."""
    settings = load_config()
    
    if name not in settings.nodes:
        console.print(f"[red]Error:[/red] Profile '{name}' not found.")
        raise typer.Exit(1)
        
    try:
        update_config("provider", name)
        console.print(f"[green]Successfully switched to profile:[/green] [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)
