import typer
from rich.console import Console
from rich.table import Table

from nopper.config import load_config, update_config

app = typer.Typer(help="Manage prompt templates.")
console = Console()

@app.command("add")
def add_template(name: str = typer.Argument(..., help="The template name"), prompt: str = typer.Argument(..., help="The prompt text")):
    """Add a prompt template."""
    settings = load_config()
    templates = settings.templates
    templates[name] = prompt
    try:
        update_config("templates", templates)
        console.print(f"[green]Successfully added template:[/green] [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command("list")
def list_templates():
    """List all registered templates."""
    settings = load_config()
    if not settings.templates:
        console.print("[yellow]No templates configured.[/yellow]")
        return
        
    table = Table(title="Prompt Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Prompt", style="green")
    
    for name, prompt in settings.templates.items():
        table.add_row(name, prompt)
        
    console.print(table)

@app.command("remove")
def remove_template(name: str = typer.Argument(..., help="The template to remove")):
    """Remove a template."""
    settings = load_config()
    templates = settings.templates
    if name not in templates:
        console.print(f"[red]Error:[/red] Template '{name}' not found.")
        raise typer.Exit(1)
        
    del templates[name]
    try:
        update_config("templates", templates)
        console.print(f"[green]Successfully removed template:[/green] [bold]{name}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)
