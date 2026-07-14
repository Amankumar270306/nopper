import typer
from rich.console import Console
from rich.table import Table

from nopper.cache import clear_cache as clear_cache_core
from nopper.cache import get_cache_stats
from nopper.config import load_config, update_config

app = typer.Typer(help="Manage response cache.")
console = Console()

@app.command("enable")
def enable_cache():
    """Enable response caching."""
    try:
        update_config("cache_enabled", True)
        console.print("[green]Response caching enabled.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to enable caching:[/red] {e}")

@app.command("disable")
def disable_cache():
    """Disable response caching."""
    try:
        update_config("cache_enabled", False)
        console.print("[green]Response caching disabled.[/green]")
    except Exception as e:
        console.print(f"[red]Failed to disable caching:[/red] {e}")

@app.command("clear")
def clear_cache():
    """Clear all cached responses."""
    count = clear_cache_core()
    console.print(f"[green]Cache cleared successfully.[/green] ({count} entries removed)")

@app.command("stats")
def cache_stats():
    """Show cache statistics."""
    stats = get_cache_stats()
    
    settings = load_config()
    status = "[green]Enabled[/green]" if getattr(settings, "cache_enabled", False) else "[yellow]Disabled[/yellow]"
    
    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Status", status)
    table.add_row("Entries", str(stats["entries"]))
    table.add_row("Size", f"{stats['size_bytes'] / 1024:.2f} KB")
    
    console.print(table)
