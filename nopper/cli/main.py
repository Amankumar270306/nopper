
import typer
from rich.console import Console

from nopper.cli.alias import app as alias_app
from nopper.cli.cache import app as cache_app
from nopper.cli.config import app as config_app
from nopper.cli.model import app as model_app
from nopper.cli.node import app as node_app
from nopper.cli.profile import app as profile_app
from nopper.cli.start import app as start_app
from nopper.cli.template import app as template_app
from nopper.cli.wrapper import app as wrapper_app
from nopper.config import load_config, update_config
from nopper.providers import list_providers

app = typer.Typer(
    name="nopper",
    help="Manage every AI provider from one unified interface.",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()

app.add_typer(config_app, name="config", help="Manage Nopper configuration.")
app.add_typer(model_app, name="model", help="Manage active AI model.")
app.add_typer(start_app, name="start", help="Interactive setup wizard for Nopper.")
app.add_typer(node_app, name="node", help="Manage custom remote nodes (e.g. Tailscale).")
app.add_typer(alias_app, name="alias", help="Manage model aliases.")
app.add_typer(profile_app, name="profile", help="Manage preset profiles (nodes).")
app.add_typer(cache_app, name="cache", help="Manage response cache.")
app.add_typer(template_app, name="template", help="Manage prompt templates.")
app.add_typer(wrapper_app, name="wrapper", help="Manage AI wrappers.")

@app.callback()
def main(ctx: typer.Context):
    """
    Nopper - One Python package + CLI to manage every AI provider.
    """
    if ctx.invoked_subcommand is None:
        console.print("[bold blue]Welcome to Nopper[/bold blue] 🚀")
        console.print("Run [bold cyan]nopper --help[/bold cyan] for usage.")

@app.command()
def init():
    """Initialize Nopper configuration."""
    console.print("[green]Initializing Nopper...[/green]")

@app.command()
def login(provider: str | None = typer.Option(None, help="The provider to login to")):
    """Login and store API keys securely."""
    from rich.prompt import Prompt

    from nopper.config import load_config, update_config
    
    settings = load_config()
    target_provider = provider or settings.provider
    
    api_key = Prompt.ask(f"Enter API Key for [bold cyan]{target_provider}[/bold cyan] (input hidden)", password=True)
    if api_key:
        keys = settings.api_keys
        keys[target_provider] = api_key
        update_config("api_keys", keys)
        console.print(f"[green]Successfully saved API key for {target_provider}.[/green]")
    else:
        console.print("[yellow]No API key provided. Login cancelled.[/yellow]")

@app.command()
def logout(provider: str | None = typer.Option(None, help="The provider to logout from")):
    """Remove stored API keys."""
    from nopper.config import load_config, update_config
    
    settings = load_config()
    target_provider = provider or settings.provider
    
    if target_provider in settings.api_keys:
        keys = settings.api_keys
        del keys[target_provider]
        update_config("api_keys", keys)
        console.print(f"[green]Successfully removed API key for {target_provider}.[/green]")
    else:
        console.print(f"[yellow]No API key found for {target_provider}.[/yellow]")

@app.command()
def use(provider: str):
    """Switch the active AI provider."""
    provider = provider.lower()
    available_providers = list_providers()
    if provider not in available_providers:
        console.print(f"[red]Error:[/red] Provider '{provider}' is not registered.")
        console.print(f"Available providers: {', '.join(available_providers)}")
        raise typer.Exit(1)

    try:
        update_config("provider", provider)
        console.print(f"[green]Successfully switched to provider:[/green] [bold]{provider}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def test(prompt: str = typer.Argument(None, help="Initial prompt to send")):
    """Run an interactive test session with your active AI provider."""
    from rich.prompt import Prompt

    from nopper import AI

    try:
        ai = AI()
    except Exception as e:
        console.print(f"[red]Error initializing AI:[/red] {e}")
        console.print("Hint: Check if your provider and API key are configured correctly.")
        raise typer.Exit(1)

    console.print(f"Connected to [bold green]{ai.provider_name}[/bold green] (model: {ai.config.model})")
    console.print("Type [bold yellow]'exit'[/bold yellow] or [bold yellow]'quit'[/bold yellow] to stop.")
    console.print("-" * 50)

    def run_prompt(p: str):
        console.print("[bold blue]Assistant:[/bold blue] ", end="")
        try:
            for chunk in ai.stream(p):

                console.print(chunk, end="", markup=False)
            console.print("\n")
        except Exception as e:
            console.print(f"\n[red]Error during generation:[/red] {e}\n")

    if prompt:
        console.print(f"[bold cyan]You:[/bold cyan] {prompt}")
        run_prompt(prompt)

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            if user_input.lower().strip() in ('exit', 'quit'):
                break
            if not user_input.strip():
                continue
            run_prompt(user_input)
        except (KeyboardInterrupt, EOFError):
            console.print()
            break



@app.command()
def benchmark(prompt: str = typer.Option("Write a short poem about a fast computer.", help="The prompt to run across providers.")):
    """Benchmark configured AI providers for speed and cost."""
    import asyncio

    from rich.table import Table

    from nopper.ai import AsyncAI
    from nopper.config import load_config
    
    config = load_config()
    available_providers = []
    
    for p in config.api_keys.keys():
        if config.api_keys[p]:
            available_providers.append(p)
            
    if "ollama" not in available_providers:
        available_providers.append("ollama")
        
    if not available_providers:
        console.print("[red]No providers configured. Please add an API key first.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[bold blue]Benchmarking {len(available_providers)} providers...[/bold blue] 🚀")
    
    async def run_benchmark():
        async def query_provider(p_name: str):
            try:
                ai = AsyncAI(provider=p_name, max_retries=0)
                
                response = await ai.chat(prompt, raw=True)
                return p_name, response, None
            except Exception as e:
                return p_name, None, str(e)
                
        tasks = [query_provider(p) for p in available_providers]
        results = await asyncio.gather(*tasks)
        
        table = Table(title="Benchmark Results")
        table.add_column("Provider", style="cyan", no_wrap=True)
        table.add_column("Model", style="magenta")
        table.add_column("Speed", style="green", justify="right")
        table.add_column("Cost", style="yellow", justify="right")
        
        
        success_results = []
        errors = []
        
        for p_name, response, error in results:
            if error:
                errors.append((p_name, error))
            else:
                success_results.append((p_name, response))
                
        success_results.sort(key=lambda x: x[1].latency)
        
        for p_name, response in success_results:
            cost_str = f"${response.cost:.4f}" if response.cost > 0 else "Free"
            table.add_row(
                p_name,
                response.model,
                f"{response.latency:.2f}s",
                cost_str
            )
            
        console.print(table)
        
        if errors:
            console.print("\n[bold red]Failures:[/bold red]")
            for p_name, error in errors:
                console.print(f"- [cyan]{p_name}[/cyan]: {error}")
                
    asyncio.run(run_benchmark())

@app.command()
def whoami():
    """Show the current active context."""
    from nopper import __version__
    from nopper.config import load_config
    
    config = load_config()
    provider = config.provider
    model = config.model
    api_key = config.api_keys.get(provider)
    
    if api_key:
        if len(api_key) > 8:
            key_status = f"{api_key[:4]}...{api_key[-4:]}"
        else:
            key_status = "***"
    elif provider == "ollama":
        key_status = "Not Required"
    else:
        key_status = "Not Set"
        
    console.print(f"[bold cyan]Provider:[/bold cyan] {provider}")
    console.print(f"[bold cyan]Model:[/bold cyan] {model}")
    console.print(f"[bold cyan]API Key Status:[/bold cyan] {key_status}")
    console.print("[bold cyan]Token Limit:[/bold cyan] Provider Dependent")
    console.print(f"[bold cyan]Version:[/bold cyan] {__version__}")

@app.command("export")
def export_config(output: str | None = typer.Option(None, "--output", "-o", help="File to export to")):
    """Export the current configuration as JSON."""
    from nopper.config import load_config
    config = load_config()
    json_data = config.model_dump_json(indent=2)
    
    if output:
        with open(output, "w") as f:
            f.write(json_data)
        console.print(f"[green]Configuration exported to[/green] [bold]{output}[/bold]")
    else:
        console.print(json_data)

@app.command("import")
def import_config(file: str = typer.Argument(..., help="JSON file to import configuration from")):
    """Import configuration from a JSON file."""
    import json
    import os

    from nopper.config import CONFIG_FILE, NopperSettings
    
    if not os.path.exists(file):
        console.print(f"[red]Error:[/red] File '{file}' not found.")
        raise typer.Exit(1)
        
    try:
        with open(file, "r") as f:
            data = json.load(f)
            
        new_config = NopperSettings(**data)
        
        with open(CONFIG_FILE, "w") as f:
            f.write(new_config.model_dump_json(indent=2))
            
        console.print(f"[green]Successfully imported configuration from[/green] [bold]{file}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to import configuration:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def dashboard():
    """Open the Nopper dashboard."""
    from rich.panel import Panel

    from nopper.config import load_config
    
    settings = load_config()
    
    dashboard_text = f"""
[bold cyan]Global Provider:[/bold cyan] {settings.provider}
[bold cyan]Global Model:[/bold cyan] {settings.model}

[bold green]Usage Tracking:[/bold green] {'Enabled' if settings.track_usage else 'Disabled'}
[bold green]Caching:[/bold green] {'Enabled' if getattr(settings, 'cache_enabled', False) else 'Disabled'}

[bold yellow]Configured Providers/Keys:[/bold yellow] {len([k for k, v in settings.api_keys.items() if v])}
[bold yellow]Custom Nodes/Profiles:[/bold yellow] {len(settings.nodes)}
[bold yellow]Aliases:[/bold yellow] {len(settings.aliases)}
[bold yellow]Templates:[/bold yellow] {len(getattr(settings, 'templates', dict()))}

[dim]Note: A full web dashboard is coming soon! For now, use this terminal summary.[/dim]
    """
    console.print(Panel(dashboard_text.strip(), title="Nopper Terminal Dashboard", expand=False))

@app.command()
def doctor():
    """Run diagnostic checks."""
    import urllib.request

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from nopper import __version__
    from nopper.ai import AI
    from nopper.config import load_config
    
    console.print("[bold blue]Nopper Doctor[/bold blue] 🩺")
    console.print("-" * 30)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        
        console.print(f"[green]✓[/green] Version: {__version__}")
        
        
        task = progress.add_task("Checking configuration...", total=None)
        try:
            config = load_config()
            provider = config.provider
            console.print("[green]✓[/green] Config valid")
        except Exception as e:
            console.print(f"[red]✗[/red] Config valid: {e}")
            raise typer.Exit(1)
            
        
        progress.update(task, description="Checking internet connection...")
        try:
            urllib.request.urlopen("https://1.1.1.1", timeout=3)
            console.print("[green]✓[/green] Internet reachable")
        except Exception:
            console.print("[red]✗[/red] Internet reachable: Could not reach 1.1.1.1")
            
        
        progress.update(task, description=f"Checking API key for {provider}...")
        api_key = config.api_keys.get(provider)
        if api_key or provider == "ollama":
            console.print(f"[green]✓[/green] API key configured for {provider}")
        else:
            console.print(f"[red]✗[/red] API key configured for {provider}: Not found in config")
            
        
        progress.update(task, description=f"Checking connection to {provider}...")
        try:
            ai = AI(provider=provider, max_retries=0)
            try:
                models = ai.models()
                if models:
                    console.print("[green]✓[/green] Provider reachable")
                    if config.model in models:
                        console.print(f"[green]✓[/green] Model '{config.model}' exists")
                    else:
                        console.print(f"[yellow]![/yellow] Model '{config.model}' exists: Provider did not list this model.")
                else:
                    response = ai.chat("Hi")
                    console.print("[green]✓[/green] Provider reachable (via chat)")
                    console.print(f"[green]✓[/green] Model '{config.model}' exists (via chat)")
            except NotImplementedError:
                response = ai.chat("Hi")
                console.print("[green]✓[/green] Provider reachable (via chat)")
                console.print(f"[green]✓[/green] Model '{config.model}' exists (via chat)")
        except Exception as e:
            console.print(f"[red]✗[/red] Provider reachable: {e}")
            console.print(f"[red]✗[/red] Model '{config.model}' exists: Could not verify")
            
    if getattr(config, 'nodes', None):
        console.print("\n[bold blue]Checking Remote Nodes[/bold blue]")
        import asyncio

        import httpx
        
        async def check_node(name, node):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    headers = {}
                    if node.api_key:
                        headers["Authorization"] = f"Bearer {node.api_key}"
                    response = await client.get(f"{node.base_url}/models", headers=headers)
                    if response.status_code == 200:
                        console.print(f"[green]✓[/green] Node '{name}': ONLINE ({response.elapsed.total_seconds():.2f}s)")
                    else:
                        console.print(f"[yellow]![/yellow] Node '{name}': HTTP {response.status_code}")
            except Exception:
                console.print(f"[red]✗[/red] Node '{name}': OFFLINE")

        async def run_node_checks():
            tasks = [check_node(name, node) for name, node in config.nodes.items()]
            await asyncio.gather(*tasks)
            
        asyncio.run(run_node_checks())
        
    console.print("-" * 30)
    console.print("Diagnostics complete.")



@app.command()
def providers():
    """List available providers."""
    available_providers = list_providers()
    console.print("[bold cyan]Available Providers:[/bold cyan]")
    for p in available_providers:
        console.print(f"- {p}")

@app.command()
def version():
    """Show the current Nopper version."""
    from nopper import __version__
    console.print(f"Nopper version: [bold cyan]{__version__}[/bold cyan]")

@app.command()
def update(key: str = typer.Argument(..., help="Config key to update (e.g., api_keys.openai)"), 
           value: str = typer.Argument(..., help="New value for the config key")):
    """Update a specific configuration value."""
    try:
        from nopper.config import update_config
        update_config(key, value)
        console.print(f"[green]Successfully updated[/green] [bold]{key}[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to update configuration:[/red] {e}")

@app.command()
def nodes():
    """List all stored nodes quickly without checking status."""
    from rich.table import Table

    from nopper.config import load_config
    
    config = load_config()
    if not config.nodes:
        console.print("[yellow]No custom nodes stored.[/yellow]")
        return
        
    table = Table(title="Stored Custom Nodes")
    table.add_column("Name", style="cyan")
    table.add_column("Base URL", style="blue")
    table.add_column("Model")
    
    for name, node in config.nodes.items():
        table.add_row(name, node.base_url or f"Standard ({node.type})", node.model or "Not Set")
        
    console.print(table)

@app.command("track_usage")
def track_usage(
    state: str = typer.Argument(..., help="on or off"),
    path: str = typer.Option(None, "-p", "--path", help="File path/name to save the usage history"),
    json_format: bool = typer.Option(False, "--json", help="Use JSON format instead of CSV")
):
    """Enable or disable global AI usage tracking."""
    state = state.lower()
    if state not in ["on", "off"]:
        console.print("[red]State must be 'on' or 'off'.[/red]")
        raise typer.Exit(1)
        
    update_config("track_usage", state == "on")
    
    if path:
        update_config("track_file", path)
        
    if json_format:
        update_config("track_format", "json")
    else:
        update_config("track_format", "csv")
        
    settings = load_config()
    console.print(f"[green]Usage tracking is now {'ON' if settings.track_usage else 'OFF'}.[/green]")
    console.print(f"File: {settings.track_file} ({settings.track_format.upper()})")

if __name__ == "__main__":
    app()

