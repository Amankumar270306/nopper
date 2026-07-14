import typer
from rich.console import Console
from rich.table import Table

from nopper import AI
from nopper.config import load_config, update_config

app = typer.Typer(help="Manage the active AI model.")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Show the currently active model if no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        settings = load_config()
        if settings.model:
            console.print(f"Current active model: [bold green]{settings.model}[/bold green] (Provider: {settings.provider})")
        else:
            console.print(f"No default model set for provider [bold]{settings.provider}[/bold].")
            console.print("Use [yellow]nopper model set <model_name>[/yellow] to set one.")

@app.command(name="set")
def set_model(model: str = typer.Argument(..., help="The model name to use (e.g. gpt-4o, llama3)")):
    """Set the active AI model globally."""
    try:
        update_config("model", model)
        console.print(f"[green]Successfully set active model to:[/green] [bold]{model}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command(name="list")
def list_models():
    """List available models from the currently active provider."""
    settings = load_config()
    console.print(f"Fetching models for active provider: [bold]{settings.provider}[/bold]...")

    try:
        ai = AI()
        models = ai.models()

        if not models:
            console.print("[yellow]No models found or the provider does not support listing models.[/yellow]")
            return

        table = Table(title=f"Available Models ({settings.provider})")
        table.add_column("Model Name", style="cyan", no_wrap=True)

        for m in sorted(models):

            if m == settings.model:
                table.add_row(f"{m} (active)", style="bold green")
            else:
                table.add_row(m)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to fetch models:[/red] {e!s}")
        console.print("Hint: Check if your API key is correctly configured for this provider.")
        raise typer.Exit(1)

